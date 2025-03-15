FROM python:3.9-slim

# Tạo thư mục /app và copy file cần thiết
WORKDIR /app

# Cài đặt thư viện
COPY ./uploads/requirements.txt /app/
COPY ./ssh_honeypot.py /app/
COPY ./web_honeypot.py /app/
COPY ./honeypy.py /app/
COPY ./templates /app/templates
COPY ./static /app/static
COPY ./server.key /app/server.key


RUN pip install --no-cache-dir -r /app/requirements.txt

# Mở cổng tuỳ theo honeypot SSH, web, ...
EXPOSE 22  
EXPOSE 5000 

# Lệnh chạy
CMD ["python", "ssh_honeypot.py"]

