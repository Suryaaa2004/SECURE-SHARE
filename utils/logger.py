from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

def log_access(filename, status):
    logging.info(f"{datetime.now()} - {filename} - {status}")