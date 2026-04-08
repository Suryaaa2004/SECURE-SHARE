import secrets
import time

def generate_token():
    return secrets.token_urlsafe(16)

def get_expiry(minutes=10):
    return time.time() + minutes * 60

def is_expired(expiry):
    return time.time() > expiry