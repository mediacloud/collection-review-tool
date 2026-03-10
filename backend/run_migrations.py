"""Run all database migrations in order.

This script runs all manual migration scripts in the correct order.
It's designed to be idempotent - safe to run multiple times.
Works with both SQLite and PostgreSQL.

Usage:
    python backend/run_migrations.py
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up environment for Flask app
os.environ.setdefault('FLASK_APP', 'app:create_app')

def run_all_migrations():
    """Run all migrations using SQLAlchemy."""
    from app import create_app
    from database import db
    from sqlalchemy import inspect, text
    
    app = create_app()
    
    with app.app_context():
        # Get database connection info
        engine = db.engine
        inspector = inspect(engine)
        is_sqlite = 'sqlite' in str(engine.url)
        
        print("Starting database migrations...")
        print(f"Database: {engine.url.drivername}")
        
        # Get connection for raw SQL
        conn = engine.connect()
        trans = conn.begin()
        
        try:
            # Migration 1: collection_name
            print("\nRunning migration: collection_name")
            if is_sqlite:
                # SQLite: Check if column exists
                result = conn.execute(text("PRAGMA table_info(reviews)"))
                columns = [row[1] for row in result]
                if 'collection_name' in columns:
                    print("Column 'collection_name' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN collection_name TEXT"))
                    print("Successfully added 'collection_name' column.")
            else:
                # PostgreSQL: Check if column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='reviews' AND column_name='collection_name'
                """))
                if result.fetchone():
                    print("Column 'collection_name' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN collection_name TEXT"))
                    print("Successfully added 'collection_name' column.")
            
            # Migration 2: removal_reason
            print("\nRunning migration: removal_reason")
            if is_sqlite:
                result = conn.execute(text("PRAGMA table_info(review_items)"))
                columns = [row[1] for row in result]
                if 'removal_reason' in columns:
                    print("Column 'removal_reason' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE review_items ADD COLUMN removal_reason TEXT"))
                    print("Successfully added 'removal_reason' column.")
            else:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='review_items' AND column_name='removal_reason'
                """))
                if result.fetchone():
                    print("Column 'removal_reason' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE review_items ADD COLUMN removal_reason TEXT"))
                    print("Successfully added 'removal_reason' column.")
            
            # Migration 3: source_metadata
            print("\nRunning migration: source_metadata")
            if is_sqlite:
                result = conn.execute(text("PRAGMA table_info(review_items)"))
                columns = [row[1] for row in result]
                if 'source_metadata' in columns:
                    print("Column 'source_metadata' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE review_items ADD COLUMN source_metadata TEXT"))
                    print("Successfully added 'source_metadata' column.")
            else:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='review_items' AND column_name='source_metadata'
                """))
                if result.fetchone():
                    print("Column 'source_metadata' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE review_items ADD COLUMN source_metadata TEXT"))
                    print("Successfully added 'source_metadata' column.")
            
            # Migration 4: guidelines_template
            print("\nRunning migration: guidelines_template")
            if is_sqlite:
                result = conn.execute(text("PRAGMA table_info(reviews)"))
                columns = [row[1] for row in result]
                if 'guidelines_template' in columns:
                    print("Column 'guidelines_template' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN guidelines_template TEXT DEFAULT 'default'"))
                    print("Successfully added 'guidelines_template' column.")
            else:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='reviews' AND column_name='guidelines_template'
                """))
                if result.fetchone():
                    print("Column 'guidelines_template' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN guidelines_template TEXT DEFAULT 'default'"))
                    print("Successfully added 'guidelines_template' column.")
            
            # Migration 5: edit_metadata flag on reviews
            print("\nRunning migration: edit_metadata")
            if is_sqlite:
                result = conn.execute(text("PRAGMA table_info(reviews)"))
                columns = [row[1] for row in result]
                if 'edit_metadata' in columns:
                    print("Column 'edit_metadata' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN edit_metadata BOOLEAN DEFAULT 0"))
                    print("Successfully added 'edit_metadata' column.")
            else:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='reviews' AND column_name='edit_metadata'
                """))
                if result.fetchone():
                    print("Column 'edit_metadata' already exists. No migration needed.")
                else:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN edit_metadata BOOLEAN DEFAULT FALSE"))
                    print("Successfully added 'edit_metadata' column.")
            
            trans.commit()
            print("\n✓ All migrations completed successfully.")
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error during migration: {e}")
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    run_all_migrations()
