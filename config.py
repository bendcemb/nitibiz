import os

# ============================================================
# Database Configuration
# ============================================================
DB_HOST     = os.environ.get('POSTGRES_HOST',     'localhost')
DB_PORT     = os.environ.get('POSTGRES_PORT',     '5432')
DB_NAME     = os.environ.get('POSTGRES_DB',       'sbp-dailyreport')
DB_USER     = os.environ.get('POSTGRES_USER',     'bendcemb')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'Ben28122523!')

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ============================================================
# Data Paths
# ============================================================
DATA_DIR     = os.path.join(os.path.dirname(__file__), 'data')
SBP_DATA_DIR = os.path.join(DATA_DIR, 'sbp')
