import psycopg2
import os

db_url = os.environ.get('DATABASE_URL', 'dbname=memoire_db user=postgres password=maria123 host=localhost')
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM units")
    print(f"Units: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM equipment")
    print(f"Equipment: {cur.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
