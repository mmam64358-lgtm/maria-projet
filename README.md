# Intelligent Fire Incident Management & Dispatch System (maria projet) 🚒⚡

**maria projet** is a full-stack Intelligent Decision Support System (DSS) designed for high-performance fire alert handling, risk analysis, and automatic emergency resource dispatch. It combines a premium glassmorphic dashboard with a robust Flask/PostgreSQL backend powered by AI optimization algorithms.

## 🚀 Key Features

### 🔐 Security & Access Control
- **Role-Based Access Control (RBAC)**: Distinct permissions for `Admin`, `Fireman (Operator)`, and `Citizen`.
- **Identity Management**: Secure authentication integrated with role claims to ensure tactical data integrity.

### 🔥 Intelligent Incident Handling
- **Duplicate Detection Logic**: Automatically identifies redundant reports within a **0.8 km** radius and **10-minute** window to prevent resource waste.
- **Domino Risk Scoring**: Dynamic analysis of potential fire spread (Low, Medium, High) based on environmental data and proximity to sensitive zones.
- **Zone Detection**: Precise haversine-based calculation to identify which tactical zone or forest region is affected.

### 🤖 AI-Driven Dispatch Strategy
The system follows a strict tactical protocol for unit allocation based on incident severity:
- **Low Severity**: Dispatches **2** nearest available units.
- **Medium Severity**: Dispatches **3** units.
- **High Severity**: Dispatches **7** units.
- **Critical Severity**: Dispatches **8** units for maximum containment.
- **Optimization Engines**: Real-time resolution using **Genetic Algorithms (GA)** and **Hybrid PSO-GWO** to find the absolute fastest routes.

### 🛰️ Premium Tactical Dashboard
- **Live GIS Mapping**: Leaflet-powered engine with tactical overlays (Water sources, Risk zones).
- **Mission Pulse**: Real-time telemetry and charts (Chart.js) tracking active missions and unit availability.
- **Tactical Alerts**: Instant audio-visual dispatch notifications for field agents.

---

## 🛠️ Technology Stack

- **Backend**: Python / Flask
- **Database**: **PostgreSQL** (with optimized connection pooling)
- **ORM/Migrations**: SQLAlchemy + Flask-Migrate integration.
- **Frontend**: ES6+ JavaScript, Vanilla CSS3 (Custom Design System), Leaflet.js.
- **Algorithms**: Custom Metaheuristic implementation for resource optimization.

---

## 📂 Project Structure

```text
maria-projet/
├── app.py              # Main Application Logic & API Endpoints
├── static/             # Assets (CSS, JS, Premium Icons)
│   ├── css/            # Design System & Glassmorphism
│   └── js/             # Real-time Map Logic & UI Interactions
├── templates/          # Responsive HTML5 Portals
├── add_units.py        # Database Seeding (Resource Inventory)
├── final_db_seed.py    # Database Seeding (Initial System State)
├── requirements.txt    # Production Dependencies
└── README.md           # Professional Documentation
```

---

## 📦 Setup & Installation (Windows)

1. **Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Database Configuration**:
   - Create a PostgreSQL database: `CREATE DATABASE fire_dispatch_db;`
   - Configure your credentials in the `.env` file:
     `DATABASE_URL=dbname=fire_dispatch_db user=postgres password=YOUR_PASSWORD host=localhost`

4. **Initialize System**:
   ```powershell
   python final_db_seed.py
   ```

5. **Run Server**:
   ```powershell
   python app.py
   ```

---

## 📡 Primary API Endpoints

### Authentication
- `POST /api/login` - Secure session acquisition.
- `GET /logout` - Session termination.

### Tactical Alerts
- `GET /api/alerts` - Retrieve global incident state.
- `POST /api/alerts` - Incident creation (with auto-dispatch trigger).
- `POST /api/alerts/<id>/status` - Tactical status update (Operator/Admin).

### Resource Management
- `GET /api/units` - Real-time unit tracking.
- `GET /api/equipment` - Live inventory monitoring.
- `GET /api/live_inventory` - Detailed equipment breakdown by station.

---
**Developed for Academic Excellence in AI & Emergency Systems**