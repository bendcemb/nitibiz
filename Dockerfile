# ใช้ Python 3.11 บน Debian 11 (Bullseye)
FROM python:3.11-slim-bullseye

# ติดตั้ง System Dependencies สำหรับ pyodbc และ Microsoft ODBC Driver 17 for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    gnupg2 \
    unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# ตั้งค่า Working Directory ภายใน Container
WORKDIR /app

# คัดลอก requirements.txt และติดตั้ง Python Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์ทั้งหมดในโปรเจกต์เข้าไปใน Container
COPY . .

# เปิดพอร์ต 5000 เพื่อให้ภายนอกเข้าถึง Flask
EXPOSE 5000

# รันคำสั่งนี้เมื่อ Container เริ่มต้น
CMD ["python", "app.py"]
