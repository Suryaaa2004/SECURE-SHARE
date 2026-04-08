from flask import Flask, request, render_template, send_file
import os
import threading
import time

from utils.crypto import encrypt_file, decrypt_file
from utils.auth import hash_password, verify_password
from utils.token import generate_token, get_expiry, is_expired
from utils.logger import log_access

app = Flask(__name__)

UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage
file_store = {}


# 🔐 Upload Route
@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        password = request.form["password"]

        filename = file.filename
        path = os.path.join(UPLOAD_FOLDER, filename)

        # Save original file
        file.save(path)

        # Encrypt file
        encrypted_path = encrypt_file(path, password)

        # Hash password
        hashed_pw = hash_password(password)

        # Generate secure token + expiry
        token = generate_token()
        expiry = get_expiry(10)  # 10 minutes

        # Store metadata
        file_store[filename] = {
            "path": encrypted_path,
            "password": hashed_pw,
            "attempts": 0,
            "token": token,
            "expiry": expiry
        }

        # Return success UI
        link = f"http://127.0.0.1:5000/download/{token}"
        return render_template("success.html", link=link)

    return render_template("upload.html")


# 🔓 Download Route (ONE-TIME DOWNLOAD ENABLED)
@app.route("/download/<token>", methods=["GET", "POST"])
def download(token):
    file_data = None
    filename = None

    # Find file by token
    for fname, data in file_store.items():
        if data["token"] == token:
            file_data = data
            filename = fname
            break

    # Invalid token
    if not file_data:
        return "Invalid or broken link"

    # Expiry check
    if is_expired(file_data["expiry"]):
        return "Link expired"

    if request.method == "POST":
        password = request.form["password"]

        # Brute-force protection
        if file_data["attempts"] > 5:
            return "Too many attempts!"

        # Password verification
        if verify_password(password, file_data["password"]):
            decrypted_path = decrypt_file(file_data["path"], password)

            log_access(filename, "SUCCESS")

            # 🔥 ONE-TIME DOWNLOAD LOGIC

            # Delete encrypted file
            try:
                os.remove(file_data["path"])
            except:
                pass

            # Remove entry from memory
            del file_store[filename]

            # Optional: delete decrypted file after sending
            def delete_file_later(path):
                time.sleep(5)
                try:
                    os.remove(path)
                except:
                    pass

            threading.Thread(target=delete_file_later, args=(decrypted_path,)).start()

            return send_file(decrypted_path, as_attachment=True)

        else:
            file_data["attempts"] += 1
            log_access(filename, "FAILED")
            return "Wrong password"

    return render_template("download.html", filename=filename)


# 🚀 Run App
if __name__ == "__main__":
    app.run(debug=True)