from fastapi import UploadFile, HTTPException
from agents.checkIntent import checkIntent
from utils.pdfutils import pdfParser
from agents.invoiceAgent import invoiceAgent
from agents.rfqAgent import rfqAgent
from agents.complaintAgent import complaintAgent
from agents.regulationAgent import regulationAgent
from agents.fraudRiskAgent import fraudRiskAgent
from memory.database import DatabaseManager

db_manager = DatabaseManager()

async def orchestrator(file: UploadFile):
    #1. check file type and process file   
    try:
        print(f"Processing file: {file.filename}")
        result = await processfile(file)
        print(f"File processed, checking intent...")
        intent = await checkIntent(result)
        print(f"Intent: {intent}, running IntentManager...")
        data = await IntentManager(intent, result)
        print(f"Got data from IntentManager")
        
        # Prepare data for logging
        log_data = {
            "intent": intent,
            "filename": file.filename,
            "result": data,
            "status": "processed"
        }
        
        # Log agent data to database
        print("Logging to database...")
        db_manager.log_agent_data(
            agent_type=intent,
            file_name=file.filename,
            intent=intent,
            data=data,
            status="processed"
        )
        print("Successfully logged to database")
        
        return data
    except Exception as e:
        # Log error to database
        db_manager.log_agent_data(
            agent_type="Unknown",
            file_name=file.filename,
            intent="Unknown",
            data={"error": str(e)},
            status="error"
        )
        raise

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

def IntentManager(intent, result):
    if intent == "Invoice":
        return invoiceAgent(result)
    elif intent == "RFQ":
        return rfqAgent(result)
    elif intent == "Complaint":
        return complaintAgent(result)
    elif intent == "Regulation":
        return regulationAgent(result)
    elif intent == "Fraud_Risk":
        return fraudRiskAgent(result)
    else:
        raise HTTPException(status_code=400, detail="Unknown intent")