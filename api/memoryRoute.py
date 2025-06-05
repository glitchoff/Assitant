
from fastapi import APIRouter, HTTPException, Form
from memory.database import DatabaseManager
import logging

# Create a router
router = APIRouter()
# Initialize database manager
db_manager = DatabaseManager()

@router.get("/agent/data")
async def get_agent_data():
    """Get all agent data with optional filtering"""
    try:
        data = db_manager.get_agent_data()
        return data
    except Exception as e:
        logging.error(f"Error getting agent data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent/data/{record_id}")
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

@router.post("/agent/data/{record_id}/followup")
async def add_followup(record_id: int, notes: str = Form(...)):
    """Add follow-up notes to an agent record"""
    try:
        db_manager.add_followup_notes(record_id, notes)
        return {"message": "Notes added successfully"}
    except Exception as e:
        logging.error(f"Error adding follow-up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# This will be imported in main.py
api_router = router
