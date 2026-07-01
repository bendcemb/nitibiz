from flask import Flask, render_template
import pyodbc
import os

app = Flask(__name__)

# กำหนดค่าการเชื่อมต่อ SQL Server
SERVER = r'10.11.0.4\SQLEXPRESS'
DATABASE = 'sbp-dailyreport'
USERNAME = 'bendcemb'
PASSWORD = 'Ben28122523!'

def get_db_connection():
    # Connection String สำหรับ SQL Server Authentication
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
    )
    conn = pyodbc.connect(connection_string)
    return conn

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT TOP (1000) [company_id]
              ,[genre]
              ,[company]
          FROM [sbp-dailyreport].[dbo].[master_company]
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        company_data = []
        for row in rows:
            company_data.append({
                "company_id": getattr(row, 'company_id', ''),
                "genre": getattr(row, 'genre', ''),
                "company": getattr(row, 'company', '')
            })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Database error: {error_msg}")
        company_data = []
        return render_template('index.html', company_data=company_data, error=error_msg)

    return render_template('index.html', company_data=company_data)

if __name__ == '__main__':
    # กำหนด host='0.0.0.0' เพื่อให้สามารถเข้าถึงจากภายนอก Container ได้
    app.run(host='0.0.0.0', port=5000, debug=True)
