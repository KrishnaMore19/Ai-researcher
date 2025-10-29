import os
import shutil
from fastapi import UploadFile
from typing import Optional

# Define storage paths
UPLOAD_DIR = "storage/uploads"
PROCESSED_DIR = "storage/processed"
TEMP_DIR = "storage/temp"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def save_upload_file(uploaded_file: UploadFile, destination_dir: str = UPLOAD_DIR) -> str:
    """
    Save an uploaded file to a destination directory.
    Returns the file path.
    """
    file_path = os.path.join(destination_dir, uploaded_file.filename)

    # Handle duplicate file names
    base, ext = os.path.splitext(file_path)
    counter = 1
    while os.path.exists(file_path):
        file_path = f"{base}_{counter}{ext}"
        counter += 1

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    return file_path


def delete_file(file_path: str) -> bool:
    """
    Delete a file from storage safely.
    Returns True if deleted, False if not found.
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"❌ Error deleting file: {e}")
        return False


def move_file(src_path: str, dest_dir: str = PROCESSED_DIR) -> Optional[str]:
    """
    Move file from source to destination directory.
    Returns new file path.
    """
    try:
        if not os.path.exists(src_path):
            return None
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.move(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"❌ Error moving file: {e}")
        return None


def read_file_content(file_path: str) -> Optional[str]:
    """
    Read and return text content from a file (for .txt, .md, etc.)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
