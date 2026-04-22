import psycopg2
import psycopg2.extras
import random
import string
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(".env")
DB_URL = os.environ.get('DATABASE_URL', 'dbname=memoire_db user=postgres password=maria123 host=localhost')

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def seed_everything():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        print("Ensuring tables exist...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS units (id SERIAL PRIMARY KEY, name TEXT UNIQUE, lat REAL, lng REAL, status TEXT);
            CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, picture TEXT, role TEXT, last_login TEXT);
            CREATE TABLE IF NOT EXISTS zones (id SERIAL PRIMARY KEY, name TEXT UNIQUE, risk_level TEXT, center_lat REAL, center_lng REAL, radius_km REAL);
            CREATE TABLE IF NOT EXISTS equipment (id SERIAL PRIMARY KEY, unit_id INTEGER REFERENCES units(id), type TEXT, code TEXT UNIQUE, status TEXT);
            CREATE TABLE IF NOT EXISTS alerts (id SERIAL PRIMARY KEY, title TEXT, severity TEXT, description TEXT, lat REAL, lng REAL, status TEXT, zone_id INTEGER REFERENCES zones(id), domino_risk TEXT, created_at TEXT, reporter_name TEXT, reporter_email TEXT);
            CREATE TABLE IF NOT EXISTS dispatches (id SERIAL PRIMARY KEY, alert_id INTEGER REFERENCES alerts(id), equipment_id INTEGER REFERENCES equipment(id), unit_id INTEGER REFERENCES units(id), eta_minutes REAL, dispatched_at TEXT, status TEXT);
            CREATE TABLE IF NOT EXISTS user_activity (id SERIAL PRIMARY KEY, user_email TEXT, action TEXT, details TEXT, timestamp TEXT);
            DROP TABLE IF EXISTS water;
            CREATE TABLE water (id SERIAL PRIMARY KEY, name TEXT, lat REAL, lng REAL, capacity TEXT);
        """)

        print("Cleaning up existing data...")
        # Truncate all tables to start fresh
        tables = ['dispatches', 'equipment', 'user_activity', 'alerts', 'units', 'zones', 'users']
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
        
        # 1. Add 26 Real Chlef Units
        print("Adding Chlef Fire Units...")
        chlef_units = {
            'Unité Secondaire Abou El Hassen': {'lat': 36.4333, 'lng': 1.1833, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Moyen': 1}},
            'Unité Secondaire Ain Merane': {'lat': 36.1667, 'lng': 0.9667, 'eq': {'Ambulance Sanitaire': 1, 'C.C.F. Moyen': 1}},
            'Unité Secondaire Beni Haoua': {'lat': 36.5333, 'lng': 1.5833, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Moyen': 1, 'C.C.I 4000L': 1}},
            'Unité Secondaire Boukadir': {'lat': 36.0667, 'lng': 1.1167, 'eq': {'Ambulance Sanitaire': 1, 'C.T.E': 1, 'F.P.T': 1}},
            'Unité Secondaire El Karimia': {'lat': 35.9996, 'lng': 1.5401, 'eq': {'Ambulance Sanitaire': 1, 'C.C.I 4000L': 1}},
            'Unité Secondaire El Marsa': {'lat': 36.4000, 'lng': 0.8833, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Moyen': 1, 'C.C.I 6000L': 1}},
            'Unité Secondaire Oued Fodda': {'lat': 36.1904, 'lng': 1.5372, 'eq': {'Ambulance Sanitaire': 2, 'F.P.T': 1}},
            'Unité Secondaire Ouled Ben Abdelkader': {'lat': 35.9833, 'lng': 1.2500, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Léger': 1, 'C.C.F. Moyen': 1, 'C.T.E': 1}},
            'Unité Secondaire Ouled Fares': {'lat': 36.2333, 'lng': 1.2167, 'eq': {'Ambulance Sanitaire': 2, 'F.P.T': 1}},
            'Unité Secondaire Taougrit': {'lat': 36.1950, 'lng': 0.8750, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Léger': 1, 'C.C.F. Moyen': 1, 'C.C.I 6000L': 1}},
            'Unité Secondaire Tenes': {'lat': 36.5108, 'lng': 1.3080, 'eq': {'Ambulance Sanitaire': 2, 'C.C.F. Moyen': 1, 'V. Secours Routiers VSR': 1}},
            'Unité Secondaire Zeboudja': {'lat': 36.3167, 'lng': 1.3500, 'eq': {'Ambulance Sanitaire': 1, 'C.C.F. Léger': 1, 'C.C.F. Moyen': 1}},
            'Unité Principale Chlef': {'lat': 36.1650, 'lng': 1.3340, 'eq': {'Ambulance Médicalisée': 1, 'Ambulance Sanitaire': 4, 'C.C.I 6000L': 2, 'F.P.T': 2, 'C.C.F. Moyen': 2}}
        }
        
        for name, data in chlef_units.items():
            cursor.execute("INSERT INTO units (name, lat, lng, status) VALUES (%s, %s, %s, 'active') RETURNING id", (name, data['lat'], data['lng']))
            unit_id = cursor.fetchone()[0]
            
            eq_list = []
            for eq_type, count in data['eq'].items():
                for i in range(count):
                    rnd = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
                    eq_code = f"{eq_type[:3].upper()}-{unit_id}-{i+1}-{rnd}"
                    eq_list.append((unit_id, eq_type, eq_code, 'available'))
            
            if eq_list:
                psycopg2.extras.execute_values(cursor, "INSERT INTO equipment (unit_id, type, code, status) VALUES %s", eq_list)

        # 2. Add National Wilayas
        print("Adding National Wilaya Centers...")
        wilayas = [
            ("Alger Central", 36.7538, 3.0588), ("Oran Central", 35.6987, -0.6308), ("Constantine Central", 36.3650, 6.6147),
            ("Annaba Central", 36.9000, 7.7667), ("Blida Central", 36.4700, 2.8277), ("Setif Central", 36.1898, 5.4108)
        ]
        for name, lat, lng in wilayas:
            cursor.execute("INSERT INTO units (name, lat, lng, status) VALUES (%s, %s, %s, 'active') RETURNING id", (name, lat, lng))
            u_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO equipment (unit_id, type, code, status) VALUES (%s, %s, %s, %s)", (u_id, 'CCI', f'CCI-NAT-{u_id}', 'available'))

        # 3. Add Zones
        print("Adding Tactical Zones...")
        zones = [
            ("Chlef Urban", "high", 36.1653, 1.3345, 7.5),
            ("Coastal Belt", "medium", 36.43, 1.25, 12),
            ("Southern Plains", "low", 35.95, 1.42, 15)
        ]
        psycopg2.extras.execute_values(cursor, "INSERT INTO zones (name, risk_level, center_lat, center_lng, radius_km) VALUES %s", zones)

        # 4. Add Users
        print(f"Connected to Database: {conn.get_dsn_parameters().get('dbname')}")

        print("Tactical Data: Refilling Water Sources...")
        water_sources = [
            ("Barrage Sidi Yacoub", 36.1200, 1.2500, "12.5M m3"),
            ("Barrage Oued Fodda", 36.1500, 1.5500, "8.2M m3"),
            ("Chlef River Access (Central)", 36.1700, 1.3300, "Continuous"),
            ("Tenes Reservoir", 36.5000, 1.3200, "2.1M m3")
        ]
        psycopg2.extras.execute_values(cursor, "INSERT INTO water (name, lat, lng, capacity) VALUES %s", water_sources)

        print("Adding System Users...")
        users = [
            ('admin@firesafe.dz', 'Admin Controller', '', 'admin', now_iso()),
            ('mmam64358@gmail.com', 'Mmam64358', '', 'admin', now_iso()),
            ('fireman@firesafe.dz', 'Field Agent', '', 'fireman', now_iso()),
            ('citizen@demo.dz', 'Demo Citizen', '', 'citizen', now_iso())
        ]
        psycopg2.extras.execute_values(cursor, "INSERT INTO users (email, name, picture, role, last_login) VALUES %s", users)

        # 5. Add a few starting alerts
        print("Adding Initial Tactical Alerts...")
        alerts = [
            ("Forest Fire Tenes", "high", "Coastal wildfire spreading", 36.5108, 1.3080, "resolved", now_iso()),
            ("Industrial Hazard Chlef", "critical", "Warehouse fire central", 36.1650, 1.3340, "open", now_iso())
        ]
        for a in alerts:
            cursor.execute("INSERT INTO alerts (title, severity, description, lat, lng, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", a)

        conn.commit()
        print("\nDATABASE SUCCESSFULLY REFILLED (PostgreSQL)")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"FAILED TO REFILL: {e}")

if __name__ == "__main__":
    seed_everything()
