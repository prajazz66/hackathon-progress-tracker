from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'hackathon-tracker-secret-key'

DATA_FILE = 'hackathons.json'

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
            # Add full thumbnail URL
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
            'notes': []
        }
        data['hackathons'].append(hackathon)
        save_data(data)
    return redirect(url_for('index'))

@app.route('/delete_hackathon/<int:hackathon_id>', methods=['POST'])
def delete_hackathon(hackathon_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    
    data = load_data()
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