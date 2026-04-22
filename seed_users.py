import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:maria123@localhost:5432/memoire_db")

def seed_users():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    users = [
        ('andrew.mike@firesafe.dz', 'Andrew Mike', 'https://randomuser.me/api/portraits/men/32.jpg', 'admin'),
        ('jane.doe@firesafe.dz', 'Jane Doe', 'https://randomuser.me/api/portraits/women/44.jpg', 'fireman'),
        ('micheal.holz@firesafe.dz', 'Micheal Holz', 'https://randomuser.me/api/portraits/men/67.jpg', 'fireman'),
        ('alex.mike@firesafe.dz', 'Alex Mike', 'https://randomuser.me/api/portraits/men/85.jpg', 'citizen'),
        ('paula.wilson@firesafe.dz', 'Paula Wilson', 'https://randomuser.me/api/portraits/women/68.jpg', 'citizen'),
        ('martin.sommer@firesafe.dz', 'Martin Sommer', 'https://randomuser.me/api/portraits/men/22.jpg', 'citizen'),
        ('admin@firesafe.dz', 'Super Admin', 'https://randomuser.me/api/portraits/men/1.jpg', 'admin'),
        ('fireman@firesafe.dz', 'Commandant Omar', 'https://randomuser.me/api/portraits/men/2.jpg', 'fireman')
    ]

    print("Seeding users...")
    for email, name, picture, role in users:
        last_login = (datetime.now() - timedelta(hours=os.urandom(1)[0] % 24)).isoformat()
        cursor.execute("""
            INSERT INTO users (email, name, picture, role, last_login)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE 
            SET name = EXCLUDED.name, picture = EXCLUDED.picture, role = EXCLUDED.role, last_login = EXCLUDED.last_login
        """, (email, name, picture, role, last_login))

    conn.commit()
    cursor.close()
    conn.close()
    print("Successfully seeded users!")

if __name__ == "__main__":
    seed_users()
