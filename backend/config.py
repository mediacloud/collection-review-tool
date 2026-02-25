"""Configuration management for the application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    # Database configuration
    # Normalize postgres URLs from older schemes (e.g. dokku/postgres)
    _raw_db_url = os.getenv('DATABASE_URL', 'sqlite:///reviews.db')
    if _raw_db_url.startswith('postgres://'):
        _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
    DATABASE_URL = _raw_db_url
    
    # MediaCloud API configuration
    MEDIACLOUD_API_KEY = os.getenv('MEDIACLOUD_API_KEY')
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def get_config():
    """Get configuration instance."""
    return Config()
