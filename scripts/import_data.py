import pandas as pd
import psycopg2
import os
import io
import sys

# รองรับการรันทั้งจาก root และจาก scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def main():
    try:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        csv_path = os.path.join(config.DATA_DIR, 'sp_company_updated.csv')
        print(f"Loading CSV from {csv_path}...")
        df = pd.read_csv(csv_path)
        
        print(f"Loaded {len(df)} rows. Updating database...")
        
        # We can create a temp table and use COPY for fast upload, then UPDATE
        cursor.execute("""
            CREATE TEMP TABLE temp_sp_company (
                company_id INTEGER,
                company TEXT,
                new_company_id FLOAT
            ) ON COMMIT DROP;
        """)
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False)
        csv_buffer.seek(0)
        
        cursor.copy_expert("COPY temp_sp_company FROM STDIN WITH CSV", csv_buffer)
        
        # Now update the main table
        cursor.execute("""
            UPDATE sbp_company s
            SET new_company_id = t.new_company_id
            FROM temp_sp_company t
            WHERE s.company_id = t.company_id;
        """)
        
        conn.commit()
        print(f"Updated successfully! Rows affected: {cursor.rowcount}")
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    main()
