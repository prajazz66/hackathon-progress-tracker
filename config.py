import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hackathon-tracker-secret-key')
    
    # Database configuration with postgres:// -> postgresql:// conversion
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url and ('[YOUR-PASSWORD]' in raw_db_url or not raw_db_url.strip()):
        raw_db_url = None  # Fallback to local SQLite until real password is provided
    elif raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = raw_db_url or 'sqlite:///hackathons.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supabase credentials
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'attachments')
    
    # Supabase participated events bucket (separate from main attachments bucket)
    SUPABASE_PARTICIPATED_BUCKET = os.environ.get('SUPABASE_PARTICIPATED_BUCKET', '')
    
    # Local fallback file config
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    PARTICIPATED_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'participated')
    ALLOWED_EXTENSIONS = {'md', 'pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
