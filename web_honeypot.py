import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

from datetime import datetime
import pytz

def get_vietnam_time():
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    return datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")

# Logging setup
LOG_FILE = os.getenv("LOG_FILE", "logs/http_audits.json") 

def append_to_json(entry):
    try:
        data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

        if not isinstance(data, list):
            data = []

        data.append(entry)

        with open(LOG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error writing to JSON: {e}")

database = [
    {
        "input_username": "admin123@gmail.com",
        "input_password": "admin@123"
    },
    {
        "input_username": "admin123@gmail.com",
        "input_password": "password"
    }
]

def web_honeypot(database):
    app = Flask(__name__, template_folder='templates')

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/admin')
    def admin():
        ip_address = request.remote_addr
        log_entry = {
            "timestamp": get_vietnam_time(),
            "ip": ip_address,
            "type": "admin_access"
        }
        print(log_entry)
        append_to_json(log_entry)
        return render_template('admin.html')

    @app.route('/admin_dashboard', methods=['POST'])
    def login():
        username = request.form['username']
        password = request.form['password']
        ip_address = request.remote_addr
        log_entry = {
            "timestamp": get_vietnam_time(),
            "ip": ip_address,
            "type": "login",
            "username": username,
            "password": password
        }
        append_to_json(log_entry)
        for user in database:
            if username == user['input_username'] and password == user['input_password']:
                return redirect(url_for('admin'))
        return redirect(url_for('index'))

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        ip_address = request.remote_addr
        if request.method == 'POST':
            file = request.files.get('file')
            if file:
                log_entry = {
                    "timestamp": get_vietnam_time(),
                    "ip": ip_address,
                    "type": "upload",
                    "filename": file.filename
                }
                append_to_json(log_entry)
                file.save(os.path.join('uploads', file.filename))
                return jsonify({'status': 'success', 'message': 'File uploaded successfully!'})
            else:
                log_entry = {
                    "timestamp": get_vietnam_time(),
                    "ip": ip_address,
                    "type": "upload_access",
                    "error": "No file uploaded"
                }
                append_to_json(log_entry)
                return jsonify({'status': 'error', 'message': 'No file uploaded!'})
        log_entry = {
            "timestamp": get_vietnam_time(),
            "ip": ip_address,
            "type": "upload_access"
        }
        append_to_json(log_entry)
        return render_template('upload.html')

    @app.route('/register')
    def register():
        return render_template('register.html')

    @app.route('/register_user', methods=['POST'])
    def register_user():
        if request.method == 'POST':
            fullname = request.form.get('fullname')
            password = request.form.get('password')
            email = request.form.get('email')
            ip_address = request.remote_addr

            if not fullname or not password or not email:
                return "Missing form data!", 400
            log_entry = {
                "timestamp": get_vietnam_time(),
                "ip": ip_address,
                "type": "register",
                "fullname": fullname,
                "password": password,
                "email": email
            }
            append_to_json(log_entry)
            return "Registration Successful"
        return "Method not allowed", 405

    return app

def run_web_honeypot(port=5000):
    run_web_honeypot_app = web_honeypot(database)
    run_web_honeypot_app.run(debug=False, port=port, host="0.0.0.0")

if __name__ == "__main__":
    run_web_honeypot(port=5000)