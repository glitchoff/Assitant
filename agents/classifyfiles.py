# Inside classifyfiles.py
async def handle_file(file: UploadFile):
    if file.filename.upper().endswith(".PDF"):
        return {"file_name": file.filename}
    if file.filename.upper().endswith(".TXT"):
        return {"file_name": file.filename}
    if file.filename.upper().endswith(".CSV"):
        return {"file_name": file.filename}
    else:
        return {"file_name": "Invalid file type"}