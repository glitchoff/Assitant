from fastapi import UploadFile, HTTPException
from agents.checkIntent import checkIntent
from utils.pdfutils import pdfParser
# from utils.textutils import txt_to_markdown
# from utils.csvutils import csv_to_markdown

async def orchestrator(file: UploadFile):
    #1. check file type and process it   
    result = await processfile(file)
    intent = await checkIntent(result)
    return intent 

async def getExt(file: UploadFile):
    ext = file.filename.upper().split(".")[-1]
    return ext

async def processfile(file: UploadFile):
    file_type = await getExt(file)

    if file_type == "PDF":  
        return await pdfParser(file)
    elif file_type == "TXT":
        raise HTTPException(status_code=400, detail="TXT file support is currently disabled")
    elif file_type == "CSV":
        raise HTTPException(status_code=400, detail="CSV file support is currently disabled")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}. Currently supported types: PDF")




