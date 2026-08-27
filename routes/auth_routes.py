from flask import Blueprint, render_template, request, redirect, url_for, session
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        passcode = request.form.get('passcode', '')
        if passcode == 'Oneshot':
            session['authenticated'] = True
            return redirect(url_for('hackathon.index'))
        return render_template('login.html', error='Invalid passcode')
    except Exception as e:
        logger.error(f"Login error: {e}")
        return render_template('login.html', error='An unexpected error occurred.')

@auth_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('hackathon.index'))
