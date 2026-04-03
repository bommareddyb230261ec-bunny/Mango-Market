"""
Database Configuration Module
Handles connection to MySQL database using SQLAlchemy with environment variables.
Supports both Flask-SQLAlchemy and standalone SQLAlchemy usage.
"""

import os
from typing import Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Load environment variables from .env file
load_dotenv()


# =====================================================
# DATABASE CREDENTIALS FROM ENVIRONMENT VARIABLES
# =====================================================
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'mango_market_db')
DB_DRIVER = os.getenv('DB_DRIVER', 'pymysql')
DB_TYPE = os.getenv('DB_TYPE', 'mysql')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


# =====================================================
# DATABASE URL CONSTRUCTION
# =====================================================
def get_database_url() -> str:
    """Construct the database URL for MySQL or SQLite."""
    if DB_TYPE.lower() == 'sqlite':
        db_path = os.getenv('SQLITE_DB_PATH', 'instance/mango_market.db')
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        return f"sqlite:///{db_path}"
    
    # MySQL connection
    if not DB_PASSWORD:
        return f"mysql+{DB_DRIVER}://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        from urllib.parse import quote_plus
        encoded_password = quote_plus(DB_PASSWORD)
        return f"mysql+{DB_DRIVER}://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# =====================================================
# SQLALCHEMY ENGINE CONFIGURATION
# =====================================================
def create_db_engine():
    """Create SQLAlchemy engine for MySQL or SQLite database."""
    database_url = get_database_url()
    
    if DB_TYPE.lower() == 'sqlite':
        return create_engine(
            database_url,
            poolclass=None,
            echo=False,
            future=True,
            connect_args={
                'check_same_thread': False,
                'timeout': 10
            }
        )
    else:
        # MySQL configuration
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            future=True,
            connect_args={
                'charset': 'utf8mb4',
                'autocommit': False,
                'connect_timeout': 10,
            }
        )


# =====================================================
# SESSION FACTORY
# =====================================================
def create_session_factory(engine=None):
    """Create a session factory for database operations."""
    if engine is None:
        engine = create_db_engine()
    
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=Session
    )


# =====================================================
# CONNECTION TESTING & UTILITIES
# =====================================================
def test_database_connection(engine=None) -> bool:
    """Test if database connection is working."""
    try:
        if engine is None:
            engine = create_db_engine()
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.close()
            return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


def get_database_info(engine=None) -> dict:
    """Get information about the database."""
    if engine is None:
        engine = create_db_engine()
    
    inspector = inspect(engine)
    
    return {
        'database_name': DB_NAME,
        'host': DB_HOST,
        'port': DB_PORT,
        'tables': inspector.get_table_names(),
        'table_count': len(inspector.get_table_names()),
    }


def print_database_info(engine=None) -> None:
    """Print formatted database information."""
    info = get_database_info(engine)
    print("\n" + "="*50)
    print("DATABASE INFORMATION")
    print("="*50)
    print(f"Database: {info['database_name']}")
    print(f"Host: {info['host']}")
    print(f"Port: {info['port']}")
    print(f"Total Tables: {info['table_count']}")
    if info['tables']:
        print("\nExisting Tables:")
        for table in info['tables']:
            print(f"  - {table}")
    else:
        print("\nNo tables found. Run Base.metadata.create_all() to create them.")
    print("="*50 + "\n")


# =====================================================
# FLASK-SQLALCHEMY CONFIGURATION CLASS
# =====================================================
class MySQLConfig:
    """Configuration class for Flask with MySQL backend."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mango_market_secure_key_2026')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'echo': False,
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 10,
        }
    }
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'mango_session'
    PERMANENT_SESSION_LIFETIME = 3600


if __name__ == '__main__':
    print("Testing Database Connection...\n")
    
    engine = create_db_engine()
    
    if test_database_connection(engine):
        print_database_info(engine)
    else:
        print("\nWarning: Database connection failed. Check your credentials in .env file")
        print(f"\nCurrent Configuration:")
        print(f"  Type: {DB_TYPE}")
        print(f"  Host: {DB_HOST}")
        print(f"  Port: {DB_PORT}")
        print(f"  User: {DB_USER}")
        print(f"  Database: {DB_NAME}")
