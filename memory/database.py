import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

class DatabaseManager:
    def __init__(self):
        self.db_path = Path(__file__).parent / "agent_data.db"
        self.initialize_db()

    def initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create table for agent data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agent_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    agent_type TEXT,
                    file_name TEXT,
                    intent TEXT,
                    data TEXT,  -- JSON string of the agent's data
                    status TEXT,
                    requires_followup BOOLEAN DEFAULT 0,
                    followup_notes TEXT
                )
            ''')
            
            # Create table for CRM data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crm_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    client_name TEXT,
                    contact_info TEXT,
                    document_type TEXT,
                    document_id TEXT,
                    status TEXT,
                    notes TEXT
                )
            ''')
            
            conn.commit()

    def log_agent_data(self, agent_type: str, file_name: str, intent: str, data: Dict[str, Any], status: str = "processed") -> int:
        print(f"[DB] Logging agent data - Type: {agent_type}, File: {file_name}, Intent: {intent}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                print(f"[DB] Executing INSERT query...")
                cursor.execute('''
                    INSERT INTO agent_data (timestamp, agent_type, file_name, intent, data, status, requires_followup)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, agent_type, file_name, intent, json.dumps(data), status, 0))
                conn.commit()
                last_id = cursor.lastrowid
                print(f"[DB] Successfully logged data with ID: {last_id}")
                return last_id
        except Exception as e:
            print(f"[DB ERROR] Failed to log agent data: {str(e)}")
            raise
            
    def get_agent_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, agent_type, file_name, intent, data, status, requires_followup, followup_notes
                FROM agent_data 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result['data'] = json.loads(result['data'])
                results.append(result)
            return results
            
    def add_followup_notes(self, record_id: int, notes: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE agent_data 
                SET requires_followup = 1, 
                    followup_notes = ?
                WHERE id = ?
            ''', (notes, record_id))
            conn.commit()
            
    def get_agent_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, agent_type, file_name, intent, data, status, requires_followup, followup_notes
                FROM agent_data 
                WHERE id = ?
            ''', (record_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['data'] = json.loads(result['data'])
                return result
            return None

    def add_crm_record(self, client_name, contact_info, document_type, document_id, status, notes):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO crm_data (timestamp, client_name, contact_info, document_type, document_id, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, client_name, contact_info, document_type, document_id, status, notes))
            conn.commit()

    def get_crm_records(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM crm_data ORDER BY timestamp DESC')
            return cursor.fetchall()

    def get_agent_logs(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM agent_logs ORDER BY timestamp DESC')
            return cursor.fetchall()
