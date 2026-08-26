from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import config

app = Flask(__name__)


def get_db_connection():
    # Connection String สำหรับ PostgreSQL
    conn = psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
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

        # Query สำหรับ นับข้อมูล
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN new_company_id IS NULL THEN 1 END) AS not_match,
                COUNT(CASE WHEN new_company_id = 3370  THEN 1 END) AS unknow
            FROM public.sbp_company;
        """)
        count_results = cursor.fetchall()

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

        count_data = []
        for row in count_results:
            count_data.append({
                "not_match": row.get('not_match', ''),
                "unknow": row.get('unknow', '')
            })

    except Exception as e:
        error_msg = str(e)
        print(f"Database error: {error_msg}")
        master_data = []
        sbp_data = []
        count_data = []
        return render_template('company.html', master_data=master_data, sbp_data=sbp_data, count_data=count_data, error=error_msg)

    return render_template('company.html', master_data=master_data, sbp_data=sbp_data, count_data=count_data)


@app.route('/api/sbp_stats', methods=['GET'])
def get_sbp_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN new_company_id IS NULL THEN 1 END) AS not_match,
                COUNT(CASE WHEN new_company_id = 3370  THEN 1 END) AS unknow
            FROM public.sbp_company;
        """)
        row = cursor.fetchone()
        conn.close()
        return jsonify({
            'success': True,
            'not_match': row.get('not_match', 0),
            'unknow': row.get('unknow', 0)
        })
    except Exception as e:
        print(f"Stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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


@app.route('/dailyreport')
def dailyreport():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # ดึงรายงานทั้งหมด เรียงจากวันใหม่สุด
        cursor.execute("""
            SELECT id, report_date, title, description, status,
                   created_at, updated_at
            FROM daily_reports
            ORDER BY report_date DESC, id DESC
            LIMIT 500
        """)
        rows = cursor.fetchall()
        conn.close()

        reports = []
        for row in rows:
            reports.append({
                "id":          row.get('id'),
                "report_date": str(row.get('report_date', '')),
                "title":       row.get('title', ''),
                "description": row.get('description', ''),
                "status":      row.get('status', 'in_progress'),
                "created_at":  str(row.get('created_at', '')),
                "updated_at":  str(row.get('updated_at', '')),
            })

    except Exception as e:
        error_msg = str(e)
        print(f"Daily report DB error: {error_msg}")
        reports = []
        return render_template('dailyreport.html', reports=reports, error=error_msg)

    return render_template('dailyreport.html', reports=reports)


# ── Daily Report API ──────────────────────────────────────────────────────────

@app.route('/api/daily_reports', methods=['GET'])
def api_get_daily_reports():
    """ดึงรายงานทั้งหมด (รองรับ filter date)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        date_filter = request.args.get('date')
        if date_filter:
            cursor.execute("""
                SELECT id, report_date, title, description, status, created_at, updated_at
                FROM daily_reports
                WHERE report_date = %s
                ORDER BY id DESC
            """, (date_filter,))
        else:
            cursor.execute("""
                SELECT id, report_date, title, description, status, created_at, updated_at
                FROM daily_reports
                ORDER BY report_date DESC, id DESC
                LIMIT 500
            """)

        rows = cursor.fetchall()
        conn.close()

        reports = [
            {
                "id":          row['id'],
                "report_date": str(row['report_date']),
                "title":       row['title'],
                "description": row['description'] or '',
                "status":      row['status'],
                "created_at":  str(row['created_at']),
                "updated_at":  str(row['updated_at']),
            }
            for row in rows
        ]
        return jsonify({'success': True, 'reports': reports})

    except Exception as e:
        print(f"GET daily_reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daily_reports', methods=['POST'])
def api_add_daily_report():
    """เพิ่มรายงานใหม่"""
    try:
        data = request.get_json()
        report_date = data.get('report_date')
        title       = data.get('title', '').strip()
        description = data.get('description', '').strip()
        status      = data.get('status', 'in_progress')

        if not title:
            return jsonify({'success': False, 'error': 'title is required'}), 400
        if not report_date:
            return jsonify({'success': False, 'error': 'report_date is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("""
            INSERT INTO daily_reports (report_date, title, description, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, report_date, title, description, status, created_at, updated_at
        """, (report_date, title, description, status))
        row = cursor.fetchone()
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'report': {
                "id":          row['id'],
                "report_date": str(row['report_date']),
                "title":       row['title'],
                "description": row['description'] or '',
                "status":      row['status'],
                "created_at":  str(row['created_at']),
                "updated_at":  str(row['updated_at']),
            }
        })

    except Exception as e:
        print(f"POST daily_reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daily_reports/<int:report_id>', methods=['PUT'])
def api_update_daily_report(report_id):
    """แก้ไขรายงาน"""
    try:
        data = request.get_json()
        report_date = data.get('report_date')
        title       = data.get('title', '').strip()
        description = data.get('description', '').strip()
        status      = data.get('status', 'in_progress')

        if not title:
            return jsonify({'success': False, 'error': 'title is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE daily_reports
            SET report_date = %s,
                title       = %s,
                description = %s,
                status      = %s,
                updated_at  = NOW()
            WHERE id = %s
        """, (report_date, title, description, status, report_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"PUT daily_reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daily_reports/<int:report_id>', methods=['DELETE'])
def api_delete_daily_report(report_id):
    """ลบรายงาน"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_reports WHERE id = %s", (report_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        print(f"DELETE daily_reports error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/settings')
def settings():
    import platform, sys
    info = {
        'db_host':   config.DB_HOST,
        'db_port':   config.DB_PORT,
        'db_name':   config.DB_NAME,
        'db_user':   config.DB_USER,
        'py_version': sys.version.split()[0],
        'os_info':    platform.system() + ' ' + platform.release(),
    }
    return render_template('setting.html', info=info)


if __name__ == '__main__':

    # กำหนด host='0.0.0.0' เพื่อให้สามารถเข้าถึงจากภายนอก Container ได้
    app.run(host='0.0.0.0', port=5000, debug=True)
