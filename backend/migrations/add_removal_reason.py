"""Migration script to add removal_reason column to review_items table.

Run this script to add the removal_reason column to existing databases:
    python -m backend.migrations.add_removal_reason

Or run it directly:
    python backend/migrations/add_removal_reason.py
"""
import sqlite3
import os
import sys
from pathlib import Path

# Get the database path
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / 'backend' / 'instance' / 'reviews.db'

def migrate():
    """Add removal_reason column to review_items table if it doesn't exist."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("The column will be created automatically when the app starts.")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(review_items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'removal_reason' in columns:
            print("Column 'removal_reason' already exists. No migration needed.")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE review_items 
                ADD COLUMN removal_reason TEXT
            """)
            conn.commit()
            print("Successfully added 'removal_reason' column to review_items table.")
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
