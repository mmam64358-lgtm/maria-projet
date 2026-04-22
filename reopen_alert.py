import psycopg2
conn = psycopg2.connect('dbname=memoire_db user=postgres password=maria123 host=localhost')
cur = conn.cursor()
cur.execute("UPDATE alerts SET status = 'open' WHERE id = 14")
conn.commit()
cur.execute("SELECT id, title, status FROM alerts WHERE id = 14")
print('Alert updated:', cur.fetchone())
conn.close()
print('Done.')
