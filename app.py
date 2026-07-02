from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# กำหนดค่าการเชื่อมต่อ PostgreSQL จาก Environment Variables
HOST = os.environ.get('POSTGRES_HOST', 'localhost')
PORT = os.environ.get('POSTGRES_PORT', '5432')
DATABASE = os.environ.get('POSTGRES_DB', 'sbp-dailyreport')
USERNAME = os.environ.get('POSTGRES_USER', 'bendcemb')
PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'Ben28122523!')

def get_db_connection():
    # Connection String สำหรับ PostgreSQL
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname=DATABASE,
        user=USERNAME,
        password=PASSWORD
    )
    return conn

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        # ใช้ DictCursor เพื่อให้สามารถเข้าถึงข้อมูลผ่านชื่อคอลัมน์ได้
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        query = """
        SELECT company_id
              ,genre
              ,company
          FROM master_company
          LIMIT 1000
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        company_data = []
        for row in rows:
            company_data.append({
                "company_id": row.get('company_id', ''),
                "genre": row.get('genre', ''),
                "company": row.get('company', '')
            })
        
    except Exception as e:
        error_msg = str(e)
        print(f"Database error: {error_msg}")
        company_data = []
        return render_template('index.html', company_data=company_data, error=error_msg)

    return render_template('index.html', company_data=company_data)


@app.route('/company')
def company():
    try:
        conn = get_db_connection()
        # ใช้ DictCursor เพื่อให้สามารถเข้าถึงข้อมูลผ่านชื่อคอลัมน์ได้
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Query สำหรับ master_company
        cursor.execute("""
            SELECT company_id, genre, company, name_eng
            FROM master_company
            ORDER BY company_id ASC
            -- LIMIT 1000
        """)
        master_companies = cursor.fetchall()

        # Query สำหรับ sbp_company
        cursor.execute("""
            SELECT company_id, "Company" AS company, new_company_id
            FROM sbp_company
            ORDER BY company_id
            -- LIMIT 1000
        """)
        sbp_companies = cursor.fetchall()

        conn.close()

        # แปลงข้อมูลเป็น list of dictionaries
        master_data = []
        for row in master_companies:
            master_data.append({
                "company_id": row.get('company_id', ''),
                "genre": row.get('genre', ''),
                "company": row.get('company', ''),
                "name_eng": row.get('name_eng', '')
            })

        sbp_data = []
        for row in sbp_companies:
            sbp_data.append({
                "company_id": row.get('company_id', ''),
                "new_company_id": row.get('new_company_id', ''),
                "company": row.get('company', '')
            })

    except Exception as e:
        error_msg = str(e)
        print(f"Database error: {error_msg}")
        master_data = []
        sbp_data = []
        return render_template('company.html', master_data=master_data, sbp_data=sbp_data, error=error_msg)

    return render_template('company.html', master_data=master_data, sbp_data=sbp_data)


@app.route('/api/update_sbp_company', methods=['POST'])
def update_sbp_company():
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        new_company_id = data.get('new_company_id')

        if not company_id:
            return jsonify({'success': False, 'error': 'Missing company_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the sbp_company table
        # If new_company_id is empty, we set it to NULL
        if new_company_id and new_company_id.strip():
            cursor.execute("""
                UPDATE sbp_company 
                SET new_company_id = %s 
                WHERE company_id = %s
            """, (new_company_id.strip(), company_id))
        else:
            cursor.execute("""
                UPDATE sbp_company 
                SET new_company_id = NULL 
                WHERE company_id = %s
            """, (company_id,))

        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'company_id': company_id, 'new_company_id': new_company_id})
    except Exception as e:
        print(f"Update error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bulk_update_sbp_company', methods=['POST'])
def bulk_update_sbp_company():
    try:
        data = request.get_json()
        company_ids = data.get('company_ids', [])
        new_company_id = data.get('new_company_id')

        if not company_ids or not isinstance(company_ids, list):
            return jsonify({'success': False, 'error': 'Missing or invalid company_ids list'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if new_company_id and str(new_company_id).strip():
            cursor.execute("""
                UPDATE sbp_company 
                SET new_company_id = %s 
                WHERE company_id::text = ANY(%s)
            """, (str(new_company_id).strip(), company_ids))
        else:
            cursor.execute("""
                UPDATE sbp_company 
                SET new_company_id = NULL 
                WHERE company_id::text = ANY(%s)
            """, (company_ids,))

        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'updated_count': len(company_ids), 'new_company_id': new_company_id})
    except Exception as e:
        print(f"Bulk update error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/master_company/add', methods=['POST'])
def add_master_company():
    try:
        data = request.get_json()
        genre = data.get('genre')
        company = data.get('company')
        name_eng = data.get('name_eng')
        if not company:
            return jsonify({'success': False, 'error': 'company name is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(company_id) FROM master_company")
        max_id = cursor.fetchone()[0]
        new_company_id = max_id + 1 if max_id is not None else 1

        cursor.execute("""
            INSERT INTO master_company (company_id, genre, company, name_eng)
            VALUES (%s, %s, %s, %s)
        """, (new_company_id, genre, company, name_eng))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/master_company/edit', methods=['PUT'])
def edit_master_company():
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        genre = data.get('genre')
        company = data.get('company')
        name_eng = data.get('name_eng')
        if not company_id or not company:
            return jsonify({'success': False, 'error': 'company_id and company are required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE master_company
            SET genre = %s, company = %s, name_eng = %s
            WHERE company_id = %s
        """, (genre, company, name_eng, company_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/master_company/delete', methods=['DELETE'])
def delete_master_company():
    try:
        data = request.get_json()
        company_id = data.get('company_id')
        if not company_id:
            return jsonify({'success': False, 'error': 'company_id is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM master_company
            WHERE company_id = %s
        """, (company_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # กำหนด host='0.0.0.0' เพื่อให้สามารถเข้าถึงจากภายนอก Container ได้
    app.run(host='0.0.0.0', port=5000, debug=True)
