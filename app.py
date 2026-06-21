from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import json
import os
import uuid
import gzip
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'hackathon-tracker-secret-key'

DATA_FILE = 'hackathons.json'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'md', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'hackathons': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_live_hackathons():
    import requests
    try:
        r = requests.get("https://devpost.com/api/hackathons?page=1", timeout=5)
        if r.status_code == 200:
            data = r.json()
            hackathons = data.get('hackathons', [])[:5]
            for h in hackathons:
                if h.get('thumbnail_url') and not h['thumbnail_url'].startswith('http'):
                    h['thumbnail_url'] = 'https:' + h['thumbnail_url']
            return hackathons
    except:
        pass
    return []

@app.route('/')
def index():
    if not session.get('authenticated'):
        return render_template('login.html')
    data = load_data()
    live_hackathons = fetch_live_hackathons()
    return render_template('dashboard.html', hackathons=data['hackathons'], live_hackathons=live_hackathons)

@app.route('/login', methods=['POST'])
def login():
    passcode = request.form.get('passcode', '')
    if passcode == 'oneshot':
        session['authenticated'] = True
        return redirect(url_for('index'))
    return render_template('login.html', error='Invalid passcode')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

@app.route('/add_hackathon', methods=['POST'])
def add_hackathon():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    date = request.form.get('date', '').strip()
    description = request.form.get('description', '').strip()
    if name:
        data = load_data()
        hackathon = {
            'id': len(data['hackathons']) + 1,
            'name': name,
            'date': date if date else None,
            'description': description if description else None,
            'progress': 0,
            'notes': [],
            'file_attachments': []
        }
        data['hackathons'].append(hackathon)
        save_data(data)
    return redirect(url_for('index'))

@app.route('/delete_hackathon/<int:hackathon_id>', methods=['POST'])
def delete_hackathon(hackathon_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    data = load_data()
    hackathon = next((h for h in data['hackathons'] if h['id'] == hackathon_id), None)
    if hackathon and hackathon.get('file_attachments'):
        for file_info in hackathon['file_attachments']:
            file_path = os.path.join(UPLOAD_FOLDER, file_info.get('stored_filename', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
    data['hackathons'] = [h for h in data['hackathons'] if h['id'] != hackathon_id]
    save_data(data)
    return redirect(url_for('index'))

@app.route('/update_progress/<int:hackathon_id>', methods=['POST'])
def update_progress(hackathon_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    try:
        progress = int(request.form.get('progress', 0))
        note = request.form.get('note', '').strip()
        
        data = load_data()
        for h in data['hackathons']:
            if h['id'] == hackathon_id:
                h['progress'] = h['progress'] + progress
                if h['progress'] > 100:
                    h['progress'] = 100
                if h['progress'] < 0:
                    h['progress'] = 0
                if note:
                    h['notes'].insert(0, {
                        'progress': h['progress'],
                        'note': note
                    })
                break
        save_data(data)
    except (ValueError, TypeError):
        pass
    
    return redirect(url_for('index'))

@app.route('/upload_file/<int:hackathon_id>', methods=['POST'])
def upload_file(hackathon_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        stored_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        if file_ext == 'md':
            with open(stored_path, 'wb') as f:
                f.write(file.read())
        else:  # PDF - compress if large
            content = file.read()
            if len(content) > 500000:  # > 500KB, compress
                with gzip.open(stored_path + '.gz', 'wb') as f:
                    f.write(content)
                unique_filename += '.gz'
            else:
                with open(stored_path, 'wb') as f:
                    f.write(content)
        
        data = load_data()
        for h in data['hackathons']:
            if h['id'] == hackathon_id:
                if 'file_attachments' not in h:
                    h['file_attachments'] = []
                h['file_attachments'].append({
                    'original_filename': original_filename,
                    'stored_filename': unique_filename,
                    'file_type': file_ext
                })
                break
        save_data(data)
    
    return redirect(url_for('index'))

@app.route('/view_file/<filename>')
def view_file(filename):
    safe_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if not os.path.exists(safe_path):
        return "File not found", 404
    
    if filename.endswith('.md') or ('.md' in filename and not filename.endswith('.gz')):
        with open(safe_path, 'r') as f:
            content = f.read()
        # Convert markdown to HTML
        import markdown
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'toc'])
        return render_template('view_md.html', content=html_content, filename=filename)
    elif filename.endswith('.pdf'):
        return send_from_directory(UPLOAD_FOLDER, filename, mimetype='application/pdf')
    elif filename.endswith('.gz'):
        import gzip
        with gzip.open(safe_path, 'rb') as f:
            content = f.read()
        return send_from_directory(UPLOAD_FOLDER, filename.replace('.gz', ''), mimetype='application/pdf')

@app.route('/delete_file/<int:hackathon_id>/<filename>', methods=['POST'])
def delete_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    safe_filename = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    
    data = load_data()
    for h in data['hackathons']:
        if h['id'] == hackathon_id:
            h['file_attachments'] = [f for f in h.get('file_attachments', []) if f['stored_filename'] != safe_filename]
            break
    save_data(data)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    # Also check for compressed version
    gz_path = file_path + '.gz'
    if os.path.exists(gz_path):
        os.remove(gz_path)
    
    return redirect(url_for('index'))

@app.route('/modify_file/<int:hackathon_id>/<filename>')
def modify_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    safe_filename = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext == 'md':
        with open(file_path, 'r') as f:
            content = f.read()
        return render_template('edit_md.html', hackathon_id=hackathon_id, filename=safe_filename, content=content)
    
    # For PDFs, redirect to upload (replace) flow
    return redirect(url_for('index'))

@app.route('/save_md_file/<int:hackathon_id>/<filename>', methods=['POST'])
def save_md_file(hackathon_id, filename):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    safe_filename = secure_filename(filename)
    file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    content = request.form.get('content', '')
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return redirect(url_for('index'))

@app.route('/export_csv')
def export_csv():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    import csv
    from io import StringIO
    from flask import Response
    
    data = load_data()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Date', 'Description', 'Progress', 'Notes'])
    
    if data.get('hackathons'):
        for h in data['hackathons']:
            notes_str = '; '.join([f"{n['progress']}%: {n['note']}" for n in h.get('notes', [])])
            writer.writerow([
                h.get('name', ''),
                h.get('date', '') or '',
                h.get('description', '') or '',
                f"{h.get('progress', 0)}%",
                notes_str
            ])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=hackathons.csv'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)