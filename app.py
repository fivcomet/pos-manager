from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key_here" 
DB_NAME = "pospro_data.db"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT, biz_no TEXT, owner_name TEXT, 
        phone TEXT, biz_address TEXT, full_data TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return jsonify({"status": "success"})
        return jsonify({"status": "fail", "message": "아이디 또는 비밀번호가 틀렸습니다."})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register')
@login_required
def register():
    return render_template('register.html')

@app.route('/history')
@login_required
def history_page():
    return render_template('history.html')

@app.route('/api/merchant/<int:id>', methods=['GET'])
@login_required
def get_merchant(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT full_data FROM merchants WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify(json.loads(row[0]))
    return jsonify({"error": "Not found"}), 404

# ✅ 경로 추가 시 복수 주소 선택을 위해 additional_addresses 전달
@app.route('/api/search', methods=['GET'])
@login_required
def search():
    keyword = f"%{request.args.get('keyword', '')}%"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, store_name, biz_no, owner_name, phone, biz_address, full_data FROM merchants WHERE store_name LIKE ? OR biz_no LIKE ? OR owner_name LIKE ?", (keyword, keyword, keyword))
    res = []
    for r in c.fetchall():
        data = json.loads(r[6]) if r[6] else {}
        owner_phone = data.get('owner_phone', '')
        store_phone = data.get('store_phone', '')
        extra_contacts = data.get('extra_contacts', [])
        display_phone = owner_phone or (f"[{extra_contacts[0].get('role', '담당자')}] {extra_contacts[0].get('phone')}" if extra_contacts else "") or f"[매장] {store_phone}"
        
        latest_date = "0000-00-00"
        histories = data.get('histories', [])
        if histories:
            valid_dates = [h.get('date', '0000-00-00') for h in histories if h.get('date')]
            if valid_dates: latest_date = max(valid_dates)

        res.append({
            "id": r[0], "store_name": r[1], "biz_no": r[2], "owner_name": r[3], 
            "phone": display_phone, "address": r[5],
            "additional_addresses": json.dumps(data.get('additional_addresses', []), ensure_ascii=False),
            "latest_date": latest_date
        })
    conn.close()
    res.sort(key=lambda x: x['latest_date'], reverse=True)
    return jsonify(res)

@app.route('/api/find_by_phone', methods=['GET'])
@login_required
def find_by_phone():
    target_phone = request.args.get('phone', '').replace('-', '')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, store_name, full_data FROM merchants")
    matches = []
    for r in c.fetchall():
        data = json.loads(r[2]) if r[2] else {}
        if target_phone == data.get('owner_phone', '').replace('-', ''): matches.append({"id": r[0], "store_name": r[1], "role": "대표자"})
        if target_phone == data.get('store_phone', '').replace('-', ''): matches.append({"id": r[0], "store_name": r[1], "role": "매장"})
        for ext in data.get('extra_contacts', []):
            if target_phone == ext.get('phone', '').replace('-', ''): matches.append({"id": r[0], "store_name": r[1], "role": ext.get('role', '관계자')})
    conn.close()
    return jsonify({"matches": matches})

@app.route('/api/pending_tasks', methods=['GET'])
@login_required
def pending_tasks():
    worker_name = request.args.get('worker', '오혜성')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, store_name, full_data FROM merchants")
    rows = c.fetchall()
    conn.close()

    my_tasks = []
    unassigned_tasks = []
    for r in rows:
        data = json.loads(r[2])
        for idx, h in enumerate(data.get('histories', [])):
            if h.get('status') == '예정':
                cat = h.get("category_other") if h.get("category") == '기타' else h.get("category")
                task_obj = {
                    "merchant_id": r[0], "store_name": r[1], "date": h.get("date", ""),
                    "category": cat, "content": h.get("content", ""), "worker": h.get("worker", ""),
                    "history_idx": idx 
                }
                if not h.get("worker") or h.get("worker") == '미지정': unassigned_tasks.append(task_obj)
                elif h.get("worker") == worker_name: my_tasks.append(task_obj)
                    
    my_tasks.sort(key=lambda x: x['date'] if x['date'] else '9999-99-99')
    unassigned_tasks.sort(key=lambda x: x['date'] if x['date'] else '9999-99-99')
    return jsonify({"my_tasks": my_tasks, "unassigned_tasks": unassigned_tasks})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "파일이 없습니다."}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "선택된 파일이 없습니다."}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"url": "/" + filepath})

@app.route('/api/save', methods=['POST'])
@login_required
def save_merchant():
    data = request.json
    merchant_id = data.get('id')
    full_data_json = json.dumps(data, ensure_ascii=False)
    base_phone = data.get('owner_phone') or data.get('store_phone', '')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if merchant_id:
        c.execute("UPDATE merchants SET store_name=?, biz_no=?, owner_name=?, phone=?, biz_address=?, full_data=? WHERE id=?", 
                  (data.get('store_name'), data.get('biz_no'), data.get('owner_name'), base_phone, data.get('biz_address'), full_data_json, merchant_id))
        r_id = merchant_id
    else:
        c.execute("INSERT INTO merchants (store_name, biz_no, owner_name, phone, biz_address, full_data) VALUES (?, ?, ?, ?, ?, ?)", 
                  (data.get('store_name'), data.get('biz_no'), data.get('owner_name'), base_phone, data.get('biz_address'), full_data_json))
        r_id = c.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "id": r_id})

@app.route('/api/all_history', methods=['GET'])
@login_required
def all_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, store_name, full_data FROM merchants")
    rows = c.fetchall()
    conn.close()
    history_list = []
    for r in rows:
        data = json.loads(r[2])
        for idx, h in enumerate(data.get('histories', [])):
            combined_content = h.get("auto_content", "")
            if combined_content and h.get("content", ""): combined_content += "\n---\n" + h.get("content", "")
            elif not combined_content: combined_content = h.get("content", "")
            
            cat = h.get("category_other") if h.get("category") == '기타' else h.get("category")
            history_list.append({
                "merchant_id": r[0], "store_name": r[1], "date": h.get("date", ""), 
                "worker": h.get("worker", ""), "category": cat, "content": combined_content, 
                "img_urls": h.get("img_urls", []), "status": h.get("status", "완료"), "history_idx": idx
            })
    history_list.sort(key=lambda x: x['date'], reverse=True)
    return jsonify(history_list)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True, port=5000)