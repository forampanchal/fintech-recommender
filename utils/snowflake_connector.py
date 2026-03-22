import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def get_connection():
    """Returns a Snowflake connection"""
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )
    return conn


def read_table(table_name, schema='GOLD'):
    """Read a Snowflake table into pandas DataFrame"""
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM {schema}.{table_name}", conn)
    conn.close()
    print(f"✅ Loaded {table_name}: {len(df):,} rows")
    return df


def test_connection():
    """Test Snowflake connection"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    version = cursor.fetchone()[0]
    conn.close()
    print(f"✅ Connected to Snowflake! Version: {version}")
    return True
