import os
from app import app, get_db_connection

with app.app_context():
    conn = get_db_connection()
    try:
        alerts = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()
        units = conn.execute('SELECT COUNT(*) FROM units').fetchone()
        equipment = conn.execute('SELECT COUNT(*) FROM equipment').fetchone()
        print(f"Alerts: {alerts[0] if alerts else 0}")
        print(f"Units: {units[0] if units else 0}")
        print(f"Equipment: {equipment[0] if equipment else 0}")
    except Exception as e:
        print(f"Error: {e}")
