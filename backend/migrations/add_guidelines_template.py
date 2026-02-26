"""Migration script to add guidelines_template column to reviews table.

Run this script to add the guidelines_template column to existing databases:
    python -m backend.migrations.add_guidelines_template

Or run it directly:
    python backend/migrations/add_guidelines_template.py
"""
import sqlite3
import os
import sys
from pathlib import Path

# Get the database path
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / 'backend' / 'instance' / 'reviews.db'

def migrate():
    """Add guidelines_template column to reviews table if it doesn't exist."""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("The column will be created automatically when the app starts.")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'guidelines_template' in columns:
            print("Column 'guidelines_template' already exists. No migration needed.")
        else:
            # Add the column with default value
            cursor.execute("""
                ALTER TABLE reviews 
                ADD COLUMN guidelines_template TEXT DEFAULT 'default'
            """)
            conn.commit()
            print("Successfully added 'guidelines_template' column to reviews table.")
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
