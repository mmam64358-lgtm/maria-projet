# maria projet - FireSafe AI Tactical Dashboard 🚒⚡

**maria projet** is an advanced Emergency Decision Support System (DSS) designed to optimize fire response coordination in the Chlef region. It integrates real-time GIS mapping with cutting-edge Metaheuristic Optimization algorithms to minimize response times and maximize resource efficiency.

## 🌟 Project Core Logic (Architectural Overview)

The system operates on a tri-portal architecture designed for seamless coordination between the public and emergency services:

### 1. Incident Acquisition (Citizen Portal)
- **Geographic Reporting**: Citizens can pin precise fire locations on an interactive Leaflet map.
- **Risk Assessment**: Data such as fire severity and affected area are captured to feed the optimization engine.

### 2. Intelligent Dispatch Engine (The AI Core)
Once an incident is reported, the system executes one of two optimization models to assign resources:
- **Genetic Algorithm (GA)**: Evolves a population of potential dispatch solutions to find the one with the lowest "Cost Function" (Time + Resource Exhaustion).
- **Hybrid PSO-GWO (Particle Swarm & Grey Wolf Optimization)**: A high-performance hybrid model that balances exploration and exploitation to find near-optimal dispatch units in milliseconds, even for complex multi-unit scenarios.

### 3. Tactical Response (Fireman Terminal)
- **Live Mission Feed**: Firemen receive instant tactical dispatches with audio-visual alerts (Tactical Beeps & Pulsing UI).
- **Status Synchronization**: Field agents update mission status (Arrived -> Extinguished) in real-time, which updates the global resource availability.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.9+ / Flask Framework
- **Database**: **PostgreSQL** (Managed via `psycopg2` with an optimized connection wrapper).
- **Frontend**: 
  - **Styles**: Premium Dark-themed Glassmorphism (Vanilla CSS3).
  - **Logic**: ES6 JavaScript with Real-time Polling.
  - **Maps**: Leaflet.js with OSM integration.
  - **Charts**: Chart.js for mission telemetry.
- **Auth**: Secure OAuth2 / Google Integration for identity management.

---

## 💾 Database Configuration (PostgreSQL)

The system is configured to connect to a PostgreSQL database. 
- **Default Connection String**: `dbname=memoire_db user=postgres password=maria123 host=localhost`
- **Configuration**: Managed via the `.env` file under the `DATABASE_URL` variable.

## 🚀 Installation & Deployment

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/mmam64358-lgtm/maria-projet.git
   cd maria-projet
   python -m venv .venv
   pip install -r requirements.txt
   ```

2. **Database Migration**:
   ```bash
   python final_db_seed.py  # Seeds the PostgreSQL tables and initial data
   ```

3. **Launch**:
   ```bash
   python app.py
   ```

---

## 🎯 Optimization Metrics
The project tracks and visualizes:
- **ETA (Estimated Time of Arrival)** optimization.
- **Resource Depletion Ratios** across 10+ Chlef fire stations.
- **Algorithm Convergence** (GA vs. PSO-GWO performance tracking).

---
**Maintained by mmam64358-lgtm**