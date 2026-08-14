import bcrypt

def hash_password(password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()  # store as string so it's JSON-serializable

def verify_password(password, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()  # bcrypt.checkpw needs bytes
    return bcrypt.checkpw(password.encode(), hashed)