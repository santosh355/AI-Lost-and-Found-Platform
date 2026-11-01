import os
import sqlite3
import uuid
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def load_datasets():
    try:
        ds1 = pd.read_excel('datasets/DLdataset1.xlsx')
        ds2 = pd.read_csv('datasets/DLdataset2.csv')
        ds3 = pd.read_excel('datasets/DLdataset3.xlsx')
        print("Datasets loaded successfully into backend memory!")
    except Exception as e:
        print("Dataset loading note:", e)

load_datasets()

def init_db():
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            full_name TEXT,
            role TEXT,
            student_id TEXT,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT,
            item_name TEXT,
            item_category TEXT,
            colour TEXT,
            brand TEXT,
            description TEXT,
            location TEXT,
            reporter_email TEXT,
            reporter_role TEXT,
            user_token TEXT,
            image_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_token TEXT,
            receiver_token TEXT,
            sender_email TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    full_name = data.get('full_name')
    role = data.get('role')
    student_id = data.get('student_id', 'Faculty_Staff')
    password = data.get('password')

    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?)', (email, full_name, role, student_id, password))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, role, student_id, email FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'success': True,
            'user': {
                'full_name': user[0],
                'role': user[1],
                'student_id': user[2],
                'email': user[3]
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')

    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'Email not registered in the system.'}), 404

    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Password reset successful!'})

@app.route('/api/report-item', methods=['POST'])
def report_item():
    report_type = request.form.get('report_type')
    item_name = request.form.get('item_name')
    item_category = request.form.get('item_category')
    colour = request.form.get('colour', '')
    brand = request.form.get('brand', '')
    description = request.form.get('description', '')
    location = request.form.get('location')
    reporter_email = request.form.get('reporter_email')
    reporter_role = request.form.get('reporter_role')

    user_token = f"Token_{uuid.uuid4().hex[:4].upper()}"

    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f"http://127.0.0.1:5000/static/uploads/{filename}"

    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (report_type, item_name, item_category, colour, brand, description, location, reporter_email, reporter_role, user_token, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (report_type, item_name, item_category, colour, brand, description, location, reporter_email, reporter_role, user_token, image_url))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'user_token': user_token})

@app.route('/api/reports', methods=['GET'])
def get_reports():
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT report_type, item_name, item_category, colour, brand, description, location, user_token, image_url, reporter_email FROM reports ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for r in rows:
        reports.append({
            'report_type': r[0],
            'item_name': r[1],
            'item_category': r[2],
            'colour': r[3],
            'brand': r[4],
            'description': r[5],
            'location': r[6],
            'user_token': r[7],
            'image_url': r[8],
            'reporter_email': r[9]
        })
    return jsonify(reports)

@app.route('/api/reports/<string:user_token>', methods=['DELETE'])
def delete_report(user_token):
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT reporter_email FROM reports WHERE user_token = ?', (user_token,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Report not found.'}), 404
        
    cursor.execute('DELETE FROM reports WHERE user_token = ?', (user_token,))
    cursor.execute('DELETE FROM chat_messages WHERE sender_token = ? OR receiver_token = ?', (user_token, user_token))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Report and related chats cleared successfully!'})

@app.route('/api/match-candidates', methods=['GET'])
def match_candidates():
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_name, item_category, colour, brand, description, location, user_token FROM reports WHERE report_type = "lost"')
    lost_items = cursor.fetchall()
    cursor.execute('SELECT item_name, item_category, colour, brand, description, location, user_token FROM reports WHERE report_type = "found"')
    found_items = cursor.fetchall()
    conn.close()

    matches = []
    for l in lost_items:
        for f in found_items:
            l_name, l_cat, l_col, l_brand, l_desc, l_loc, l_token = l
            f_name, f_cat, f_col, f_brand, f_desc, f_loc, f_token = f

            if l_cat.strip().lower() != f_cat.strip().lower():
                continue

            l_text = f"{l_name} {l_cat} {l_col or ''} {l_brand or ''} {l_desc or ''} {l_loc}"
            f_text = f"{f_name} {f_cat} {f_col or ''} {f_brand or ''} {f_desc or ''} {f_loc}"

            vectorizer = TfidfVectorizer().fit_transform([l_text, f_text])
            vectors = vectorizer.toarray()
            similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
            
            score = int(similarity * 100)

            if score >= 35:  
                matches.append({
                    'lost_item': l_name,
                    'found_item': f_name,
                    'category': l_cat,
                    'lost_token': l_token,
                    'found_token': f_token,
                    'score': score
                })

    matches = sorted(matches, key=lambda x: x['score'], reverse=True)
    return jsonify(matches)

@app.route('/api/chat/request', methods=['POST'])
def chat_request():
    return jsonify({'success': True})

@app.route('/api/chat/messages', methods=['GET', 'POST'])
def handle_chat_messages():
    conn = sqlite3.connect('portal.db')
    cursor = conn.cursor()

    if request.method == 'GET':
        token1 = request.args.get('token1', '').strip()
        token2 = request.args.get('token2', '').strip()
        user_email = request.args.get('user_email', '').strip().lower()

        cursor.execute('''
            SELECT reporter_email FROM reports WHERE user_token IN (?, ?)
        ''', (token1, token2))
        authorized_emails = [r[0].strip().lower() for r in cursor.fetchall() if r[0]]

        if user_email and authorized_emails and user_email not in authorized_emails:
            conn.close()
            return jsonify({'authorized': False, 'messages': []})

        cursor.execute('''
            SELECT sender_token, receiver_token, sender_email, text, timestamp 
            FROM chat_messages 
            WHERE (sender_token = ? AND receiver_token = ?) OR (sender_token = ? AND receiver_token = ?)
            ORDER BY timestamp ASC
        ''', (token1, token2, token2, token1))
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for r in rows:
            messages.append({
                'sender_token': r[0],
                'receiver_token': r[1],
                'sender_email': r[2] or '',
                'text': r[3],
                'timestamp': r[4]
            })
        return jsonify({'authorized': True, 'messages': messages})

    elif request.method == 'POST':
        data = request.json
        token1 = (data.get('token1') or data.get('finder_token') or '').strip()
        token2 = (data.get('token2') or data.get('owner_token') or '').strip()
        sender_email = data.get('sender_email', '').strip().lower()
        text = data.get('text', '').strip()

        if not text or not sender_email or not token1 or not token2:
            conn.close()
            return jsonify({'success': False, 'message': 'Missing data'}), 400

        cursor.execute('SELECT user_token FROM reports WHERE user_token IN (?, ?)', (token1, token2))
        valid_rows = cursor.fetchall()
        if len(valid_rows) < 2:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid chat tokens'}), 400

        sender_token = token1
        receiver_token = token2

        cursor.execute('''
            INSERT INTO chat_messages (sender_token, receiver_token, sender_email, text)
            VALUES (?, ?, ?, ?)
        ''', (sender_token, receiver_token, sender_email, text))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)