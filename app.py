from flask import Flask, request, render_template, send_file
import os
import json
import time
import requests
import vercel_blob

from utils.crypto import encrypt_file, decrypt_file
from utils.auth import hash_password, verify_password
from utils.token import generate_token, get_expiry, is_expired
from utils.logger import log_access

app = Flask(__name__)

TMP_DIR = "/tmp"
METADATA_PATH = "metadata.json"


def load_metadata():
    """Fetch metadata.json from Blob storage, or return empty dict if it doesn't exist yet."""
    try:
        blobs = vercel_blob.list().get("blobs", [])
        meta_blob = next((b for b in blobs if b["pathname"] == METADATA_PATH), None)
        if not meta_blob:
            return {}
        resp = requests.get(meta_blob["url"])
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def save_metadata(data):
    vercel_blob.put(
        METADATA_PATH,
        json.dumps(data).encode(),
        {"contentType": "application/json"}
    )


@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        password = request.form["password"]
        filename = file.filename

        local_path = os.path.join(TMP_DIR, filename)
        file.save(local_path)

        # Encrypt locally in /tmp
        encrypted_local_path = encrypt_file(local_path, password)

        # Upload encrypted file to Blob storage
        with open(encrypted_local_path, "rb") as f:
            blob_result = vercel_blob.put(f"encrypted/{filename}", f.read())

        hashed_pw = hash_password(password)
        token = generate_token()
        expiry = get_expiry(10)

        metadata = load_metadata()
        metadata[filename] = {
            "blob_url": blob_result["url"],
            "blob_pathname": blob_result["pathname"],
            "password": hashed_pw,
            "attempts": 0,
            "token": token,
            "expiry": expiry
        }
        save_metadata(metadata)

        # Clean up local tmp files
        for p in (local_path, encrypted_local_path):
            try:
                os.remove(p)
            except Exception:
                pass

        link = f"{request.host_url}download/{token}"
        return render_template("success.html", link=link)

    return render_template("upload.html")


@app.route("/download/<token>", methods=["GET", "POST"])
def download(token):
    metadata = load_metadata()
    filename = None
    file_data = None

    for fname, data in metadata.items():
        if data["token"] == token:
            file_data = data
            filename = fname
            break

    if not file_data:
        return "Invalid or broken link"

    if is_expired(file_data["expiry"]):
        return "Link expired"

    if request.method == "POST":
        password = request.form["password"]

        if file_data["attempts"] > 5:
            return "Too many attempts!"

        if verify_password(password, file_data["password"]):
            # Download encrypted blob into /tmp
            encrypted_local_path = os.path.join(TMP_DIR, f"enc_{filename}")
            resp = requests.get(file_data["blob_url"])
            with open(encrypted_local_path, "wb") as f:
                f.write(resp.content)

            decrypted_path = decrypt_file(encrypted_local_path, password)

            log_access(filename, "SUCCESS")

            # One-time download: delete blob + metadata entry
            try:
                vercel_blob.delete(file_data["blob_url"])
            except Exception:
                pass

            del metadata[filename]
            save_metadata(metadata)

            return send_file(decrypted_path, as_attachment=True)
        else:
            file_data["attempts"] += 1
            metadata[filename] = file_data
            save_metadata(metadata)
            log_access(filename, "FAILED")
            return "Wrong password"

    return render_template("download.html", filename=filename)


if __name__ == "__main__":
    app.run(debug=True)