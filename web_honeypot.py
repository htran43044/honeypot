import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import time
import os

# Logging format
logging_format = logging.Formatter('%(message)s')

# HTTP Logger
funnel_logger = logging.getLogger('HTTPLogger')
funnel_logger.setLevel(logging.INFO)

# Đảm bảo file JSON luôn là mảng hợp lệ
JSON_FILE = 'http_audits.json'

def append_to_json(entry):
    try:
        # Đọc dữ liệu hiện tại từ file (nếu file rỗng, tạo mảng rỗng)
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                data = json.load(f) if os.path.getsize(JSON_FILE) > 0 else []
        else:
            data = []
        
        # Thêm bản ghi mới
        if not isinstance(data, list):
            data = []
        data.append(entry)
        
        # Ghi lại file với định dạng đẹp
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except json.JSONDecodeError:
        # Nếu file hỏng, khởi tạo lại mảng rỗng và thêm bản ghi
        with open(JSON_FILE, 'w') as f:
            json.dump([entry], f, indent=4)
    except IOError as e:
        print(f"Error writing to JSON: {e}")

def web_honeypot(input_username="admin@123", input_password="password"):
    app = Flask(__name__, template_folder='templates')

    # Đảm bảo thư mục uploads tồn tại
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/admin')
    def admin():
        ip_address = request.remote_addr
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "admin_access"}
        append_to_json(log_entry)
        return render_template('admin.html')

    @app.route('/admin_dashboard', methods=['POST'])
    def login():
        username = request.form['username']
        password = request.form['password']
        ip_address = request.remote_addr
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "login", "username": username, "password": password}
        append_to_json(log_entry)
        if username == input_username and password == input_password:
            return redirect(url_for('admin'))  
        return redirect(url_for('index'))

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        ip_address = request.remote_addr
        if request.method == 'POST':
            file = request.files.get('file')
            if file:
                log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload", "filename": file.filename}
                append_to_json(log_entry)
                file.save(os.path.join('uploads', file.filename))
                return jsonify({'status': 'success', 'message': 'File uploaded successfully!'})
            else:
                log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload_access", "error": "No file uploaded"}
                append_to_json(log_entry)
                return jsonify({'status': 'error', 'message': 'No file uploaded!'})
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload_access"}
        append_to_json(log_entry)
        return render_template('upload.html')

    @app.route('/register')
    def register():
        return render_template('register.html')

    @app.route('/register_user', methods=['POST'])
    def register_user():
        if request.method == 'POST':
            print("Received POST request on /register_user")
            fullname = request.form.get('fullname')
            password = request.form.get('password')
            email = request.form.get('email')
            ip_address = request.remote_addr
            if not fullname or not password or not email:
                print("Missing form data!")
                return "Missing form data!", 400
            log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "register", "fullname": fullname, "password": password, "email": email}
            append_to_json(log_entry)
            return "Registration Successful"
        return "Method not allowed", 405

    return app

def run_web_honeypot(port=5000, input_username="admin@123", input_password="password"):
    run_web_honeypot_app = web_honeypot(input_username, input_password)
    run_web_honeypot_app.run(debug=True, port=port, host="0.0.0.0")

if __name__ == "__main__":
    run_web_honeypot(port=5000, input_username="admin@123", input_password="password")