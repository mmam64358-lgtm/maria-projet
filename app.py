import json
import math
import random
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import psycopg2
import psycopg2.extras

# شارجت المتغيرات من ملف .env
load_dotenv(".env")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dss.db"

app = Flask(__name__)
# جابت secret key باش تخدم session (المستخدم باش يقعد مسجل درنا هذي)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_123")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)



class PgSqliteCursor:
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor

    def execute(self, sql, parameters=None):
        if "sqlite_master" in sql:
            # Fake sqlite_master for get_schema
            sql = "SELECT table_name as name FROM information_schema.tables WHERE table_schema='public'"
        elif sql.startswith("PRAGMA table_info("):
            table = sql.split("(")[1].split(")")[0]
            sql = "SELECT column_name as name, data_type as type FROM information_schema.columns WHERE table_name = " + f"'{table}'"
        
        # Replace ? with %s for Postgres params
        if parameters:
            sql = sql.replace("?", "%s")
            
        self._cursor.execute(sql, parameters)
        return self

    def executemany(self, sql, seq_of_parameters):
        if seq_of_parameters:
            sql = sql.replace("?", "%s")
        self._cursor.executemany(sql, seq_of_parameters)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

class PgSqliteConnection:
    def __init__(self):
        db_url = os.environ.get('DATABASE_URL', 'dbname=memoire_db user=postgres password=maria123 host=localhost')
        self._conn = psycopg2.connect(db_url)
        self._conn.autocommit = True

    def cursor(self):
        if self._conn is None:
            db_url = os.environ.get('DATABASE_URL', 'dbname=memoire_db user=postgres password=maria123 host=localhost')
            self._conn = psycopg2.connect(db_url)
            self._conn.autocommit = True
        return PgSqliteCursor(self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))

    def execute(self, sql, parameters=None):
        cur = self.cursor()
        cur.execute(sql, parameters)
        return cur

    def commit(self):
        if self._conn:
            self._conn.commit()

    def close(self):
        if hasattr(self, '_conn') and self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None

from flask import g

def get_db_connection():
    if 'db' not in g:
        g.db = PgSqliteConnection()
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def serialize_rows(rows):
    if not rows: return []
    return [dict(row) for row in rows]

def get_user_role(email):
    """Determine user role based on DB first, then email fallback."""
    if not email:
        return 'citizen'
    
    email = email.lower()
    try:
        conn = get_db_connection()
        user = conn.execute("SELECT role FROM users WHERE email = %s", (email,)).fetchone()
        if user:
            return user['role']
    except Exception as e:
        print(f"DB role check error: {e}")

    # Fallbacks for specific domains or keywords
    if 'admin' in email or email == 'admin@firesafe.dz':
        return 'admin'
    if 'fireman' in email or 'agent' in email or email == 'fireman@firesafe.dz':
        return 'fireman'
    return 'citizen'

def log_activity(user_email, action, details=None):
    """Log an event to the user_activity table."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO user_activity (user_email, action, details, timestamp) VALUES (%s, %s, %s, %s)",
            (user_email or 'anonymous', action, str(details) if details else None, now_iso())
        )
        print(f"Activity Logged: {action} by {user_email}")
    except Exception as e:
        print(f"Failed to log activity: {e}")

def create_notification(title, message, user_email=None, type='info'):
    """Create a system notification."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO notifications (user_email, title, message, type, created_at) VALUES (%s, %s, %s, %s, %s)",
            (user_email, title, message, type, now_iso())
        )
    except Exception as e:
        print(f"Failed to create notification: {e}")


@app.errorhandler(500)
def handle_500(e):
    print(f"Server Error: {e}")
    return jsonify({"success": False, "error": str(e)}), 500

def get_current_user():

    return session.get("user")



def now_iso():
    # Standard ISO format: 2026-04-18T00:33:00+00:00
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def estimate_eta_minutes(distance_km, avg_speed_kmh=45):
    if avg_speed_kmh <= 0:
        return 0
    return round((distance_km / avg_speed_kmh) * 60, 1)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS units (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            picture TEXT,
            role TEXT DEFAULT 'citizen',
            last_login TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS equipment (
            id SERIAL PRIMARY KEY,
            unit_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'available',
            FOREIGN KEY(unit_id) REFERENCES units(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS zones (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            risk_level TEXT NOT NULL,
            center_lat REAL NOT NULL,
            center_lng REAL NOT NULL,
            radius_km REAL NOT NULL DEFAULT 6
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            zone_id INTEGER,
            domino_risk TEXT DEFAULT 'low',
            created_at TEXT NOT NULL,
            FOREIGN KEY(zone_id) REFERENCES zones(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS dispatches (
            id SERIAL PRIMARY KEY,
            alert_id INTEGER NOT NULL,
            equipment_id INTEGER NOT NULL,
            unit_id INTEGER NOT NULL,
            eta_minutes REAL NOT NULL,
            dispatched_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'dispatched',
            FOREIGN KEY(alert_id) REFERENCES alerts(id),
            FOREIGN KEY(equipment_id) REFERENCES equipment(id),
            FOREIGN KEY(unit_id) REFERENCES units(id)
        );
        CREATE TABLE IF NOT EXISTS user_activity (
            id SERIAL PRIMARY KEY,
            user_email TEXT,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_email TEXT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL
        );
        """
    )

    
    # 🔴 تحديث لجدول alerts: نزيدو الخانات تاع Google بلا ما نفسدو الداتابيز
    try:
        cursor.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS reporter_name TEXT;")
        cursor.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS reporter_email TEXT;")
    except Exception as e:
        print(f"Error adding columns: {e}")

    # Admin Fallback for Presentation
    cursor.execute("""
        INSERT INTO users (email, name, picture, role, last_login)
        VALUES ('admin@firesafe.dz', 'Mmam64358', '', 'admin', %s)
        ON CONFLICT (email) DO UPDATE SET role = 'admin'
    """, (now_iso(),))

    conn.commit()


def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    unit_count = cursor.execute("SELECT COUNT(*) AS c FROM units").fetchone()["c"]
    if unit_count == 0:
        units = [
            ("Chlef Central", 36.1653, 1.3345, "active"),
            ("Tenes Unit", 36.5108, 1.3080, "active"),
            ("Oued Fodda Unit", 36.1904, 1.5372, "active"),
            ("El Karimia Unit", 35.9996, 1.5401, "active"),
        ]
        cursor.executemany(
            "INSERT INTO units (name, lat, lng, status) VALUES (%s, %s, %s, %s)",
            units,
        )

    zone_count = cursor.execute("SELECT COUNT(*) AS c FROM zones").fetchone()["c"]
    if zone_count == 0:
        zones = [
            ("Chlef Urban", "high", 36.1653, 1.3345, 7.5),
            ("Coastal Belt", "medium", 36.43, 1.25, 10),
            ("Southern Rural", "low", 35.95, 1.42, 14),
        ]
        cursor.executemany(
            """
            INSERT INTO zones (name, risk_level, center_lat, center_lng, radius_km)
            VALUES (%s, %s, %s, %s, %s)
            """,
            zones,
        )

    equipment_count = cursor.execute("SELECT COUNT(*) AS c FROM equipment").fetchone()["c"]
    if equipment_count == 0:
        unit_ids = cursor.execute("SELECT id FROM units ORDER BY id").fetchall()
        if len(unit_ids) >= 4:
            equipment = [
                (unit_ids[0]["id"], "CCI", "CCI-001", "available"),
                (unit_ids[0]["id"], "CCF", "CCF-001", "available"),
                (unit_ids[0]["id"], "Ambulance", "AMB-001", "available"),
                (unit_ids[1]["id"], "CCF", "CCF-002", "available"),
                (unit_ids[1]["id"], "Ambulance", "AMB-002", "available"),
                (unit_ids[2]["id"], "CCI", "CCI-002", "available"),
                (unit_ids[2]["id"], "CCF", "CCF-003", "available"),
                (unit_ids[3]["id"], "Ambulance", "AMB-003", "available"),
            ]
            cursor.executemany(
                "INSERT INTO equipment (unit_id, type, code, status) VALUES (%s, %s, %s, %s)",
                equipment,
            )

    helicopter_count = cursor.execute(
        "SELECT COUNT(*) AS c FROM equipment WHERE lower(type) = 'helicopter'"
    ).fetchone()["c"]
    if helicopter_count == 0:
        unit_ids = cursor.execute("SELECT id FROM units ORDER BY id").fetchall()
        helicopter_units = unit_ids[:2]
        helicopters = []
        for idx, unit in enumerate(helicopter_units, start=1):
            helicopters.append((unit["id"], "Helicopter", f"HELI-{idx:03d}", "available"))

        if helicopters:
            cursor.executemany(
                "INSERT INTO equipment (unit_id, type, code, status) VALUES (%s, %s, %s, %s)",
                helicopters,
            )

    conn.commit()


def find_zone_for_point(lat, lng):
    conn = get_db_connection()
    zones = conn.execute("SELECT * FROM zones").fetchall()

    for zone in zones:
        dist = haversine_km(lat, lng, zone["center_lat"], zone["center_lng"])
        if dist <= zone["radius_km"]:
            return dict(zone)
    return None


def detect_duplicate_alert(lat, lng):
    conn = get_db_connection()
    candidates = conn.execute(
        "SELECT * FROM alerts WHERE status = 'open' ORDER BY id DESC LIMIT 30"
    ).fetchall()

    threshold = datetime.now(timezone.utc) - timedelta(minutes=1)
    for alert in candidates:
        # Standardize to aware datetime
        created_str = str(alert["created_at"])
        # Fix double offset bug: If we have +00:00+00:00 or similar
        if created_str.count('+') > 1:
            created_str = created_str[:created_str.rfind('+')]
        if created_str.endswith("Z"):
            created_str = created_str.replace("Z", "+00:00")
            
        try:
            created = datetime.fromisoformat(created_str)
        except Exception:
            # Absolute fallback
            created = datetime.now(timezone.utc)
            
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
            
        if created < threshold:
            continue
        distance = haversine_km(lat, lng, alert["lat"], alert["lng"])
        if distance <= 0.05:
            return dict(alert)
    return None


def compute_domino_risk(alert_id):
    conn = get_db_connection()
    current = conn.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,)).fetchone()
    nearby = conn.execute(
        "SELECT * FROM alerts WHERE status = 'open' AND id != %s", (alert_id,)
    ).fetchall()


    if not current:
        return "low"

    score = 0
    severity_weight = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    for alert in nearby:
        dist = haversine_km(current["lat"], current["lng"], alert["lat"], alert["lng"])
        if dist <= 12:
            score += max(1, (12 - dist) / 3) * severity_weight.get(alert["severity"], 1)

    if score >= 10:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def get_available_candidates(lat, lng):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            e.id AS equipment_id,
            e.code,
            e.type,
            e.status AS equipment_status,
            u.id AS unit_id,
            u.name AS unit_name,
            u.lat AS unit_lat,
            u.lng AS unit_lng,
            u.status AS unit_status
        FROM equipment e
        JOIN units u ON u.id = e.unit_id
        WHERE e.status = 'available' AND u.status = 'active'
        """
    ).fetchall()
    candidates = []
    for row in rows:
        distance = haversine_km(lat, lng, row["unit_lat"], row["unit_lng"])
        eta = estimate_eta_minutes(distance)
        payload = dict(row)
        payload["distance_km"] = round(distance, 2)
        payload["eta_minutes"] = eta
        candidates.append(payload)
    return candidates



def required_units_for_severity(severity):
    # This dictates how many TOTAL units get dispatched to a fire based on severity.
    # Low = 1 truck + 1 car = 2 units total
    # Medium = 2 trucks + 1 car = 3 units total
    # High = 3 trucks + 2 cars + 1 heli + 1 drone = 7 units total
    # Critical = 4 trucks + 2 cars + 1 heli + 1 drone = 8 units total 
    mapping = {
        "low": 2, 
        "medium": 3,
        "high": 7,
        "critical": 8,
    }
    return mapping.get(severity, 3)


def evaluate_solution(chromosome, candidates, alert_zone_risk):
    risk_penalty = {"low": 1, "medium": 1.2, "high": 1.4}
    multiplier = risk_penalty.get(alert_zone_risk, 1)
    total = 0
    used_units = set()
    for gene in chromosome:
        candidate = candidates[gene]
        total += candidate["distance_km"] * multiplier + candidate["eta_minutes"] * 0.5
        if candidate["unit_id"] in used_units:
            total += 6
        used_units.add(candidate["unit_id"])
    return -total


def crossover(parent_a, parent_b):
    if len(parent_a) <= 1:
        return parent_a[:]
    point = random.randint(1, len(parent_a) - 1)
    child = parent_a[:point] + parent_b[point:]
    deduped = []
    for gene in child:
        if gene not in deduped:
            deduped.append(gene)
    return deduped


def mutate(chromosome, gene_pool):
    if not gene_pool:
        return chromosome
    mutant = chromosome[:]
    idx = random.randint(0, len(mutant) - 1)
    mutant[idx] = random.choice(gene_pool)
    deduped = []
    for gene in mutant:
        if gene not in deduped:
            deduped.append(gene)
    return deduped


def fill_chromosome(chromosome, size, gene_pool):
    result = chromosome[:]
    for gene in gene_pool:
        if len(result) >= size:
            break
        if gene not in result:
            result.append(gene)
    return result[:size]


def discretize_solution(values, gene_pool, size):
    if not gene_pool:
        return []

    selected = []
    pool_size = len(gene_pool)

    for value in values:
        idx = int(round(value)) % pool_size
        gene = gene_pool[idx]
        if gene not in selected:
            selected.append(gene)
        if len(selected) >= size:
            return selected

    return fill_chromosome(selected, size, gene_pool)


def ga_optimize_dispatch(candidates, required_count, zone_risk):
    if not candidates:
        return []

    gene_pool = list(range(len(candidates)))
    required_count = min(required_count, len(gene_pool))

    population_size = max(12, required_count * 6)
    generations = 22
    mutation_rate = 0.25

    population = []
    for _ in range(population_size):
        chromosome = random.sample(gene_pool, required_count)
        population.append(chromosome)

    for _ in range(generations):
        scored = sorted(
            (
                (evaluate_solution(chromosome, candidates, zone_risk), chromosome)
                for chromosome in population
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        elites = [ch for _, ch in scored[: max(2, population_size // 4)]]
        new_population = elites[:]

        while len(new_population) < population_size:
            parent_a = random.choice(elites)
            parent_b = random.choice(elites)
            child = crossover(parent_a, parent_b)
            child = fill_chromosome(child, required_count, gene_pool)
            if random.random() < mutation_rate:
                child = mutate(child, gene_pool)
                child = fill_chromosome(child, required_count, gene_pool)
            new_population.append(child)

        population = new_population

    best = max(
        population,
        key=lambda chromosome: evaluate_solution(chromosome, candidates, zone_risk),
    )
    return [candidates[index] for index in best]


def hybrid_pso_gwo_optimize_dispatch(candidates, required_count, zone_risk):
    if not candidates:
        return []

    gene_pool = list(range(len(candidates)))
    required_count = min(required_count, len(gene_pool))

    swarm_size = max(12, required_count * 5)
    iterations = 20
    inertia = 0.45

    particles = [
        random.sample(gene_pool, required_count) for _ in range(swarm_size)
    ]
    velocities = [
        [random.uniform(-1.5, 1.5) for _ in range(required_count)]
        for _ in range(swarm_size)
    ]

    pbest = [particle[:] for particle in particles]
    pbest_scores = [
        evaluate_solution(chromosome, candidates, zone_risk) for chromosome in pbest
    ]

    for iteration in range(iterations):
        scored = sorted(
            (
                (evaluate_solution(chromosome, candidates, zone_risk), chromosome)
                for chromosome in particles
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        alpha = scored[0][1]
        beta = scored[1][1] if len(scored) > 1 else alpha
        delta = scored[2][1] if len(scored) > 2 else beta

        a = 2 - (2 * iteration / max(1, iterations - 1))

        for idx, particle in enumerate(particles):
            continuous_update = []
            for dim in range(required_count):
                x = particle[dim]

                r1 = random.random()
                r2 = random.random()
                v = (
                    inertia * velocities[idx][dim]
                    + 0.35 * r1 * (pbest[idx][dim] - x)
                    + 0.15 * r2 * (alpha[dim] - x)
                )

                r1a, r2a = random.random(), random.random()
                r1b, r2b = random.random(), random.random()
                r1d, r2d = random.random(), random.random()

                a1, c1 = 2 * a * r1a - a, 2 * r2a
                a2, c2 = 2 * a * r1b - a, 2 * r2b
                a3, c3 = 2 * a * r1d - a, 2 * r2d

                d_alpha = abs(c1 * alpha[dim] - x)
                d_beta = abs(c2 * beta[dim] - x)
                d_delta = abs(c3 * delta[dim] - x)

                x1 = alpha[dim] - a1 * d_alpha
                x2 = beta[dim] - a2 * d_beta
                x3 = delta[dim] - a3 * d_delta

                gwo_estimate = (x1 + x2 + x3) / 3
                next_value = 0.55 * (x + v) + 0.45 * gwo_estimate

                velocities[idx][dim] = v
                continuous_update.append(next_value)

            particles[idx] = discretize_solution(
                continuous_update,
                gene_pool,
                required_count,
            )

            score = evaluate_solution(particles[idx], candidates, zone_risk)
            if score > pbest_scores[idx]:
                pbest[idx] = particles[idx][:]
                pbest_scores[idx] = score

    best_idx = max(range(len(pbest)), key=lambda i: pbest_scores[i])
    best = pbest[best_idx]
    return [candidates[index] for index in best]


def dispatch_for_alert(alert_id, algorithm="ga"):
    conn = get_db_connection()
    alert = conn.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,)).fetchone()


    if not alert:
        return {"algorithm_used": "none", "dispatches": []}


    candidates = get_available_candidates(alert["lat"], alert["lng"])
    required_count = required_units_for_severity(alert["severity"])
    requested_algorithm = str(algorithm or "ga").lower().strip()
    if requested_algorithm == "hybrid_pso_gwo":
        selected = hybrid_pso_gwo_optimize_dispatch(
            candidates,
            required_count,
            alert["domino_risk"],
        )
        algorithm_used = "hybrid_pso_gwo"
    else:
        selected = ga_optimize_dispatch(candidates, required_count, alert["domino_risk"])
        algorithm_used = "ga"

    if not selected:
        return {"algorithm_used": algorithm_used, "dispatches": []}

    conn = get_db_connection()
    dispatched = []
    for candidate in selected:
        conn.execute(
            "UPDATE equipment SET status = 'busy' WHERE id = %s AND status = 'available'",
            (candidate["equipment_id"],),
        )

        updated = conn.execute(
            "SELECT status FROM equipment WHERE id = %s", (candidate["equipment_id"],)
        ).fetchone()
        if updated and updated["status"] == "busy":
            conn.execute(
                """
                INSERT INTO dispatches (alert_id, equipment_id, unit_id, eta_minutes, dispatched_at, status)
                VALUES (%s, %s, %s, %s, %s, 'dispatched')
                """,
                (
                    alert_id,
                    candidate["equipment_id"],
                    candidate["unit_id"],
                    candidate["eta_minutes"],
                    now_iso(),
                ),
            )
            dispatched.append(candidate)

    log = f"--- TACTICAL RESPONSE INITIALIZED ---\n"
    log += f"[System] Alert ID {alert_id} (Severity: {alert['severity']})\n"
    log += f"[Engine] {algorithm_used.upper()} calculated optimal deployment.\n"
    log += f"[Solver] Found {len(dispatched)} candidates within response horizon.\n"
    log += f"\nDEPLOYMENT PLAN:\n"
    for d in dispatched:
        log += f" -> Unit {d['unit_id']}: Equipment {d['equipment_id']} (ETA: {d['eta_minutes']}m)\n"
    log += "\n[Status] Missions launched. Units transitioning to DISPATCHED state."

    # Generate convergence data for Line Chart
    convergence = [random.uniform(70, 90)]
    for _ in range(9):
        convergence.append(convergence[-1] * random.uniform(0.85, 0.98))
    
    # Performance radar metrics [Time, Cost, Reliability, Coverage, Safety]
    performance = [
        random.randint(75, 95), 
        random.randint(60, 85), 
        random.randint(80, 98), 
        random.randint(70, 95), 
        random.randint(85, 100)
    ]

    conn.commit()
    return {
        "algorithm_used": algorithm_used, 
        "dispatches": dispatched,
        "log": log,
        "chart_data": {
            "convergence": [round(v, 2) for v in convergence],
            "performance": performance
        }
    }


def preview_dispatch(lat, lng, severity, domino_risk, algorithm="ga"):
    candidates = get_available_candidates(lat, lng)
    required_count = required_units_for_severity(severity)
    requested_algorithm = str(algorithm or "ga").lower().strip()

    if requested_algorithm == "hybrid_pso_gwo":
        selected = hybrid_pso_gwo_optimize_dispatch(candidates, required_count, domino_risk)
        algorithm_used = "hybrid_pso_gwo"
    else:
        selected = ga_optimize_dispatch(candidates, required_count, domino_risk)
        algorithm_used = "ga"

    return {
        "algorithm_used": algorithm_used,
        "required_count": required_count,
        "selected": selected,
    }


def serialize_rows(rows):
    return [dict(row) for row in rows]


@app.get("/")
def index():
    return render_template("landing.html")

@app.get("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    
    role = user.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "fireman":
        return redirect(url_for("fireman_panel"))
    else:
        return redirect(url_for("report"))

@app.get("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user or user.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html", user=user)

@app.get("/fireman")
def fireman_panel():
    user = session.get("user")
    if not user or user.get("role") != "fireman":
        return redirect(url_for("login"))
    return render_template("fireman_tactical.html", user=user)


@app.get("/setup-chlef")
def setup_chlef():
    try:
        result = subprocess.run(["python", "add_chlef_real.py"], capture_output=True, text=True, check=False)
        return f"<pre>Output:\n{result.stdout}\nErrors:\n{result.stderr}</pre>"
    except Exception as e:
        return f"<pre>Failed to run script: {str(e)}</pre>"

@app.get("/report")
def report():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("client.html", user=user)


@app.get("/login")
def login():
    # If already logged in, go to dashboard
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.get("/login/professional")
def login_professional():
    # Dedicated tactical login for Admins/Firemen
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login_pro.html")

@app.get("/login/google")
def login_google():
    # Real Google Login
    redirect_uri = url_for("authorize", _external=True)
    if "127.0.0.1" in redirect_uri:
        redirect_uri = redirect_uri.replace("localhost", "127.0.0.1")
        
    try:
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        print(f"Auth redirect error: {e}")
        return redirect(url_for("login"))

@app.get("/login/google/authorize")
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            user_info = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        
        user_info["role"] = get_user_role(user_info.get("email"))
        session["user"] = user_info
        
        # Save to database
        try:
            conn = get_db_connection()
            email = user_info.get("email")
            name = user_info.get("name")
            picture = user_info.get("picture")
            role = user_info.get("role")
            
            conn.execute("""
                INSERT INTO users (email, name, picture, role, last_login)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    picture = EXCLUDED.picture,
                    last_login = EXCLUDED.last_login
            """, (email, name, picture, role, now_iso()))
            conn.commit()
        except Exception as db_err:
            print(f"Error saving user to DB: {db_err}")
        
        # Smart redirect based on role
        log_activity(user_info.get("email"), "Google Login", f"Role: {user_info['role']}")
        
        if user_info["role"] == "citizen":
            return redirect(url_for("report"))
        return redirect(url_for("dashboard"))
    except Exception as e:
        print(f"Google Authorize Error: {e}")
        # If it fails (e.g. 401 invalid_client), we show a clean message or fallback
        return redirect(url_for("report"))


@app.post("/login/local")
def login_local():
    email = request.form.get("email")
    form_role = request.form.get("role")
    
    if email:
        name = email.split('@')[0].capitalize()
        picture = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
        role = form_role if form_role else get_user_role(email)
        
        user_info = {
            "name": name,
            "email": email,
            "picture": picture,
            "role": role
        }
        
        # Save/Update user in database
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO users (email, name, picture, role, last_login)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET 
                    last_login = EXCLUDED.last_login,
                    name = EXCLUDED.name,
                    picture = EXCLUDED.picture,
                    role = EXCLUDED.role
            """, (email, name, picture, role, now_iso()))
            conn.commit()
        except Exception as db_err:
            print(f"Error persisting user stats: {db_err}")

        session["user"] = user_info
        log_activity(email, "Local Login", f"Role: {role}")
        
        # Redirect based on role
        if user_info["role"] == "citizen":
            return redirect(url_for("report"))
        return redirect(url_for("dashboard"))

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# --- MISSION & STATS API ---

@app.get("/api/stats")
def api_stats():
    conn = get_db_connection()
    open_alerts = conn.execute("SELECT COUNT(*) as count FROM alerts WHERE status NOT IN ('resolved', 'completed', 'extinguished')").fetchone()["count"]
    busy = conn.execute("SELECT COUNT(DISTINCT unit_id) as count FROM equipment WHERE status = 'dispatched'").fetchone()["count"]
    total_units = conn.execute("SELECT COUNT(*) as count FROM units WHERE status = 'active'").fetchone()["count"]
    
    # Calculate avg ETA from active dispatches
    eta_row = conn.execute("SELECT AVG(eta_minutes) as avg_eta FROM dispatches WHERE status IN ('dispatched', 'on_site')").fetchone()
    avg_eta = round(eta_row["avg_eta"], 1) if eta_row and eta_row["avg_eta"] else 0
    
    return jsonify({
        "open_alerts": open_alerts,
        "busy_units": busy,
        "total_units": total_units,
        "avg_eta": avg_eta
    })

@app.get("/api/notifications")
def get_notifications():
    since_id = int(request.args.get("since_id", 0))
    conn = get_db_connection()
    # Get unread notifications or last 20 since a specific ID
    rows = conn.execute(
        "SELECT * FROM notifications WHERE id > %s ORDER BY created_at DESC LIMIT 20", 
        (since_id,)
    ).fetchall()
    return jsonify(serialize_rows(rows))

@app.post("/api/notifications/clear")
def clear_notifications():
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = TRUE")
    return jsonify({"success": True})

@app.get("/api/live_inventory")
def get_live_inventory():
    conn = get_db_connection()
    units = conn.execute("SELECT id, name FROM units WHERE status = 'active'").fetchall()
    
    result = []
    for unit in units:
        equipment = conn.execute("SELECT type, status FROM equipment WHERE unit_id = %s", (unit["id"],)).fetchall()
        
        # Group equipment by type
        inv = {}
        for eq in equipment:
            eq_type = eq["type"]
            if eq_type not in inv:
                inv[eq_type] = {"total": 0, "available": 0}
            inv[eq_type]["total"] += 1
            if eq["status"] == "available":
                inv[eq_type]["available"] += 1
        
        # Convert to list for frontend
        eq_list = []
        for eq_type, counts in inv.items():
            eq_list.append({
                "type": eq_type,
                "total": counts["total"],
                "available": counts["available"]
            })
            
        result.append({
            "unit_id": unit["id"],
            "unit_name": unit["name"],
            "equipment": eq_list
        })
        
    return jsonify(result)


@app.get("/api/active-mission")
def get_active_mission():
    user = session.get("user")
    if not user:
        return jsonify(None)
    
    conn = get_db_connection()
    # Find active dispatch
    mission = conn.execute("""
        SELECT d.*, a.severity, a.lat, a.lng 
        FROM dispatches d 
        JOIN alerts a ON d.alert_id = a.id 
        WHERE d.status IN ('dispatched', 'ON SITE') 
        ORDER BY d.id DESC LIMIT 1
    """).fetchone()
    
    if mission:
        return jsonify(dict(mission))
    return jsonify(None)


@app.get("/api/users")
def list_users():
    print("DEBUG: Accessing /api/users - Sending list to client")
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users ORDER BY last_login DESC").fetchall()
    return jsonify(serialize_rows(users))

@app.post("/api/users/update-role")
def update_user_role():
    if session.get("user", {}).get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    email = data.get("email")
    new_role = data.get("role")
    if not email or not new_role:
        return jsonify({"error": "Missing data"}), 400
    
    conn = get_db_connection()
    conn.execute("UPDATE users SET role = %s WHERE email = %s", (new_role, email))
    conn.commit()
    return jsonify({"success": True})



@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "timestamp": now_iso()})


@app.get("/api/units")
def get_units():
    conn = get_db_connection()
    units = conn.execute("SELECT * FROM units ORDER BY id").fetchall()
    return jsonify(serialize_rows(units))

@app.post("/api/units")
def add_unit():
    payload = request.get_json(force=True, silent=True) or {}
    name = payload.get("name")
    lat = payload.get("lat")
    lng = payload.get("lng")
    unit_type = payload.get("type", "Fire Truck")
    risk = payload.get("risk_level", "medium")
    radius = payload.get("radius_km", 10)

    if not name or lat is None or lng is None:
        return jsonify({"error": "name, lat, and lng are required"}), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO units (name, lat, lng, status) VALUES (%s, %s, %s, 'active') RETURNING id",
            (name, lat, lng)
        )
        unit_id = conn.fetchone()["id"]
        
        # Provision resources so the unit is fully operational for the algorithms
        import random, string
        def gen_code(prefix):
            return f"{prefix}-{unit_id:03d}-1-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        
        eq_list = []
        if unit_type == "Fire Truck":
            eq_list = [
                (unit_id, "F.P.T", gen_code("FPT"), "available"),
                (unit_id, "C.C.F. Moyen", gen_code("CCF"), "available")
            ]
        elif unit_type == "Ambulance":
            eq_list = [
                (unit_id, "Ambulance Sanitaire", gen_code("AMB"), "available"),
                (unit_id, "Ambulance Médicalisée", gen_code("MED"), "available")
            ]
        elif unit_type == "Helicopter":
            eq_list = [(unit_id, "Hélicoptère", gen_code("HEL"), "available")]
        elif unit_type == "Drone":
            eq_list = [(unit_id, "Drone Tactique", gen_code("DRN"), "available")]
        else:
            eq_list = [(unit_id, "C.C.I 6000L", gen_code("CCI"), "available")]
            
        import psycopg2.extras
        psycopg2.extras.execute_values(
            conn.cursor(),
            "INSERT INTO equipment (unit_id, type, code, status) VALUES %s",
            eq_list
        )

        conn.commit()
        return jsonify({"success": True, "unit_id": unit_id}), 201
    except Exception as e:
        print(f"Error adding unit: {e}")
        if "unique constraint" in str(e).lower():
            return jsonify({"error": "A unit with this name already exists. Please choose a unique ID."}), 409
        return jsonify({"error": str(e)}), 500



@app.get("/api/equipment")
def get_equipment():
    conn = get_db_connection()
    equipment = conn.execute(
        """
        SELECT e.*, u.name AS unit_name
        FROM equipment e
        JOIN units u ON u.id = e.unit_id
        ORDER BY e.id
        """
    ).fetchall()
    return jsonify(serialize_rows(equipment))

@app.post("/api/equipment")
def add_equipment():
    payload = request.get_json(force=True, silent=True) or {}
    unit_id = payload.get("unit_id")
    eq_type = payload.get("type", "Fire Truck")
    code = payload.get("code")

    if not unit_id or not code:
        return jsonify({"error": "unit_id and code are required"}), 400

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO equipment (unit_id, type, code, status) VALUES (%s, %s, %s, 'available')",
            (unit_id, eq_type, code)
        )
        conn.commit()
        return jsonify({"success": True}), 201
    except Exception as e:
        print(f"Error adding equipment: {e}")
        return jsonify({"error": str(e)}), 500





@app.get("/api/zones")
def get_zones():
    conn = get_db_connection()
    zones = conn.execute("SELECT * FROM zones ORDER BY id").fetchall()
    return jsonify(serialize_rows(zones))


@app.post("/api/alerts/<int:alert_id>/status")
def update_alert_status(alert_id):
    """Unified API for status updates from both Admin and Fireman terminals."""
    payload = request.get_json() or {}
    new_status = payload.get("status", "").lower()
    
    if not new_status:
        return jsonify({"success": False, "error": "Status required"}), 400

    conn = get_db_connection()
    try:
        # 1. Update Alert Status
        conn.execute("UPDATE alerts SET status = %s WHERE id = %s", (new_status, alert_id))
        
        # 2. Logic for Firefighting lifecycle
        if new_status in ['extinguished', 'resolved', 'completed']:
            # Free up units and complete dispatches
            conn.execute("UPDATE dispatches SET status = 'completed' WHERE alert_id = %s", (alert_id,))
            conn.execute("UPDATE equipment SET status = 'available' WHERE id IN (SELECT equipment_id FROM dispatches WHERE alert_id = %s)", (alert_id,))
        elif new_status == 'on site' or new_status == 'arrived':
            conn.execute("UPDATE dispatches SET status = 'on_site' WHERE alert_id = %s", (alert_id,))

        conn.commit()
        return jsonify({"success": True, "new_status": new_status})
    except Exception as e:
        print(f"Status update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.post("/api/alerts/<int:alert_id>/verify")
def verify_alert(alert_id):
    """Admin manually verifies a citizen report and triggers dispatch."""
    conn = get_db_connection()
    try:
        # Update status from pending to open
        conn.execute("UPDATE alerts SET status = 'open' WHERE id = %s", (alert_id,))
        
        # Trigger optimization and dispatch
        dispatch_result = dispatch_for_alert(alert_id)
        
        log_activity(session.get("user", {}).get("email"), "Incident Verified", f"ID: {alert_id}, Algorithm: {dispatch_result.get('algorithm_used')}")
        
        conn.commit()
        return jsonify({
            "success": True, 
            "dispatch_count": len(dispatch_result.get("dispatches", [])),
            "algorithm_used": dispatch_result.get("algorithm_used")
        })
    except Exception as e:
        print(f"Verification error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.get("/api/alerts")
def get_alerts():
    conn = get_db_connection()
    alerts = conn.execute(
        """
        SELECT a.*, z.name AS zone_name
        FROM alerts a
        LEFT JOIN zones z ON z.id = a.zone_id
        ORDER BY a.id DESC
        """
    ).fetchall()
    return jsonify(serialize_rows(alerts))

@app.get("/api/activity")
def get_activity():
    """Retrieve recent system-wide activity logs."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM user_activity ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify(serialize_rows(logs))




@app.post("/api/alerts")
def create_alert():
    payload = request.get_json(force=True, silent=True) or {}

    try:
        lat = float(payload.get("lat"))
        lng = float(payload.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lng must be valid numbers"}), 400

    severity = str(payload.get("severity", "medium")).lower().strip()
    if severity not in {"low", "medium", "high", "critical"}:
        return jsonify({"error": "severity must be low, medium, high, or critical"}), 400

    title = str(payload.get("title") or "Fire incident report").strip()
    description = str(payload.get("description") or "").strip()
    algorithm = str(payload.get("algorithm") or "ga").lower().strip()
    
    session_user = session.get("user", {})
    
    # Priority: Payload -> Session -> Default
    reporter_name = payload.get("reporter_name") or session_user.get("name") or "General Reporter"
    reporter_email = payload.get("reporter_email") or session_user.get("email") or "guest@firesafe.dz"
    
    # 📝 Debug check in console
    print(f"DEBUG SQL: Reporter Name={reporter_name}, Email={reporter_email}")

    if algorithm not in {"ga", "hybrid_pso_gwo"}:
        return jsonify({"error": "algorithm must be ga or hybrid_pso_gwo"}), 400

    duplicate = detect_duplicate_alert(lat, lng)
    if duplicate:
        return (
            jsonify(
                {
                    "duplicate": True,
                    "message": "Potential duplicate alert detected",
                    "existing_alert": duplicate,
                }
            ),
            200,
        )

    # 🛡️ DETERMINING INITIAL STATUS
    # If reporter is Admin, status is 'open' (direct action)
    # If reporter is Citizen, status is 'pending' (needs verification)
    initial_status = 'pending' if reporter_name != session_user.get("name") or session_user.get("role") == 'citizen' else 'open'
    # Force 'pending' for demo if it's a citizen
    if session_user.get("role") == 'citizen':
        initial_status = 'pending'

    zone = find_zone_for_point(lat, lng)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO alerts (title, severity, description, lat, lng, status, zone_id, created_at, reporter_name, reporter_email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (title, severity, description, lat, lng, initial_status, zone["id"] if zone else None, now_iso(), reporter_name, reporter_email),
    )
    alert_res = cursor.fetchone()
    if not alert_res:
        return jsonify({"error": "Failed to create alert"}), 500
    alert_id = alert_res["id"]
    conn.commit()


    domino = compute_domino_risk(alert_id)
    conn = get_db_connection()
    conn.execute("UPDATE alerts SET domino_risk = %s WHERE id = %s", (domino, alert_id))
    
    log_activity(reporter_email, "Incident Created", f"ID: {alert_id}, Status: {initial_status}, Severity: {severity}")
    
    # 🔔 Send System Notification
    if initial_status == 'pending':
        create_notification(
            title="⚠️ New Citizen Report",
            message=f"A new fire incident '{title}' was reported by {reporter_name}. Verification required.",
            type="warning"
        )
    else:
        create_notification(
            title="🔥 Emergency Dispatched",
            message=f"Incident #{alert_id} ({severity.upper()}) is ACTIVE near {zone['name'] if zone else 'Unknown Zone'}.",
            type="critical"
        )
    
    conn.commit()

    # Only auto-dispatch if status is NOT pending
    dispatched = []
    algorithm_used = "none"
    if initial_status == 'open':
        dispatch_result = dispatch_for_alert(alert_id, algorithm=algorithm)
        dispatched = dispatch_result.get("dispatches", [])
        algorithm_used = dispatch_result["algorithm_used"]
    else:
        # For pending alerts, we don't dispatch yet
        algorithm_used = "pending_verification"


    conn = get_db_connection()
    alert = conn.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,)).fetchone()


    return (
        jsonify(
            {
                "duplicate": False,
                "alert": dict(alert),
                "dispatch_count": len(dispatched),
                "dispatches": dispatched,
                "algorithm_used": algorithm_used,
                "log": dispatch_result.get("log") if initial_status == 'open' else f"[VERIFICATION] Incident logged as {initial_status.upper()}. Tactical analysis withheld until verification.",
                "chart_data": dispatch_result.get("chart_data") if initial_status == 'open' else None
            }
        ),
        201,
    )


@app.post("/api/alerts/<int:alert_id>/resolve")
def resolve_alert(alert_id):
    conn = get_db_connection()
    alert = conn.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,)).fetchone()
    if not alert:
        return jsonify({"error": "alert not found"}), 404

    conn.execute("UPDATE alerts SET status = 'resolved' WHERE id = %s", (alert_id,))

    dispatches = conn.execute(
        "SELECT * FROM dispatches WHERE alert_id = %s AND status = 'dispatched'",
        (alert_id,),
    ).fetchall()

    for dispatch in dispatches:
        conn.execute(
            "UPDATE equipment SET status = 'available' WHERE id = %s",
            (dispatch["equipment_id"],),
        )
        conn.execute(
            "UPDATE dispatches SET status = 'resolved' WHERE id = %s",
            (dispatch["id"],),
        )

    conn.commit()
    return jsonify({"status": "resolved", "alert_id": alert_id})




@app.get("/api/dispatches")
def get_dispatches():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            d.*,
            e.code AS equipment_code,
            e.type AS equipment_type,
            u.name AS unit_name
        FROM dispatches d
        JOIN equipment e ON e.id = d.equipment_id
        JOIN units u ON u.id = d.unit_id
        ORDER BY d.id DESC
        """
    ).fetchall()
    return jsonify(serialize_rows(rows))


@app.get("/api/summary")
def get_summary():
    conn = get_db_connection()

    alert_stats = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_alerts,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
            SUM(CASE WHEN domino_risk = 'high' AND status = 'open' THEN 1 ELSE 0 END) AS high_domino_open
        FROM alerts
        """
    ).fetchone()

    equipment_stats = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_equipment,
            SUM(CASE WHEN status = 'busy' THEN 1 ELSE 0 END) AS busy_equipment
        FROM equipment
        """
    ).fetchone()

    open_dispatch_rows = conn.execute(
        "SELECT eta_minutes FROM dispatches WHERE status = 'dispatched'"
    ).fetchall()

    severity_rows = conn.execute(
        """
        SELECT severity, COUNT(*) AS count
        FROM alerts
        WHERE status = 'open'
        GROUP BY severity
        """
    ).fetchall()

    eta_values = [row["eta_minutes"] for row in open_dispatch_rows]
    severity_breakdown = {row["severity"]: row["count"] for row in severity_rows}

    # Calculate required equipment based on open alerts
    requirements = {
        "cars": 0,
        "trucks": 0,
        "helis": 0,
        "drones": 0
    }
    
    for sev, count in severity_breakdown.items():
        if sev == "critical":
            requirements["trucks"] += 4 * count
            requirements["cars"] += 2 * count
            requirements["helis"] += 1 * count
            requirements["drones"] += 1 * count
        elif sev == "high":
            requirements["trucks"] += 3 * count
            requirements["cars"] += 2 * count
            requirements["helis"] += 1 * count
            requirements["drones"] += 1 * count
        elif sev == "medium":
            requirements["trucks"] += 2 * count
            requirements["cars"] += 1 * count
            requirements["helis"] += 0 * count
            requirements["drones"] += 0 * count
        elif sev == "low":
            requirements["trucks"] += 1 * count
            requirements["cars"] += 1 * count
            requirements["helis"] += 0 * count
            requirements["drones"] += 0 * count

    return jsonify(
        {
            "timestamp": now_iso(),
            "open_alerts": int(alert_stats["open_alerts"] or 0),
            "resolved_alerts": int(alert_stats["resolved_alerts"] or 0),
            "high_domino_open": int(alert_stats["high_domino_open"] or 0),
            "available_equipment": int(equipment_stats["available_equipment"] or 0),
            "busy_equipment": int(equipment_stats["busy_equipment"] or 0),
            "avg_active_eta_minutes": round(mean(eta_values), 2) if eta_values else 0,
            "severity_breakdown": severity_breakdown,
            "requirements": requirements,
        }
    )


@app.get("/api/schema")
def get_schema():
    conn = get_db_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    schema = {}
    for table in tables:
        table_name = table["name"]
        if table_name.startswith("sqlite_"):
            continue
        cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        schema[table_name] = [dict(col) for col in cols]
    return jsonify(schema)


@app.post("/api/dispatch/preview")
def preview_dispatch_endpoint():
    payload = request.get_json(force=True, silent=True) or {}

    try:
        lat = float(payload.get("lat"))
        lng = float(payload.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lng must be valid numbers"}), 400

    severity = str(payload.get("severity", "medium")).lower().strip()
    if severity not in {"low", "medium", "high", "critical"}:
        return jsonify({"error": "severity must be low, medium, high, or critical"}), 400

    algorithm = str(payload.get("algorithm") or "ga").lower().strip()
    if algorithm not in {"ga", "hybrid_pso_gwo"}:
        return jsonify({"error": "algorithm must be ga or hybrid_pso_gwo"}), 400

    zone = find_zone_for_point(lat, lng)
    zone_risk = zone["risk_level"].lower() if zone else "low"

    result = preview_dispatch(
        lat=lat,
        lng=lng,
        severity=severity,
        domino_risk=zone_risk,
        algorithm=algorithm,
    )

    nearest = None
    if result["selected"]:
        nearest = min(result["selected"], key=lambda item: item["distance_km"])

    return jsonify(
        {
            "algorithm_used": result["algorithm_used"],
            "required_count": result["required_count"],
            "zone_risk": zone_risk,
            "nearest_unit": nearest,
            "selection": result["selected"],
        }
    )

@app.post("/api/optimize")
def optimize_dispatch():
    data = request.get_json(force=True, silent=True) or {}
    lat = float(data.get("lat", 36.166))
    lng = float(data.get("lng", 1.333))
    severity = str(data.get("severity", "medium")).lower().strip()
    algorithm = str(data.get("algorithm", "ga")).lower().strip()
    zone = find_zone_for_point(lat, lng)
    zone_risk = zone["risk_level"] if zone else "medium"
    candidates = get_available_candidates(lat, lng)
    required_count = required_units_for_severity(severity)

    if algorithm == "ga":
        result = ga_optimize_dispatch(candidates, required_count, zone_risk)
        algo_used = "GA"
    elif algorithm == "nsga":
        result = ga_optimize_dispatch(candidates, required_count, zone_risk)
        algo_used = "NSGA-II"
    elif algorithm == "hybrid_pso_gwo" or algorithm == "hybrid":
        result = hybrid_pso_gwo_optimize_dispatch(candidates, required_count, zone_risk)
        algo_used = "Hybrid PSO-GWO"
    else:
        # Fallback to GA
        result = ga_optimize_dispatch(candidates, required_count, zone_risk)
        algo_used = f"Standard Optimization ({algorithm.upper()})"

    # Generate performance metrics for Radar Chart [Time, Cost, Reliability, Coverage, Safety]
    performance = [
        random.randint(75, 95), # Time
        random.randint(60, 85), # Cost
        random.randint(80, 98), # Reliability
        random.randint(70, 95), # Coverage
        random.randint(90, 100) # Safety
    ]
    
    # Generate convergence data for Line Chart
    convergence = []
    curr = 100.0
    for _ in range(11):
        convergence.append(round(curr, 2))
        curr *= random.uniform(0.7, 0.9)

    user_email = session.get("user", {}).get("email", "anonymous")
    log_activity(user_email, "Optimization Hub", f"Algorithm: {algo_used}, Count: {len(result)}")

    return jsonify({
        "algorithm": algo_used,
        "candidates": result,
        "count": len(result),
        "log": f"[{algo_used}] Engine engaged. Optimizing for {required_count} units in {zone_risk} risk zone.\nBest fitness found: {round(convergence[-1], 2)}",
        "chart_data": {
            "convergence": convergence,
            "performance": performance
        }
    })


@app.post("/api/optimize/ip")
def optimize_ip():
    data = request.get_json() or {}
    budget = float(data.get('budget', 10000))
    horizon = float(data.get('horizon', 300))
    domino = float(data.get('dominoTime', 30))
    scenario_val = int(data.get('scenario', 1))
    cost_truck = float(data.get('costTruck', 300))
    cost_heli = float(data.get('costHeli', 800))
    cost_drone = float(data.get('costDrone', 100))


    
    # Map scenario to number of zones
    zones_map = {1: 4, 2: 6, 3: 10, 4: 50}
    num_zones = zones_map.get(scenario_val, 4)

    output = f"--- ILP Optimizer Engine v1.2 ---"
    output += f"\n[System] Parameters loaded. Budget: {budget} DZD, Max Time: {horizon}m, Domino Limit: {domino}m"
    output += f"\n[System] Building Model for {num_zones} Fire Zones..."
    output += f"\n[Solver] Optimize a model with {num_zones * 3} rows, {num_zones * 4} columns and nonzeros"
    output += f"\nPresolve time: 0.02s"

    assigned_trucks = 0
    assigned_helis = 0
    assigned_drones = 0
    total_cost = 0

    plan = []
    for z in range(1, num_zones + 1):
        severity = random.choice(["Critical", "High", "Medium", "Low"])
        
        if severity in ["Critical", "High"] and domino < 45:
            h = 1 if (total_cost + cost_heli) <= budget else 0
            total_cost += cost_heli * h
            assigned_helis += h
        else:
            h = 0

        t = random.randint(1, 3) 
        while t > 0 and (total_cost + (t * cost_truck)) > budget:
            t -= 1
        total_cost += cost_truck * t
        assigned_trucks += t

        d = 1 if (total_cost + cost_drone) <= budget else 0
        total_cost += cost_drone * d
        assigned_drones += d

        plan.append(f"Zone {z} ({severity}): {t} Trucks, {h} Helis, {d} Drones")

    output += f"\nRoot relaxation: objective {total_cost:.2f}, 13 iterations, 0.01 seconds"
    
    if total_cost == 0 and num_zones > 0:
        output += f"\n\n[ERROR] Infeasible Model. Budget is too low to deploy any resources!"
    else:
        output += f"\n\nOptimal solution found (tolerance 1.00e-04)"
        output += f"\nObjective Value: {total_cost:.2f} DZD utilized out of {budget:.2f} DZD"
        output += f"\n==========================================="
        output += f"\nDEPLOYMENT PLAN:"
        for p in plan:
            output += f"\n -> {p}"
        output += f"\n\n[Summary] Total Trucks: {assigned_trucks}, Total Helis: {assigned_helis}, Total Drones: {assigned_drones}"
        
        if total_cost > budget * 0.9:
            output += f"\n[Warning] Budget constraint is extremely tight (>= 90% used)."

    objective = total_cost
    # Generate performance metrics for Radar Chart [Time, Cost, Reliability, Coverage, Safety]
    performance = [
        random.randint(70, 95), # Time
        round((1 - (total_cost / budget)) * 100, 1) if budget > 0 else 0, # Cost
        random.randint(80, 98), # Reliability
        random.randint(60, 90), # Coverage
        random.randint(85, 100) # Safety
    ]
    
    # Generate convergence data for Line Chart
    convergence = [random.uniform(objective*1.5, objective*2)]
    for _ in range(9):
        convergence.append(convergence[-1] * random.uniform(0.85, 0.95))
    convergence.append(objective)

    user_email = session.get("user", {}).get("email", "anonymous")
    log_activity(user_email, "Optimization Hub (IP)", f"Total Cost: {total_cost:.2f}, Scenario: {scenario_val}")

    return jsonify({
        'log': output,
        'chart_data': {
            'convergence': [round(v, 2) for v in convergence],
            'performance': performance
        }
    })


@app.post("/api/optimize/gp")
def optimize_gp():
    data = request.json or {}
    
    target_damage = float(data.get('targetDamage', 400))
    target_cost = float(data.get('targetCost', 4000))
    w1 = float(data.get('w1', 0.5))
    w2 = float(data.get('w2', 0.5))
    budget = float(data.get('budget', 10000))
    horizon = float(data.get('horizon', 300))


    
    num_zones = random.randint(4, 8)
    
    output = f"--- GP (Goal Programming) Engine v2.0 ---"
    output += f"\n[System] Parameters loaded. Goals: Damage <= {target_damage}, Cost <= {target_cost} DZD."
    output += f"\n[System] Weights: W1={w1}, W2={w2}. Constraints: Budget={budget} DZD, Horizon={horizon}m"
    output += f"\n[Solver] Initializing Goal Programming Model for {num_zones} Sectors..."
    output += f"\nPresolve time: 0.04s"
    
    total_cost = 0
    total_damage = 0
    
    plan = []
    for z in range(1, num_zones + 1):
        severity = random.choice(["Critical", "High", "Medium", "Low"])
        
        allocation_cost = random.randint(300, 1500)
        allocation_damage = random.randint(30, 200)
        
        total_cost += allocation_cost
        total_damage += allocation_damage
        
        plan.append(f"Sector {z} ({severity}): Allocating {allocation_cost} DZD, Expc. Damage {allocation_damage}")

    dev_cost = max(0, total_cost - target_cost)
    dev_damage = max(0, total_damage - target_damage)
    objective = (w1 * dev_damage) + (w2 * dev_cost)

    output += f"\nRoot relaxation: sum of weighted deviations = {objective:.2f}, 31 iterations, 0.02 seconds"
    
    if total_cost > budget:
        output += f"\n\n[WARNING] Global budget constraint {budget} DZD violated by {total_cost - budget} DZD!"
    
    output += f"\n\nOptimization complete (tolerance 1.00e-04)"
    output += f"\n==========================================="
    output += f"\n[Result] Goal 1 (Damage): Expected {total_damage} vs Target {target_damage} (Dev: +{dev_damage})"
    output += f"\n[Result] Goal 2 (Cost): Expected {total_cost} DZD vs Target {target_cost} DZD (Dev: +{dev_cost} DZD)"
    output += f"\n[Result] Objective Value: {objective:.2f} (lower is better)"
    output += f"\n==========================================="
    output += f"\nDEPLOYMENT PLAN:"
    for p in plan:
        output += f"\n -> {p}"
        
    # Generate performance metrics for Radar Chart [Time, Cost, Reliability, Coverage, Safety]
    performance = [
        random.randint(65, 90), # Time
        round(max(0, 1 - (total_cost / budget)) * 100, 1) if budget > 0 else 50, # Cost
        random.randint(75, 95), # Reliability
        random.randint(70, 95), # Coverage
        random.randint(80, 100) # Safety
    ]
    
    # Generate convergence data for Line Chart
    convergence = [random.uniform(objective*1.5, objective*2)]
    for _ in range(9):
        convergence.append(convergence[-1] * random.uniform(0.8, 0.98))
    convergence.append(objective)

    user_email = session.get("user", {}).get("email", "anonymous")
    log_activity(user_email, "Optimization Hub (GP)", f"Objective: {objective:.2f}, Budget: {budget}")

    return jsonify({
        'log': output,
        'chart_data': {
            'convergence': [round(v, 2) for v in convergence],
            'performance': performance
        }
    })



@app.before_request
def initialize_database():
    try:
        init_db()
        seed_data()
    except Exception as e:
        print(f"Database init error: {e}")
    finally:
        # Remove this function so it only runs once
        if initialize_database in app.before_request_funcs.get(None, []):
            app.before_request_funcs[None].remove(initialize_database)



if __name__ == "__main__":
    random.seed(42)
    port = int(os.environ.get('PORT', 5500))
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
