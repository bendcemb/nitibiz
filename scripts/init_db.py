import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
import time

# รองรับการรันทั้งจาก root และจาก scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def init_db():
    print("Initializing Database...")
    
    engine = create_engine(config.DATABASE_URL)
    
    # Wait for DB to be ready
    for i in range(10):
        try:
            with engine.connect() as conn:
                print("Successfully connected to the database.")
                break
        except Exception as e:
            print(f"Waiting for database... ({i+1}/10)")
            time.sleep(3)
    else:
        print("Could not connect to the database. Exiting.")
        return

    # Wipe the database
    print("Wiping the database completely...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    folder = config.SBP_DATA_DIR
    if not os.path.exists(folder):
        print(f"Folder '{folder}' does not exist. Please run from project root.")
        return

    for file in os.listdir(folder):
        if file.endswith('.csv'):
            file_path = os.path.join(folder, file)
            table_name = file.replace('.csv', '').replace('-', '_')
            print(f"Processing {file} into table {table_name}...")
            
            # Use utf-8-sig for excel exported CSVs
            encoding = 'utf-8-sig'
                
            try:
                # Read CSV (default quoting handles Excel newlines properly)
                df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
                
                # Replace newlines in all string columns with space
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].astype(str).str.replace(r'[\r\n]+', ' ', regex=True)
                    
                # Clean up column names (strip whitespace)
                df.columns = df.columns.str.strip()
                
                # Remove duplicates for tables that will have primary keys
                if table_name in ['sbp_company', 'master_company']:
                    if 'company_id' in df.columns:
                        # Drop rows where company_id is entirely null
                        df.dropna(subset=['company_id'], inplace=True)
                        # Drop duplicates based on company_id
                        df.drop_duplicates(subset=['company_id'], keep='first', inplace=True)
                        print(f"  Cleaned duplicates. Rows remaining: {len(df)}")

                # Save to SQL
                df.to_sql(table_name, engine, if_exists='replace', index=False)
                print(f"  Successfully loaded {len(df)} rows into {table_name}.")

                # Add Primary Key for specific tables
                if table_name in ['sbp_company', 'master_company']:
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (company_id);"))
                            conn.commit()
                        print(f"  -> Added PRIMARY KEY (company_id) to {table_name}.")
                    except Exception as pk_err:
                        print(f"  -> Warning: Could not add PRIMARY KEY to {table_name}. (May contain duplicates: {pk_err})")
            except Exception as e:
                print(f"  Error processing {file}: {e}")

if __name__ == '__main__':
    init_db()
