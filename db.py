import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url)
    
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        if fetch:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def execute_one(query, params=None):
    result = execute_query(query, params, fetch=True)
    return result[0] if result else None