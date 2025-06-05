import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Initialize database connection
crmdb = sqlite3.connect('crm.db', check_same_thread=False)
crmdb.row_factory = sqlite3.Row  # Enable column access by name
cursor_crm = crmdb.cursor()

# Enable foreign key support
cursor_crm.execute("PRAGMA foreign_keys = ON")

# Create tables
TABLES = {
    'documents': """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type TEXT,
        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        original_content TEXT,
        processed_content TEXT,
        status TEXT DEFAULT 'pending',
        error_message TEXT
    )
    """,
    
    'intents': """
    CREATE TABLE IF NOT EXISTS intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        intent_type TEXT NOT NULL,
        confidence FLOAT,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,
    
    'agent_responses': """
    CREATE TABLE IF NOT EXISTS agent_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        intent_id INTEGER NOT NULL,
        agent_type TEXT NOT NULL,
        response_data TEXT NOT NULL,  -- JSON string
        processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT,  -- Additional metadata as JSON
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
    )
    """,
    
    'follow_ups': """
    CREATE TABLE IF NOT EXISTS follow_ups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        action_details TEXT,  -- JSON string
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,
    
    'document_metadata': """
    CREATE TABLE IF NOT EXISTS document_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT,
        data_type TEXT,  -- 'str', 'int', 'float', 'bool', 'json', 'datetime'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        UNIQUE(document_id, key)
    )
    """
}

# Create all tables
for table_name, create_query in TABLES.items():
    cursor_crm.execute(create_query)

# Create indexes for better query performance
cursor_crm.execute("""
    CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
""")

cursor_crm.execute("""
    CREATE INDEX IF NOT EXISTS idx_intents_document_id ON intents(document_id);
""")

cursor_crm.execute("""
    CREATE INDEX IF NOT EXISTS idx_agent_responses_document_id ON agent_responses(document_id);
""")

crmdb.commit()

# Database utility functions
def log_document(file_name: str, file_size: int, mime_type: str, 
                original_content: str = None, processed_content: str = None) -> int:
    """
    Log a new document in the database.
    Returns the document ID.
    """
    cursor_crm.execute(
        """
        INSERT INTO documents 
        (filename, file_size, mime_type, original_content, processed_content, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (file_name, file_size, mime_type, original_content, processed_content, 'uploaded')
    )
    crmdb.commit()
    return cursor_crm.lastrowid

def log_intent(document_id: int, intent_type: str, confidence: float = None) -> int:
    """
    Log a detected intent for a document.
    Returns the intent ID.
    """
    cursor_crm.execute(
        """
        INSERT INTO intents (document_id, intent_type, confidence)
        VALUES (?, ?, ?)
        """,
        (document_id, intent_type, confidence)
    )
    crmdb.commit()
    return cursor_crm.lastrowid

def log_agent_response(document_id: int, intent_id: int, agent_type: str, 
                      response_data: Union[Dict, str], metadata: Dict = None) -> int:
    """
    Log an agent's response for a document and intent.
    Returns the response ID.
    """
    if isinstance(response_data, dict):
        response_data = json.dumps(response_data)
    
    metadata_str = json.dumps(metadata) if metadata else None
    
    cursor_crm.execute(
        """
        INSERT INTO agent_responses 
        (document_id, intent_id, agent_type, response_data, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (document_id, intent_id, agent_type, response_data, metadata_str)
    )
    crmdb.commit()
    return cursor_crm.lastrowid

def add_follow_up(document_id: int, action_type: str, action_details: Dict = None) -> int:
    """
    Add a follow-up action for a document.
    Returns the follow-up ID.
    """
    details_str = json.dumps(action_details) if action_details else None
    
    cursor_crm.execute(
        """
        INSERT INTO follow_ups (document_id, action_type, action_details)
        VALUES (?, ?, ?)
        """,
        (document_id, action_type, details_str)
    )
    crmdb.commit()
    return cursor_crm.lastrowid

def set_document_metadata(document_id: int, key: str, value: Any, data_type: str = None) -> None:
    """
    Set metadata for a document.
    Automatically determines data type if not specified.
    """
    if data_type is None:
        if isinstance(value, bool):
            data_type = 'bool'
            value = str(value).lower()
        elif isinstance(value, int):
            data_type = 'int'
            value = str(value)
        elif isinstance(value, float):
            data_type = 'float'
            value = str(value)
        elif isinstance(value, dict) or isinstance(value, list):
            data_type = 'json'
            value = json.dumps(value)
        elif isinstance(value, datetime):
            data_type = 'datetime'
            value = value.isoformat()
        else:
            data_type = 'str'
            value = str(value)
    
    # Try to update existing metadata, or insert if not exists
    cursor_crm.execute(
        """
        INSERT INTO document_metadata (document_id, key, value, data_type, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(document_id, key) DO UPDATE SET
            value = excluded.value,
            data_type = excluded.data_type,
            updated_at = CURRENT_TIMESTAMP
        """,
        (document_id, key, value, data_type)
    )
    crmdb.commit()

def get_all_document_metadata(document_id: int) -> Dict[str, Any]:
    """
    Get all metadata for a document.
    Returns a dictionary of all metadata with appropriate type conversion.
    """
    cursor_crm.execute(
        """
        SELECT key, value, data_type 
        FROM document_metadata 
        WHERE document_id = ?
        """,
        (document_id,)
    )
    
    metadata = {}
    for row in cursor_crm.fetchall():
        key = row['key']
        value = row['value']
        data_type = row['data_type']
        
        if value is None:
            metadata[key] = None
            continue
            
        try:
            if data_type == 'int':
                metadata[key] = int(value)
            elif data_type == 'float':
                metadata[key] = float(value)
            elif data_type == 'bool':
                metadata[key] = value.lower() == 'true'
            elif data_type == 'json':
                metadata[key] = json.loads(value) if value else {}
            elif data_type == 'datetime':
                metadata[key] = datetime.fromisoformat(value)
            else:  # 'str' or unknown
                metadata[key] = value
        except (ValueError, json.JSONDecodeError) as e:
            logging.warning(f"Error converting metadata {key}={value} (type: {data_type}): {str(e)}")
            metadata[key] = value
    
    return metadata
    
def get_document_metadata(document_id: int, key: str) -> Any:
    """
    Get metadata for a document by key.
    Returns the value with appropriate type conversion.
    """
    cursor_crm.execute(
        """
        SELECT value, data_type 
        FROM document_metadata 
        WHERE document_id = ? AND key = ?
        """,
        (document_id, key)
    )
    
    result = cursor_crm.fetchone()
    if not result:
        return None
    
    value = result['value']
    data_type = result['data_type']
    
    if value is None:
        return None
        
    try:
        if data_type == 'int':
            return int(value)
        elif data_type == 'float':
            return float(value)
        elif data_type == 'bool':
            return value.lower() == 'true'
        elif data_type == 'json':
            return json.loads(value) if value else {}
        elif data_type == 'datetime':
            return datetime.fromisoformat(value)
        else:  # 'str' or unknown
            return value
    except (ValueError, json.JSONDecodeError) as e:
        logging.warning(f"Error converting metadata {key}={value} (type: {data_type}): {str(e)}")
        return value

def update_document_status(document_id: int, status: str, error_message: str = None) -> None:
    """
    Update the status of a document.
    """
    cursor_crm.execute(
        """
        UPDATE documents 
        SET status = ?, 
            error_message = ?,
            upload_time = CASE WHEN ? IS NOT NULL THEN upload_time ELSE upload_time END
        WHERE id = ?
        """,
        (status, error_message, error_message, document_id)
    )
    crmdb.commit()

def get_document(document_id: int) -> dict:
    """
    Get document details by ID.
    """
    cursor_crm.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    row = cursor_crm.fetchone()
    return dict(row) if row else None

def get_document_intents(document_id: int) -> List[dict]:
    """
    Get all intents for a document.
    """
    cursor_crm.execute("SELECT * FROM intents WHERE document_id = ?", (document_id,))
    return [dict(row) for row in cursor_crm.fetchall()]

def get_agent_responses(document_id: int, intent_id: int = None) -> List[dict]:
    """
    Get agent responses for a document, optionally filtered by intent.
    """
    if intent_id:
        cursor_crm.execute(
            "SELECT * FROM agent_responses WHERE document_id = ? AND intent_id = ?",
            (document_id, intent_id)
        )
    else:
        cursor_crm.execute(
            "SELECT * FROM agent_responses WHERE document_id = ?",
            (document_id,)
        )
    
    results = []
    for row in cursor_crm.fetchall():
        result = dict(row)
        # Parse JSON data
        if 'response_data' in result and result['response_data']:
            try:
                result['response_data'] = json.loads(result['response_data'])
            except json.JSONDecodeError:
                pass
        if 'metadata' in result and result['metadata']:
            try:
                result['metadata'] = json.loads(result['metadata'])
            except json.JSONDecodeError:
                pass
        results.append(result)
    
    return results
