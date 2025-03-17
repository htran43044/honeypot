# Cài đặt các thư viện cần thiết ở trong file requirements.txt với:
pip install -r requirements.txt 

# Tạo server key:
ssh-keygen -t rsa -b 2048 -f server.key
# => Tự động tạo ra 2 file: server.key (Secret key) và server.key.pub (Public key). 2 file này dùng để login vào hệ thống ssh

# Có thể chạy 1 trong 2 file để kiểm thử ghi log với ssh hoặc http
python3 ssh_honeypot.py
python3 web_honeypot.py

# Với ssh, sau khi đã chạy file trên thì dùng WSL của Ubuntu để đăng nhập vào hệ thống giả lập:
ssh -p 2223 username@127.0.0.1
# => Sau đó sẽ hiển thị "username@127.0.0.1's password:", lúc này cần nhập password đã cho là ở trong file ssh_honeypot.py. Sau đó ta sẽ thấy banner cùng với user giả lập Ubuntu
# => Ta có thể nhập các lệnh trong Ubuntu để xem kết quả trả về, cùng lúc đó ta sẽ thấy folder logs sẽ hiện ra 2 file cmd_audits.json (ghi nhận các lệnh đã sử dụng) và creds_audits.json (ghi nhận các thao tác của hacker)

# Với http, sau khi đã chạy file trên thì sẽ hiện ra "Running on http://127.0.0.1:5000" hoặc pop up thông báo dùng trình duyệt truy cập với port 5000. Thì ta chọn vào cái nào cũng được, vì đều cần trình duyệt để hiển thị
# Sau đó sẽ hiện ra trang login, thì ta nhập username và password tương ứng đã cung cấp ở trong file web_honeypot.py
# => Sau đó sẽ hiện ra trang dashboard của admin. Và mọi thao tác đều sẽ được ghi trong file http_audits.json ở folder logs

