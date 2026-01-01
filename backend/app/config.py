"""
Configuration settings for LIBER
"""
import os
import socket
from datetime import timedelta
from dotenv import load_dotenv
# Check if we're in Docker (env_file in docker-compose should already set env vars)
is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/self/cgroup')

# Check if OPENAI_API_KEY is already set (from Docker env_file or host environment)
openai_key_before = os.getenv('OPENAI_API_KEY', '')

# Define possible .env locations
env_paths = [
    '.env',  # Current directory
    'backend/.env',  # Relative from project root
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # Relative from app/
    os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env'),  # Absolute from app/
    '/app/.env',  # Inside Docker container
    '/app/backend/.env',  # Inside Docker container (alternative)
]

# If not in Docker or key not set, try to load from .env file
env_file_found = None
if not is_docker or not openai_key_before:
    for path in env_paths:
        abs_path = os.path.abspath(path) if not path.startswith('/') else path
        if os.path.exists(abs_path):
            env_file_found = abs_path
            break

# Try loading from found path or default
# In Docker, env_file should already set variables, but we load .env as fallback
if env_file_found:
    load_dotenv(dotenv_path=env_file_found, override=False)  # override=False: don't override existing env vars
elif not is_docker:
    # Only try default load_dotenv() if not in Docker (to avoid unnecessary file system access)
    load_dotenv(override=False)


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Database - PostgreSQL (Supabase)
    # Supabase provides DATABASE_URL in format: postgresql://postgres:[password]@[host]:5432/postgres
    # For Docker containers, use Connection Pooler (port 6543) instead of direct connection (port 5432)
    # to avoid IPv6 issues. Pooler format: postgresql://postgres:[password]@[host]:6543/postgres
    # Handle both postgres:// and postgresql:// formats (Supabase sometimes uses postgres://)
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    if DATABASE_URL:
        # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        # If using Supabase direct connection (port 5432) and we're in Docker, switch to pooler (port 6543)
        # This avoids IPv6 connectivity issues in Docker containers
        if ':5432/' in SQLALCHEMY_DATABASE_URI and 'supabase.co' in SQLALCHEMY_DATABASE_URI:
            if is_docker:
                SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(':5432/', ':6543/')
        
        # Force IPv4 resolution for Supabase connections in Docker to avoid IPv6 issues
        if is_docker and 'supabase.co' in SQLALCHEMY_DATABASE_URI:
            try:
                # Extract hostname from connection string
                # Format: postgresql://user:pass@host:port/db
                parts = SQLALCHEMY_DATABASE_URI.split('@')
                if len(parts) == 2:
                    host_port_db = parts[1]
                    host_port = host_port_db.split('/')[0]
                    if ':' in host_port:
                        hostname, port = host_port.rsplit(':', 1)
                        
                        # Resolve hostname to IPv4 address
                        # getaddrinfo returns (family, type, proto, canonname, sockaddr)
                        # We filter for AF_INET (IPv4) only
                        addrinfo = socket.getaddrinfo(hostname, int(port), socket.AF_INET, socket.SOCK_STREAM)
                        if addrinfo:
                            # Get first IPv4 address
                            ipv4_address = addrinfo[0][4][0]
                            # Replace hostname with IPv4 address in connection string
                            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(f'{hostname}:{port}', f'{ipv4_address}:{port}')
            except (socket.gaierror, ValueError, IndexError) as e:
                # If DNS resolution fails, log warning but continue with original hostname
                # This allows the connection to be attempted normally
                pass
    else:
        # Fallback to individual components if DATABASE_URL is not provided
        POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
        POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
        POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
        
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
            f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Qdrant Vector DB
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
    QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'wines')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-mini-2025-08-07')  # Conversational model for opening messages (use gpt-4o-mini as default, can be overridden with gpt-5 if available)
    OPENAI_FINETUNED_MODEL = os.getenv('OPENAI_FINETUNED_MODEL', 'ft:gpt-4.1-mini-2025-04-14:personal:liber-ai:CoTKB8PZ')  # Fine-tuned model for wine selection (from .env)
    OPENAI_COMMUNICATION_MODEL = os.getenv('OPENAI_COMMUNICATION_MODEL', 'gpt-5-mini-2025-08-07')  # Model for natural language communication
    OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    
    # Frontend
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # Supabase Storage
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    SUPABASE_STORAGE_BUCKET_QRCODES = os.getenv('SUPABASE_STORAGE_BUCKET_QRCODES', 'qrcodes')
    SUPABASE_STORAGE_BUCKET_WINE_LABELS = os.getenv('SUPABASE_STORAGE_BUCKET_WINE_LABELS', 'wine-labels')
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '20'))


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

