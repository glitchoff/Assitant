
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging
import os

# Import database utilities
from utils.dbutils import (
    get_document, get_document_intents, get_agent_responses,
    get_document_metadata, get_all_document_metadata, update_document_status
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a router
router = APIRouter()

# API Endpoints
@router.get("/api/documents", response_model=List[Dict[str, Any]])
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = None,
    intent: Optional[str] = None
):
    """
    List all documents with pagination and filtering
    """
    logger.info(f"Fetching documents - page: {page}, page_size: {page_size}, status: {status}, intent: {intent}")
    
    try:
        # Check if database file exists
        db_path = os.path.join(os.getcwd(), 'crm.db')
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            raise HTTPException(
                status_code=500,
                detail="Database not initialized. Please check if the database file exists."
            )
        
        # Initialize database connection if not already done
        if not hasattr(router, 'db_conn') or not router.db_conn:
            logger.info("Initializing database connection...")
            try:
                router.db_conn = sqlite3.connect(db_path, check_same_thread=False)
                router.db_conn.row_factory = sqlite3.Row
                logger.info("Database connection established successfully")
            except sqlite3.Error as e:
                logger.error(f"Failed to connect to database: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to connect to database: {str(e)}"
                )
        
        offset = (page - 1) * page_size
        query = """
            SELECT d.*, i.intent_type, i.confidence 
            FROM documents d
            LEFT JOIN (
                SELECT document_id, intent_type, confidence
                FROM intents
                WHERE id IN (
                    SELECT MAX(id) FROM intents GROUP BY document_id
                )
            ) i ON d.id = i.document_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND d.status = ?"
            params.append(status)
            
        if intent:
            query += " AND i.intent_type = ?"
            params.append(intent)
            
        query += " ORDER BY d.upload_time DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Query params: {params}")
        
        try:
            cursor = router.db_conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")  # Ensure foreign key support
            cursor.execute(query, params)
            
            # Get column names
            columns = [column[0] for column in cursor.description] if cursor.description else []
            logger.debug(f"Query columns: {columns}")
            
            # Convert query results to list of dictionaries
            documents = []
            rows = cursor.fetchall()
            logger.info(f"Found {len(rows)} documents")
            
            for row in rows:
                try:
                    doc = dict(zip(columns, row))
                    # Get all metadata for this document
                    doc['metadata'] = get_all_document_metadata(doc['id'])
                    documents.append(doc)
                except Exception as doc_error:
                    logger.error(f"Error processing document row: {str(doc_error)}", exc_info=True)
                    continue
            
            # Get total count for pagination
            count_query = "SELECT COUNT(*) as total FROM documents d"
            count_params = []
            
            if status or intent:
                where_clauses = []
                if status:
                    where_clauses.append("d.status = ?")
                    count_params.append(status)
                if intent:
                    where_clauses.append("i.intent_type = ?")
                    count_params.append(intent)
                
                if where_clauses:
                    count_query += " WHERE " + " AND ".join(where_clauses)
            
            if intent:  # Need to join with intents table if filtering by intent
                count_query = """
                    SELECT COUNT(DISTINCT d.id) as total 
                    FROM documents d
                    LEFT JOIN intents i ON d.id = i.document_id
                """
                
                if status or intent:
                    where_clauses = []
                    if status:
                        where_clauses.append("d.status = ?")
                    if intent:
                        where_clauses.append("i.intent_type = ?")
                    
                    count_query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]
            
            logger.info(f"Returning {len(documents)} of {total_count} documents")
            
            # Add pagination headers
            response_headers = {
                "X-Total-Count": str(total_count),
                "X-Page": str(page),
                "X-Page-Size": str(page_size),
                "X-Total-Pages": str((total_count + page_size - 1) // page_size)
            }
            
            return JSONResponse(
                content=documents,
                headers=response_headers
            )
            
        except sqlite3.Error as db_error:
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(db_error)}"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"Error listing documents: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/api/documents/{document_id}", response_model=Dict[str, Any])
async def get_document_details(document_id: int):
    """
    Get detailed information about a specific document
    """
    try:
        document = get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Get all intents for this document
        intents = get_document_intents(document_id)
        
        # Get all agent responses
        responses = get_agent_responses(document_id)
        
        # Get all metadata
        metadata = get_document_metadata(document_id)
        
        return {
            "document": document,
            "intents": intents,
            "responses": responses,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/documents/{document_id}/responses")
async def get_document_responses(document_id: int):
    """
    Get all agent responses for a specific document
    """
    try:
        responses = get_agent_responses(document_id)
        return {"responses": responses}
    except Exception as e:
        logger.error(f"Error getting responses for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/stats")
async def get_system_stats():
    """
    Get system statistics with caching and better error handling
    """
    try:
        cursor = get_db_cursor()
        
        stats = {}
        
        try:
            # Total documents
            cursor.execute("SELECT COUNT(*) as total FROM documents")
            stats["total_documents"] = cursor.fetchone()['total']
            
            # Documents by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM documents 
                GROUP BY status
            """)
            stats["by_status"] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Documents by intent
            cursor.execute("""
                SELECT i.intent_type, COUNT(*) as count
                FROM documents d
                JOIN intents i ON d.id = i.document_id
                WHERE i.id IN (
                    SELECT MAX(id) FROM intents GROUP BY document_id
                )
                GROUP BY i.intent_type
            """)
            stats["by_intent"] = {row['intent_type']: row['count'] for row in cursor.fetchall()}
            
            # Add timestamp
            stats["last_updated"] = datetime.utcnow().isoformat()
            
            # Add database info
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            if db_info and len(db_info) > 0:
                stats["database"] = {
                    "path": db_info[0]['file'],
                    "size": os.path.getsize(db_info[0]['file']) if db_info[0]['file'] else 0
                }
            
            return stats
            
        except sqlite3.Error as db_error:
            error_msg = f"Database error: {str(db_error)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error getting system stats: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# Serve the CRM HTML page with cache control
@router.get("/crm", response_class=HTMLResponse)
async def get_crm_page():
    """
    Serve the CRM interface with proper caching headers
    """
    try:
        file_path = os.path.join("static", "crm.html")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"CRM HTML file not found at {os.path.abspath(file_path)}")
            raise HTTPException(
                status_code=404,
                detail="CRM interface not found. Please ensure the static files are properly deployed."
            )
        
        # Read file with error handling
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Add version info to the response headers
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY"
                }
                
                return HTMLResponse(
                    content=content,
                    status_code=200,
                    headers=headers
                )
                
        except UnicodeDecodeError:
            logger.error(f"Failed to decode CRM HTML file with UTF-8 encoding")
            raise HTTPException(
                status_code=500,
                detail="Failed to decode CRM interface file"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        error_msg = f"Error serving CRM page: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

# This will be imported in main.py
api_router = router

def init_db_connection(db_path: str):
    """
    Initialize database connection for the router
    """
    try:
        import sqlite3
        import os
        
        logger.info(f"Initializing database connection to: {os.path.abspath(db_path)}")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            logger.warning(f"Database file not found at {db_path}, will be created")
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or '.', exist_ok=True)
        
        # Connect to the database
        router.db_conn = sqlite3.connect(db_path)
        router.db_conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Test the connection
        cursor = router.db_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Successfully connected to database. Found {len(tables)} tables.")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}", exc_info=True)
        raise
