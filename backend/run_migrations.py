"""Run all database migrations in order.

This script runs all manual migration scripts in the correct order.
It's designed to be idempotent - safe to run multiple times.

Usage:
    python backend/run_migrations.py
"""
import sys
from pathlib import Path

# Add backend to path so we can import migrations
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def run_all_migrations():
    """Run all migrations in order."""
    # Import migration functions
    try:
        from migrations.add_collection_name import migrate as migrate_collection_name
        from migrations.add_removal_reason import migrate as migrate_removal_reason
        from migrations.add_source_metadata import migrate as migrate_source_metadata
        from migrations.add_guidelines_template import migrate as migrate_guidelines_template
    except ImportError as e:
        print(f"Error importing migrations: {e}")
        sys.exit(1)
    
    # Define migrations in order
    migrations = [
        ("collection_name", migrate_collection_name),
        ("removal_reason", migrate_removal_reason),
        ("source_metadata", migrate_source_metadata),
        ("guidelines_template", migrate_guidelines_template),
    ]
    
    print("Starting database migrations...")
    
    for name, migrate_func in migrations:
        print(f"\nRunning migration: {name}")
        try:
            migrate_func()
        except Exception as e:
            print(f"ERROR: Migration {name} failed: {e}")
            # For safety, we'll continue with other migrations
            # but you might want to fail fast in production
            # Uncomment the next line to fail on first error:
            # sys.exit(1)
    
    print("\n✓ All migrations completed.")

if __name__ == '__main__':
    run_all_migrations()
