# 🔐 SecureShare — Encrypted File Sharing

A simple and secure file-sharing web application that encrypts files in the browser and generates one-time download links that expire after use.

SecureShare is designed to make sharing files easy while protecting their contents through client-side encryption.

## ✨ Features

- **Client-side encryption:** Files are encrypted in the browser using AES-256-GCM before upload.
- **Secure sharing links:** Generates cryptographically random tokens for file access.
- **One-time downloads:** Links become unusable after the download request is consumed.
- **Encryption key privacy:** The decryption key is included in the URL fragment and is not sent to the server in HTTP requests.
- **Automatic link expiration:** Links expire after the configured lifetime.
- **Drag-and-drop uploads:** Simple interface for selecting and uploading files.
- **Encrypted storage:** The server stores encrypted file contents rather than plaintext.
- **Browser-side decryption:** Recipients decrypt files locally after downloading.
- **Simple interface:** Upload, encrypt, share, and download without creating an account.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend language |
| Flask | Web framework |
| HTML, CSS, JavaScript | Frontend |
| Web Crypto API | Browser-side AES-GCM encryption |
| SQLite | Share-link metadata |
| Python `secrets` | Secure token generation |
| Docker | Planned containerization |

## 🔄 How It Works

1. The sender selects or drops a file into SecureShare.
2. The browser generates a random AES-256 key and encrypts the file using AES-GCM.
3. Only the encrypted file is uploaded to the server.
4. SecureShare generates a unique sharing token and link.
5. The sender shares the complete link with the intended recipient.
6. The recipient downloads the encrypted file.
7. The recipient's browser decrypts the file using the key from the URL fragment.
8. The link is marked as consumed and cannot be reused.

The database and encrypted file storage are generated locally when the application runs.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- A modern browser supporting the Web Crypto API

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SecureShare.git
cd SecureShare
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open the application:

```text
http://127.0.0.1:5000
```

## 🔒 Security Design

- Files are encrypted client-side using AES-256-GCM.
- A fresh random encryption key and initialization vector are generated for each file.
- Decryption keys are stored in the URL fragment, which is not transmitted in HTTP requests.
- Sharing tokens are generated using cryptographically secure randomness.
- Download links are consumed atomically to prevent concurrent reuse.
- File contents are stored encrypted on the server.

## ⚠️ Limitations

This project is currently a development prototype.

- HTTPS is required for secure public deployment.
- Rate limiting and upload abuse protections need to be configured.
- Expired-file cleanup is planned.
- A failed download after link consumption may require the sender to upload the file again.
- Anyone possessing the complete share link can access the file until it expires or is consumed.
- The application has not yet undergone an independent security audit.

## 🛣️ Roadmap

- [ ] Improve upload and download progress indicators
- [ ] Add automatic cleanup of expired files
- [ ] Add configurable link expiration
- [ ] Add rate limiting and security headers
- [ ] Add Docker support
- [ ] Deploy with HTTPS
- [ ] Add automated security and functional tests

## 🎯 Purpose

SecureShare was developed as a cybersecurity portfolio project to demonstrate practical implementation of:

- Cryptographic file protection
- Secure file-sharing workflows
- Client-side encryption
- Secure token generation
- Web application security principles
- Python and Flask development

## 👨‍💻 Author

**Surya Abhiram**

Cybersecurity Analyst | SOC | Application Security

- Portfolio: https://portfolio-inky-nine-53.vercel.app/
