# Inside classifyfiles.py
from fastapi import UploadFile

async def handle_file(file: UploadFile):
    if file.filename.upper().endswith(".PDF"):
        return "pdf"
    if file.filename.upper().endswith(".TXT"):
        return "txt"
    if file.filename.upper().endswith(".CSV"):
        return "csv"
    else:
        return "Invalid file type"

