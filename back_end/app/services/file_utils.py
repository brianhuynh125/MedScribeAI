# services/file_utils.py
import tempfile
import os

def save_upload_tmp(file_bytes: bytes, suffix=".wav") -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(file_bytes)
    tmp.flush()
    tmp.close()
    return tmp.name

def cleanup_file(file_path: str):
    if os.path.exists(file_path):
        os.unlink(file_path)
