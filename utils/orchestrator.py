from fastapi import UploadFile, HTTPException
import logging
import os
from typing import Dict, Any, Optional
import mimetypes
from datetime import datetime

# Import agents
from agents.checkIntent import checkIntent
from utils.pdfutils import pdfParser
from agents.invoiceAgent import invoiceAgent
from agents.rfqAgent import rfqAgent
from agents.complaintAgent import complaintAgent
from agents.regulationAgent import regulationAgent
from agents.fraudRiskAgent import fraudRiskAgent

# Import database utilities
from .dbutils import (
    log_document, log_intent, log_agent_response, 
    update_document_status, set_document_metadata, get_document,
    get_agent_responses, add_follow_up
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def orchestrator(file: UploadFile) -> Dict[str, Any]:
    """
    Main orchestrator function to process uploaded files.
    Handles the entire pipeline from file upload to agent processing.
    """
    document_id = None
    intent_id = None
    
    try:
        # 1. Read file content once
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="The file appears to be empty")
            
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
        
        logger.info(f"Processing file: {file.filename} (Size: {len(file_content)} bytes, Type: {mime_type})")
        
        # Log the document in the database
        document_id = log_document(
            file_name=file.filename,
            file_size=len(file_content),
            mime_type=mime_type,
            original_content=file_content.decode('utf-8', errors='replace') if file_content else None
        )
        
        # 2. Process the file based on its type
        try:
            # Create a temporary file to store the content
            import tempfile
            import os
            
            # Create a temporary file with the same extension
            file_ext = os.path.splitext(file.filename or '')[-1] or '.bin'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Open the temporary file and create an UploadFile
                temp_file = open(temp_file_path, 'rb')
                file_copy = UploadFile(
                    filename=os.path.basename(file.filename or 'unnamed_file' + file_ext),
                    file=temp_file
                )
                
                # Process the file
                processed_content = await process_file(file_copy)
                
            finally:
                # Clean up the temporary file
                temp_file.close()
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {temp_file_path}: {str(e)}")
            
            # Update document with processed content
            set_document_metadata(document_id, "processed_content", processed_content)
            update_document_status(document_id, "processed")
            
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            update_document_status(document_id, "error", error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 3. Check intent
        try:
            logger.info("Determining document intent...")
            intent_result = await check_intent(processed_content)
            intent = intent_result.get("intent", "unknown")
            confidence = float(intent_result.get("confidence", 0))
            
            # Log the detected intent
            intent_id = log_intent(
                document_id=document_id,
                intent_type=intent,
                confidence=confidence
            )
            
            # Store intent metadata
            set_document_metadata(document_id, "intent", intent)
            set_document_metadata(document_id, "intent_confidence", confidence)
            
            logger.info(f"Detected intent: {intent} (Confidence: {confidence:.2f})")
            
        except Exception as e:
            error_msg = f"Error determining intent: {str(e)}"
            logger.error(error_msg, exc_info=True)
            update_document_status(document_id, "intent_error", error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 4. Route to appropriate agent based on intent
        try:
            logger.info(f"Routing to {intent} agent...")
            agent_response = await route_to_agent(intent, processed_content)
            
            # Log the agent response
            response_id = log_agent_response(
                document_id=document_id,
                intent_id=intent_id,
                agent_type=intent.lower(),
                response_data=agent_response,
                metadata={
                    "processing_time_ms": 0,  # TODO: Add actual timing
                    "agent_version": "1.0"
                }
            )
            
            # Update document status
            update_document_status(document_id, "processed")
            
            # Add any necessary follow-ups
            if intent == "Complaint":
                add_follow_up(
                    document_id=document_id,
                    action_type="review_complaint",
                    action_details={
                        "priority": "high" if agent_response.get("severity") == "high" else "normal",
                        "assigned_to": "support_team"
                    }
                )
            
            logger.info(f"Successfully processed {intent} document")
            
            # Return the complete response
            return {
                "status": "success",
                "document_id": document_id,
                "intent": intent,
                "confidence": confidence,
                "data": agent_response,
                "metadata": {
                    "filename": file.filename,
                    "processed_at": datetime.utcnow().isoformat(),
                    "document_url": f"/documents/{document_id}"
                }
            }
            
        except Exception as e:
            error_msg = f"Error in agent processing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            update_document_status(document_id, "agent_error", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle any other exceptions
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        if document_id:
            update_document_status(document_id, "error", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

async def check_intent(content: str) -> Dict[str, Any]:
    """
    Wrapper around the checkIntent agent to standardize the response format.
    """
    try:
        result = await checkIntent(content)
        # Ensure the result has the expected format
        if isinstance(result, str):
            # Try to parse as JSON if it's a string
            import json
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                # If it's not JSON, assume it's just the intent type
                result = {"intent": result, "confidence": 1.0}
        
        # Ensure required fields exist
        if not isinstance(result, dict):
            result = {"intent": str(result), "confidence": 1.0}
        
        if "intent" not in result:
            result["intent"] = "unknown"
        if "confidence" not in result:
            result["confidence"] = 1.0
            
        return result
    except Exception as e:
        logger.error(f"Error in check_intent: {str(e)}", exc_info=True)
        return {"intent": "unknown", "confidence": 0.0, "error": str(e)}

async def process_file(file: UploadFile) -> str:
    """
    Process the uploaded file based on its type.
    Returns the processed content as a string.
    """
    try:
        # Read the file content once
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The file is empty")
            
        # Get file extension (without dot)
        file_type = os.path.splitext(file.filename or '')[-1].upper().lstrip('.') if file.filename else ""
        
        if file_type == "PDF":
            try:
                # Process PDF file using the content directly
                from io import BytesIO
                file_obj = BytesIO(content)
                # Create a new UploadFile for the PDF parser
                pdf_file = UploadFile(
                    filename=file.filename or 'document.pdf',
                    file=file_obj
                )
                result = await pdfParser(pdf_file)
                return result.get("content", "")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
                
        elif file_type in ["TXT", "TEXT"]:
            try:
                return content.decode('utf-8', errors='replace')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading text file: {str(e)}")
                
        elif file_type == "CSV":
            raise HTTPException(status_code=400, detail="CSV file support is currently disabled")
            
        else:
            # For unsupported types, try to read as text
            try:
                return content.decode('utf-8', errors='replace')
            except Exception:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_type}. Currently supported types: PDF, TXT"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

async def route_to_agent(intent: str, content: str) -> Dict[str, Any]:
    """
    Route the content to the appropriate agent based on the detected intent.
    """
    agent_mapping = {
        "Invoice": invoiceAgent,
        "RFQ": rfqAgent,
        "Complaint": complaintAgent,
        "Regulation": regulationAgent,
        "Fraud_Risk": fraudRiskAgent,
    }
    
    agent_func = agent_mapping.get(intent)
    if not agent_func:
        raise HTTPException(status_code=400, detail=f"No agent available for intent: {intent}")
    
    try:
        # Call the appropriate agent
        result = await agent_func(content)
        
        # Ensure the result is a dictionary
        if not isinstance(result, dict):
            try:
                # Try to parse as JSON if it's a string
                import json
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, wrap it in a result field
                result = {"result": str(result)}
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in {intent} agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing with {intent} agent: {str(e)}"
        )

def get_document_status(document_id: int) -> Dict[str, Any]:
    """
    Get the status and results of a processed document.
    """
    try:
        document = get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        intents = get_document_intents(document_id)
        responses = get_agent_responses(document_id)
        
        return {
            "document": dict(document),
            "intents": intents,
            "responses": responses
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))