import os
import re
import time
import sqlite3
import secrets
import hashlib
from pathlib import Path
from flask import (
    Flask, request, jsonify, render_template,
    send_file, abort
)
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STORAGE = BASE_DIR / "storage"
DB_PATH = BASE_DIR / "secureshare.db"

STORAGE.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", secrets.token_hex(32)
)

LINK_LIFETIME = 24 * 60 * 60  # 24 hours
ALLOWED_NAME = re.compile(r"^[\w.\- ()]+$")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                stored_name TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            )
        """)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/s/<token>")
def receive_page(token):
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        abort(404)

    return render_template("receive.html", token=token)


@app.route("/api/upload", methods=["POST"])
def upload():
    encrypted_file = request.files.get("file")
    original_name = request.form.get("filename", "file")

    if not encrypted_file:
        return jsonify({"error": "No file provided"}), 400

    original_name = secure_filename(original_name)

    if not original_name or not ALLOWED_NAME.match(original_name):
        original_name = "shared-file"

    # The uploaded file is already encrypted by the browser.
    data = encrypted_file.read()

    if not data:
        return jsonify({"error": "Empty upload"}), 400

    if len(data) > 100 * 1024 * 1024:
        return jsonify({"error": "File too large"}), 413

    token = secrets.token_hex(32)
    token_hash = hash_token(token)
    stored_name = secrets.token_hex(16) + ".enc"

    now = int(time.time())
    expires_at = now + LINK_LIFETIME

    path = STORAGE / stored_name
    path.write_bytes(data)

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO shares (
                    token_hash, stored_name, original_name,
                    file_size, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                token_hash,
                stored_name,
                original_name,
                len(data),
                now,
                expires_at
            ))
    except Exception:
        path.unlink(missing_ok=True)
        raise

    return jsonify({
        "link": request.host_url.rstrip("/") + "/s/" + token,
        "token": token,
        "expires_at": expires_at
    })

@app.route("/api/info/<token>")
def share_info(token):
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        abort(404)

    with get_db() as db:
        row = db.execute("""
            SELECT original_name, expires_at, consumed
            FROM shares
            WHERE token_hash = ?
        """, (hash_token(token),)).fetchone()

    if not row or row["expires_at"] <= int(time.time()) or row["consumed"]:
        return jsonify({"error": "Link expired or already used"}), 410

    return jsonify({
        "filename": row["original_name"],
        "expires_at": row["expires_at"]
    })
@app.route("/api/download/<token>", methods=["POST"])
def download(token):
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        abort(404)

    token_hash = hash_token(token)
    now = int(time.time())

    # Atomic claim: only one request can consume this link.
    with get_db() as db:
        db.execute("BEGIN IMMEDIATE")

        row = db.execute("""
            SELECT * FROM shares
            WHERE token_hash = ?
              AND expires_at > ?
              AND consumed = 0
        """, (token_hash, now)).fetchone()

        if not row:
            db.rollback()
            return jsonify({
                "error": "This link has expired or was already used."
            }), 410

        updated = db.execute("""
            UPDATE shares
            SET consumed = 1
            WHERE id = ? AND consumed = 0
        """, (row["id"],))

        if updated.rowcount != 1:
            db.rollback()
            return jsonify({"error": "Link already used"}), 410

        db.commit()

    file_path = STORAGE / row["stored_name"]

    if not file_path.exists():
        return jsonify({"error": "File unavailable"}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name="encrypted-file.enc",
        mimetype="application/octet-stream"
    )


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "Maximum upload size is 100 MB"}), 413


init_db()

if __name__ == "__main__":
    app.run(debug=True)