"""Database initialization and setup."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Initialize SQLAlchemy instance (will be initialized with app in init_db)
db = SQLAlchemy()


def init_db(app: Flask):
    """Initialize database with Flask app."""
    db.init_app(app)
    
    # Enable foreign keys for SQLite
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    # Create all tables
    with app.app_context():
        db.create_all()


def get_db():
    """Get database instance."""
    return db
