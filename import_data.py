import pandas as pd
import psycopg2
import os

HOST = os.environ.get('POSTGRES_HOST', 'localhost')
PORT = os.environ.get('POSTGRES_PORT', '15432')
DATABASE = os.environ.get('POSTGRES_DB', 'sbp-dailyreport')
USERNAME = os.environ.get('POSTGRES_USER', 'bendcemb')
PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'Ben28122523!')

def main():
    try:
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            dbname=DATABASE,
            user=USERNAME,
            password=PASSWORD
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("Loading CSV...")
        df = pd.read_csv('sp_company_updated.csv')
        
        print(f"Loaded {len(df)} rows. Updating database...")
        
        # We can create a temp table and use COPY for fast upload, then UPDATE
        cursor.execute("""
            CREATE TEMP TABLE temp_sp_company (
                company_id INTEGER,
                company TEXT,
                new_company_id FLOAT
            ) ON COMMIT DROP;
        """)
        
        import io
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
