from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib

def derive_key(password):
    return hashlib.sha256(password.encode()).digest()

def encrypt_file(filepath, password):
    key = derive_key(password)
    cipher = AES.new(key, AES.MODE_CBC)

    with open(filepath, "rb") as f:
        data = f.read()

    pad_len = 16 - len(data) % 16
    data += bytes([pad_len]) * pad_len

    ciphertext = cipher.encrypt(data)

    new_path = filepath + ".enc"

    with open(new_path, "wb") as f:
        f.write(cipher.iv + ciphertext)

    return new_path

def decrypt_file(filepath, password):
    key = derive_key(password)

    with open(filepath, "rb") as f:
        iv = f.read(16)
        ciphertext = f.read()

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    data = cipher.decrypt(ciphertext)

    pad_len = data[-1]
    data = data[:-pad_len]

    new_path = filepath.replace(".enc", "_dec")

    with open(new_path, "wb") as f:
        f.write(data)

    return new_path