import logging
import socket
import paramiko
import threading
import time
import json
import os

# Constants
SSH_BANNER = "SSH-2.0-MySSHServer_1.0"
LOG_DIR = "logs"
CREDS_LOG_FILE = os.path.join(LOG_DIR, "creds_audits.json")  # Đổi sang JSON
CMD_LOG_FILE = os.path.join(LOG_DIR, "cmd_audits.json")

os.makedirs(LOG_DIR, exist_ok=True)

host_key = paramiko.RSAKey(filename='server.key')  # Private key file

def log_to_json(file_path, data):
    # Nếu file chưa tồn tại, tạo mới danh sách
    if not os.path.exists(file_path):
        logs = []
    else:
        try:
            with open(file_path, "r") as f:
                logs = json.load(f) 
        except json.JSONDecodeError:
            logs = []  

    logs.append(data)  

    with open(file_path, "w") as f:
        json.dump(logs, f, indent=4) 

def emulated_shell(channel, client_ip):
    channel.send(b'corporate-jumpbox2$ ')
    command = b""
    while True:
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()
            break
        
        command += char
        if char == b"\r":
            cmd_str = command.strip().decode()
            log_entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "ip": client_ip, "command": cmd_str}
            log_to_json(CMD_LOG_FILE, log_entry)  # Ghi vào JSON
            
            if command.strip() == b'exit':
                response = b'\n Goodbye!\n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b"\n" + b'\\usr\\local' + b'\r\n'
            elif command.strip() == b'whoami':
                response = b"\n" + b"corpuser1" + b"\r\n"
            elif command.strip() == b'ls':
                response = b'\n' + b"jumpbox1.conf" + b"\r\n"
            elif command.strip() == b'cat jumpbox1.conf':
                response = b'\n' + b"Go to boodah.com." + b"\r\n"
            else:
                response = b"\n" + bytes(command.strip()) + b"\r\n"
            
            channel.send(response)
            channel.send(b'corporate-jumpbox2$ ')
            command = b''

class Server(paramiko.ServerInterface):
    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
    
    def get_allowed_auths(self, username):
        return "password"
    
    def check_auth_password(self, username, password):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "ip": self.client_ip,
            "username": username,
            "password": password
        }
        log_to_json(CREDS_LOG_FILE, log_entry)  # Ghi vào JSON
        
        if self.input_username and self.input_password:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFUL
            return paramiko.AUTH_FAILED
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True         

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def client_handle(client, addr, username, password):
    client_ip = addr[0]
    print(f"{client_ip} has connected to the server.")
    try:
        transport = paramiko.Transport(client)
        transport.local_version = SSH_BANNER
        server = Server(client_ip=client_ip, input_username=username, input_password=password)
        transport.add_server_key(host_key)
        transport.start_server(server=server)
        channel = transport.accept(100)
        if channel is None:
            print("No channel was opened.")
            return
        standard_banner = "Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\r\n\r\n"
        channel.send(standard_banner)
        emulated_shell(channel, client_ip=client_ip)
    except Exception as error:
        print(f'Error: {error}')
    finally:
        transport.close()
        client.close()

def honeypot(address, port, username, password):
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))
    socks.listen(100)
    print(f"SSH server is listening on port {port}.")
    while True:
        try:
            client, addr = socks.accept()
            ssh_honeypot_thread = threading.Thread(target=client_handle, args=(client, addr, username, password))
            ssh_honeypot_thread.start()
        except Exception as error:
            print(error)

if __name__ == "__main__":
    honeypot('0.0.0.0', 2223, 'username', 'password')
