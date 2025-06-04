from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.orchestrator import orchestrator
from memory.database import DatabaseManager
import logging
from typing import List, Dict, Any
import json

app = FastAPI()

# Initialize database manager
print("Initializing database...")
db_manager = DatabaseManager()
print("Database initialized successfully")

templates = Jinja2Templates(directory="templates")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

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


@app.get("/test_db")
async def test_db():
    """Test database connection and logging"""
    try:
        test_data = {"test": "This is a test record"}
        record_id = db_manager.log_agent_data(
            agent_type="test",
            file_name="test.txt",
            intent="test",
            data=test_data,
            status="test"
        )
        return {"status": "success", "record_id": record_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/crm")
def crm_dashboard(request: Request):
    return templates.TemplateResponse("crm.html", {"request": request})

@app.get("/agent/data")
async def get_agent_data():
    """Get all agent data with optional filtering"""
    try:
        data = db_manager.get_agent_data()
        return data
    except Exception as e:
        logging.error(f"Error getting agent data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agent/data/{record_id}")
async def get_single_agent_record(record_id: int):
    """Get a single agent record by ID"""
    try:
        record = db_manager.get_agent_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except Exception as e:
        logging.error(f"Error getting agent record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/data/{record_id}/followup")
async def add_followup(record_id: int, notes: str = Form(...)):
    """Add follow-up notes to an agent record"""
    try:
        db_manager.add_followup_notes(record_id, notes)
        return {"status": "success", "message": "Follow-up notes added"}
    except Exception as e:
        logging.error(f"Error adding follow-up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crm")
async def crm_dashboard(request: Request):
    """CRM Dashboard with agent data"""
    try:
        print("Fetching agent data for CRM...")
        agent_data = db_manager.get_agent_data()
        print(f"Found {len(agent_data)} records")
        
        # Convert data to a format that can be JSON serialized
        serializable_data = []
        for record in agent_data:
            serializable_record = dict(record)
            # Convert data to string if it's a dictionary
            if 'data' in serializable_record:
                if isinstance(serializable_record['data'], str):
                    try:
                        # If it's a JSON string, parse it to dict
                        serializable_record['data'] = json.loads(serializable_record['data'])
                    except json.JSONDecodeError:
                        # If it's not JSON, keep it as is
                        pass
            serializable_data.append(serializable_record)
            
        print("Rendering template...")
        return templates.TemplateResponse("crm.html", {
            "request": request, 
            "agent_data": serializable_data,
            "json_module": json  # Make json module available in templates
        })
    except Exception as e:
        logging.error(f"Error loading CRM dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
