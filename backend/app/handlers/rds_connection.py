import os
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Load environment variables ---
DB_HOST = os.environ["DB_HOST"]            # e.g. mydb.xxxxxx.us-east-1.rds.amazonaws.com
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

# --- Global connection reuse ---
connection = None


def get_connection():
    """Return a live PostgreSQL connection, reusing if possible."""
    global connection
    if connection is not None and connection.closed == 0:
        return connection

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=5
    )
    return connection


def run_query(sql, params=None, fetch=False):
    """
    Execute a SQL query safely.
    :param sql: SQL string with placeholders (%s)
    :param params: tuple/list of parameters
    :param fetch: whether to return fetched rows
    """
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or [])
        if fetch:
            result = cur.fetchall()
        else:
            result = None
        conn.commit()
    return result
