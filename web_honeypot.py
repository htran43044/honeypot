import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for
import json
import time

# Logging format
logging_format = logging.Formatter('%(message)s')

# HTTP Logger
funnel_logger = logging.getLogger('HTTPLogger')
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler('http_audits.json', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

def web_honeypot(input_username="admin", input_password="password"):
    app = Flask(__name__, template_folder='templates')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/admin_dashboard', methods=['POST'])
    def login():
        username = request.form['username']
        password = request.form['password']
        ip_address = request.remote_addr
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "login", "username": username, "password": password}
        funnel_logger.info(json.dumps(log_entry))
        if username == input_username and password == input_password:
            return redirect(url_for('admin'))  
        elif "'" in username or "'" in password:  # Giả lập SQL Injection
            return "SQL Error: Invalid query near ' OR 1=1 --"
        else:
            return "Invalid credentials. Try again."

    @app.route('/admin')
    def admin():
        ip_address = request.remote_addr
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "admin_access"}
        funnel_logger.info(json.dumps(log_entry))
        return render_template('admin.html')

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        ip_address = request.remote_addr
        if request.method == 'POST':
            file = request.files.get('file')
            if file:
                log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload", "filename": file.filename}
                funnel_logger.info(json.dumps(log_entry))
                return "File uploaded successfully!"
            else:
                log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload_access", "error": "No file uploaded"}
                funnel_logger.info(json.dumps(log_entry))
        log_entry = {"timestamp": time.ctime(), "ip": ip_address, "type": "upload_access"}
        funnel_logger.info(json.dumps(log_entry))
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
            funnel_logger.info(json.dumps(log_entry))
            return "Registration Successful"
        return "Method not allowed", 405

    return app

def run_web_honeypot(port=5000, input_username="admin", input_password="password"):
    run_web_honeypot_app = web_honeypot(input_username, input_password)
    run_web_honeypot_app.run(debug=True, port=port, host="0.0.0.0")

if __name__ == "__main__":
    run_web_honeypot(port=5000, input_username="admin", input_password="password")