from datetime import datetime
import os

os.makedirs("logs", exist_ok=True)

def log_access(filename, status):
    with open("logs/access.log", "a") as f:
        f.write(f"{datetime.now()} - {filename} - {status}\n")