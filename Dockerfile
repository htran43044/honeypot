# Dockerfile

FROM python:3.9-slim

# Tạo thư mục /app và copy file cần thiết
WORKDIR /app

# Cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào /app
COPY . .

# Mở cổng tuỳ theo honeypot SSH, web, ...
EXPOSE 22  
EXPOSE 5000 

# Lệnh chạy
CMD ["python", "ssh_honeypot.py"]

