from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        allowed_users = current_app.config.get('ALLOWED_USERS', {})
        
        if username and password and username in allowed_users and allowed_users[username] == password:
            session.permanent = True
            session['authenticated'] = True
            session['username'] = username
            logger.info(f"User '{username}' logged in successfully.")
            return redirect(url_for('hackathon.index'))
            
        logger.warning(f"Failed login attempt for username '{username}'.")
        return render_template('login.html', error='Invalid username or password')
    except Exception as e:
        logger.error(f"Login error: {e}")
        return render_template('login.html', error='An unexpected error occurred.')

@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'user')
    session.clear()
    logger.info(f"User '{username}' logged out.")
    return redirect(url_for('hackathon.index'))
