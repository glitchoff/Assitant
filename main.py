from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.orchestrator import orchestrator
from memory.database import DatabaseManager
import logging
from typing import List, Dict, Any
import json
from api.memoryRoute import api_router
import uvicorn

app = FastAPI()

# Initialize database manager
print("Initializing database...")
db_manager = DatabaseManager()
print("Database initialized successfully")

templates = Jinja2Templates(directory="templates")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/classify")
async def classify_file(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        # Validate file size
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        #this is the real orchestrator function
        result = await orchestrator(file)
        logger.info(f"Successfully processed file: {file.filename}")
        return result
    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@app.get("/")
def read_root():
    return FileResponse("static/index.html")

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
