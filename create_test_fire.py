import psycopg2
conn = psycopg2.connect('dbname=memoire_db user=postgres password=maria123 host=localhost')
cur = conn.cursor()
cur.execute("INSERT INTO alerts (lat, lng, severity, status, title, description) VALUES (%s, %s, %s, %s, %s, %s)", 
            (36.16, 1.33, 'high', 'open', 'Forest Fire', 'Controlled test fire for demo'))
conn.commit()
conn.close()
print("Test fire created at (36.16, 1.33)")
