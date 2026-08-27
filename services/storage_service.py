import os
import gzip
import io
import shutil
import logging
from werkzeug.utils import secure_filename
from config import Config
from extensions import supabase_client

logger = logging.getLogger(__name__)

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.PARTICIPATED_UPLOAD_FOLDER, exist_ok=True)

def _get_bucket_and_folder(bucket_type='main'):
    """Resolve the Supabase bucket name and local folder for a given bucket type."""
    if bucket_type == 'participated':
        bucket_name = Config.SUPABASE_PARTICIPATED_BUCKET
        local_folder = Config.PARTICIPATED_UPLOAD_FOLDER
    else:
        bucket_name = Config.SUPABASE_BUCKET
        local_folder = Config.UPLOAD_FOLDER
    return bucket_name, local_folder

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def upload_file_content(unique_filename, file_content, file_ext, bucket_type='main'):
    """Upload content to Supabase Storage or fallback to local disk."""
    bucket_name, local_folder = _get_bucket_and_folder(bucket_type)
    
    if supabase_client and bucket_name:
        try:
            content_type = "application/pdf" if file_ext == 'pdf' else "text/markdown"
            supabase_client.storage.from_(bucket_name).upload(
                path=unique_filename,
                file=file_content,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            logger.info(f"Uploaded {unique_filename} to Supabase bucket '{bucket_name}'")
            return True
        except Exception as e:
            logger.error(f"Supabase upload failed for {unique_filename}: {e}")
            raise e
    else:
        try:
            stored_path = os.path.join(local_folder, unique_filename)
            with open(stored_path, 'wb') as f:
                f.write(file_content)
            logger.info(f"Saved {unique_filename} locally to {stored_path}")
            return True
        except Exception as e:
            logger.error(f"Local file write failed for {unique_filename}: {e}")
            raise e

def download_file_content(stored_filename, bucket_type='main'):
    """Download content from Supabase Storage or fallback to local disk."""
    bucket_name, local_folder = _get_bucket_and_folder(bucket_type)
    content = None
    
    if supabase_client and bucket_name:
        try:
            content = supabase_client.storage.from_(bucket_name).download(stored_filename)
        except Exception as e:
            logger.error(f"Supabase download failed for {stored_filename}: {e}")
            
    if content is None:
        safe_name = secure_filename(stored_filename)
        local_path = os.path.join(local_folder, safe_name)
        if os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read local file {local_path}: {e}")
        else:
            logger.warning(f"File {stored_filename} not found locally or on Supabase.")
            
    return content

def delete_file_content(stored_filename, bucket_type='main'):
    """Delete file from Supabase Storage or local disk."""
    bucket_name, local_folder = _get_bucket_and_folder(bucket_type)
    
    if supabase_client and bucket_name:
        try:
            supabase_client.storage.from_(bucket_name).remove([stored_filename])
            logger.info(f"Removed {stored_filename} from Supabase bucket '{bucket_name}'.")
        except Exception as e:
            logger.error(f"Failed to delete {stored_filename} from Supabase: {e}")
    else:
        safe_name = secure_filename(stored_filename)
        local_path = os.path.join(local_folder, safe_name)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.info(f"Removed local file {local_path}")
            except Exception as e:
                logger.error(f"Failed to remove local file {local_path}: {e}")

def move_file_to_participated_bucket(stored_filename):
    """Move a file from the main bucket to the participated bucket."""
    try:
        # Download from main bucket
        content = download_file_content(stored_filename, bucket_type='main')
        if content is None:
            logger.warning(f"Cannot move {stored_filename}: file not found in main bucket.")
            return False
        
        # Determine file extension for upload
        file_ext = stored_filename.rsplit('.', 1)[-1].lower() if '.' in stored_filename else 'md'
        if file_ext == 'gz':
            # For .md.gz or .pdf.gz files, get the actual extension
            base = stored_filename[:-3]  # Remove .gz
            file_ext = base.rsplit('.', 1)[-1].lower() if '.' in base else 'md'
        
        # Upload to participated bucket
        upload_file_content(stored_filename, content, file_ext, bucket_type='participated')
        
        # Delete from main bucket
        delete_file_content(stored_filename, bucket_type='main')
        
        logger.info(f"Moved {stored_filename} from main to participated bucket.")
        return True
    except Exception as e:
        logger.error(f"Failed to move file {stored_filename} to participated bucket: {e}")
        return False

def decompress_if_needed(content, filename):
    """Decompress gzip content if filename ends with .gz."""
    if filename.endswith('.gz'):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(content), mode='rb') as gz:
                return gz.read()
        except Exception as e:
            logger.error(f"Gzip decompression failed for {filename}: {e}")
            return content
    return content
