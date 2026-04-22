import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv(".env")
db_url = os.environ.get('DATABASE_URL', 'dbname=memoire_db user=postgres password=maria123 host=localhost')

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    tables = ['alerts', 'dispatches', 'equipment', 'units', 'users', 'water', 'zones']
    
    print("Database Table Audit:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        res = cursor.fetchone()
        print(f"- {table}: {res['count']} rows")
        
    print("\nRecent Alerts:")
    cursor.execute("SELECT id, status, reporter_name FROM alerts ORDER BY id DESC LIMIT 5")
    alerts = cursor.fetchall()
    for a in alerts:
        print(f"  ID:{a['id']} | Status:{a['status']} | Reporter:{a['reporter_name']}")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
