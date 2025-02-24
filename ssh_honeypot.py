# Libraries
import logging
from logging.handlers import RotatingFileHandler
import socket
import paramiko
import threading
import time
import json

# Constants
logging_format = logging.Formatter('%(message)s')
SSH_BANNER = "SSH-2.0-MySSHServer_1.0"

host_key = paramiko.RSAKey(filename='server.key', password='password') # private file key pair

# Loggers & Logging files
funnel_logger = logging.getLogger('FunnelLogger') # Capture the username & password, IP addr
funnel_logger.setLevel(logging.INFO) # Provide the info logger
funnel_handler = RotatingFileHandler('cmd_audits.json', maxBytes = 2000, backupCount = 5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

# Capture the emulated shell what commands the bots,.. a hackers are using
creds_logger = logging.getLogger('CredsLogger') # Capture the username & password, IP addr
creds_logger.setLevel(logging.INFO) # Provide the info logger
creds_handler = RotatingFileHandler('creds_audits.json', maxBytes = 2000, backupCount = 5)
creds_handler.setFormatter(logging_format)
creds_logger.addHandler(creds_handler)

# Emulated Shell
def emulated_shell(channel, client_ip):
    channel.send(b'corporate-jumpbox2$ ') # send default prompt when we're not in emulated shell environment
    command = b"" # listening to (input) receive those commands followed by binary
    while True:
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()
        
        command += char # make all of those character variables into a string

        if char == b"\r":
            cmd_str = command.strip().decode()
            log_entry = {"timestamp": time.ctime(), "ip": client_ip, "command": cmd_str}
            if command.strip() == b'exit':
                response = b'\n Goodbye!\n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b"\n" + b'\\usr\\local' + b'\r\n'
                creds_logger.info(f'Command {command.strip()}' + 'executed by ' + f'{client_ip}')
            elif command.strip() == b'whoami':
                response = b"\n" + b"corpuser1" + b"\r\n"
                creds_logger.info(f'Command {command.strip()}' + 'executed by ' + f'{client_ip}')
            elif command.strip() == b'ls':
                response = b'\n' + b"jumpbox1.conf" + b"\r\n"
                creds_logger.info(f'Command {command.strip()}' + 'executed by ' + f'{client_ip}')
            elif command.strip() == b'cat jumpbox1.conf':
                response = b'\n' + b"Go to boodah.com." + b"\r\n"
                creds_logger.info(f'Command {command.strip()}' + 'executed by ' + f'{client_ip}')
            else:
                response = b"\n" + bytes(command.strip()) + b"\r\n"
            creds_logger.info(json.dumps(log_entry))

            channel.send(response)
            channel.send(b'corporate-jumpbox2$ ')
            command = b''      

# SSH Server + Sockets
# set up SSH connections
class Server(paramiko.ServerInterface):
    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    # channel type
    def check_channel_request(self, kind: str, chanid: id) -> int:
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
    
    # basic authentication => username & password
    def get_allowed_auths(self, username):
        return "password"
    
    # check pass
    def check_auth_password(self, username, password):
        log_entry = {"timestamp": time.ctime(), "ip": self.client_ip, "username": username, "password": password}
        funnel_logger.info(json.dumps(log_entry))
        creds_logger.info(json.dumps(log_entry))
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED
        else:
            return paramiko.AUTH_SUCCESSFUL

    # check channel        
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True         

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    
    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True
    
# client handle    
def client_handle(client, addr, username, password):
    client_ip = addr[0]
    print(f"{client_ip} has connected to the server.")
    
    try:
        # low level SSH session
        transport = paramiko.Transport(client) # use the client socket
        transport.local_version = SSH_BANNER
        server = Server(client_ip=client_ip, input_username=username, input_password=password)

        # Load host key
        transport.add_server_key(host_key) # provide a host key = pubKey + priKey allows connections/ clients to verify

        transport.start_server(server=server)

        # Open channel
        channel = transport.accept(100) # provide 100ms for the client to request the channel
        if channel is None:
            print("No channel was opened.")
            return
        
        standard_banner = "Welcome to Ubuntu 22.04 LTS (Jammy Jellyfish)!\r\n\r\n"
        channel.send(standard_banner)
        emulated_shell(channel, client_ip=client_ip)
    
    except Exception as error:
        print(f'Error: {error}')
  
    finally:
        try:
            transport.close()
        except:
            print(f'Error: {error}')
        client.close()

# Provision SSH-based Honeypot
def honeypot(address, port, username, password):

    # set up a socket
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listening using the TCP port => connection port
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse address even if it's come in before
    socks.bind((address, port))

    # connection handle
    socks.listen(100) # 100 conn can come in and socket can handle => if it's above => have to wait/ refused
    print(f"SSH server is listening on port {port}.")

    while True:
        try:
            client, addr = socks.accept() 
            ssh_honeypot_thread = threading.Thread(target=client_handle, args=(client, addr, username, password)) # new thread
            ssh_honeypot_thread.start()
        except Exception as error:
            print(error)

honeypot('127.0.0.1', 2223, 'username', 'password')