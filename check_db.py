import sqlite3
import json

def check_database():
    try:
        conn = sqlite3.connect('memory/agent_data.db')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:", tables)
        
        # Get data from agent_data table
        cursor.execute("SELECT * FROM agent_data;")
        columns = [description[0] for description in cursor.description]
        print("\nColumns in agent_data:", columns)
        
        # Fetch all rows
        rows = cursor.fetchall()
        print(f"\nFound {len(rows)} records in agent_data:")
        for row in rows:
            print("\nRecord:")
            for col, value in zip(columns, row):
                print(f"  {col}: {value}")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database()
