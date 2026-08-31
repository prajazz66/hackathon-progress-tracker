from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
from werkzeug.utils import secure_filename
from extensions import db
from models import Attachment
from services.storage_service import (
    is_allowed_file,
    upload_file_content,
    download_file_content,
    delete_file_content,
    decompress_if_needed
)
import uuid
import gzip
import io
import markdown
import logging

logger = logging.getLogger(__name__)

file_bp = Blueprint('file', __name__)

@file_bp.route('/upload_file/<int:hackathon_id>', methods=['POST'])
def upload_file(hackathon_id):
    if not session.get('authenticated'):
        return redirect(url_for('hackathon.index'))
    
    if 'file' not in request.files:
        return redirect(url_for('hackathon.index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('hackathon.index'))
    
    if file and is_allowed_file(file.filename):
        try:
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            content = file.read()
            
            # Compress large PDFs
            if file_ext == 'pdf' and len(content) > 500000:
                compressed_io = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed_io, mode='wb') as gz:
                    gz.write(content)
                content = compressed_io.getvalue()
                unique_filename += '.gz'
                
            upload_file_content(unique_filename, content, file_ext)
            
            attachment = Attachment(
                hackathon_id=hackathon_id,
                original_filename=original_filename,
                stored_filename=unique_filename,
                file_type=file_ext
            )
            db.session.add(attachment)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error handling file upload for hackathon ID {hackathon_id}: {e}")
            db.session.rollback()
    
    return redirect(url_for('hackathon.index'))

@file_bp.route('/view_file/<filename>')
def view_file(filename):
    try:
        bucket_type = request.args.get('bucket', 'main')
        content = download_file_content(filename, bucket_type=bucket_type)
        if content is None:
            return "File not found", 404
            
        content = decompress_if_needed(content, filename)
        display_name = filename[:-3] if filename.endswith('.gz') else filename
        
        if display_name.endswith('.md'):
            text_content = content.decode('utf-8', errors='replace')
            html_content = markdown.markdown(text_content, extensions=['fenced_code', 'tables', 'toc'])
            return render_template('view_md.html', content=html_content, filename=filename)
        elif display_name.endswith('.pdf'):
            response = make_response(content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename={display_name}'
            return response
            
        return "Unsupported file type", 400
    except Exception as e:
        logger.error(f"Error viewing file {filename}: {e}")
        return "An error occurred while displaying the file", 500

@file_bp.route('/delete_file/<int:hackathon_id>/<filename>', methods=['POST'])
def delete_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('hackathon.index'))
    
    try:
        attachment = Attachment.query.filter_by(hackathon_id=hackathon_id, stored_filename=filename).first()
        if attachment:
            delete_file_content(filename)
            db.session.delete(attachment)
            db.session.commit()
    except Exception as e:
        logger.error(f"Error deleting file {filename}: {e}")
        db.session.rollback()
        
    return redirect(url_for('hackathon.index'))

@file_bp.route('/modify_file/<int:hackathon_id>/<filename>')
def modify_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('hackathon.index'))
    
    try:
        content = download_file_content(filename)
        if content is None:
            return "File not found", 404
            
        text_content = content.decode('utf-8', errors='replace')
        return render_template('edit_md.html', hackathon_id=hackathon_id, filename=filename, content=text_content)
    except Exception as e:
        logger.error(f"Error modifying file {filename}: {e}")
        return redirect(url_for('hackathon.index'))

@file_bp.route('/save_md_file/<int:hackathon_id>/<filename>', methods=['POST'])
def save_md_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('hackathon.index'))
    
    try:
        content = request.form.get('content', '')
        upload_file_content(filename, content.encode('utf-8'), 'md')
    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        return f"Failed to save file: {e}", 500
        
    return redirect(url_for('hackathon.index'))
