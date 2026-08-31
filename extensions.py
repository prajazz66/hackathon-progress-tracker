from flask_sqlalchemy import SQLAlchemy
from supabase import create_client
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

supabase_client = None
if Config.SUPABASE_URL and Config.SUPABASE_KEY:
    try:
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.info("Supabase credentials not configured. Using local filesystem fallback.")
