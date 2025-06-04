from fastapi import UploadFile, HTTPException
from utils.pdfutils import pdf_to_markdown_advanced
# from utils.textutils import txt_to_markdown
# from utils.csvutils import csv_to_markdown

async def handle_file(file: UploadFile):
    ext = file.filename.upper().split(".")[-1]
    return ext

async def processfile(file: UploadFile):
    file_type = await handle_file(file)

    if file_type == "PDF":
        return await processpdf(file)
    elif file_type == "TXT":
        raise HTTPException(status_code=400, detail="TXT file support is currently disabled")
    elif file_type == "CSV":
        raise HTTPException(status_code=400, detail="CSV file support is currently disabled")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}. Currently supported types: PDF")


def processpdf(file: UploadFile):
    pdfData = pdfParser(file)
    return pdfData
