# maria projet - FireSafe AI Tactical Dashboard 🚒⚡

**maria projet** is a sophisticated Emergency Decision Support System (DSS) designed for the Chlef region. It leverages AI-driven dispatch algorithms and real-time GIS mapping to optimize response times and resource allocation during critical fire incidents.

## 🚀 Key Features

- **Tactical Mission Center**: Real-time dashboard for firemen with pulsing emergency alerts and tactical audio notifications.
- **AI Optimization Hub**: Advanced dispatching using **Genetic Algorithms (GA)** and **Hybrid PSO-GWO** to find the most efficient resource allocation.
- **Intelligent Alert Handling**: 
    - **Duplicate Detection**: Identifies nearby reports to prevent redundant dispatches.
    - **Domino Risk Analysis**: Evaluates potential fire spread to sensitive areas.
- **Dynamic GIS Mapping**: Integrated Leaflet.js maps with multi-layer tactical data (Units, Incidents, Water Sources, Risk Zones).
- **Security Directory**: Role-based access control (Admin, Agent, Citizen) with secure session management.

## 🛠️ Tech Stack

- **Backend**: Python / Flask
- **Database**: **PostgreSQL** (High-performance relational storage)
- **Frontend**: ES6+ JavaScript, Vanilla CSS3 (Premium Glassmorphism), Leaflet.js
- **Charts**: Chart.js for real-time mission telemetry

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mmam64358-lgtm/maria-projet.git
   cd maria-projet
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Database Configuration**:
   Ensure PostgreSQL is running and update your credentials in the `.env` file:
   `DATABASE_URL=dbname=memoire_db user=postgres password=YOUR_PASSWORD host=localhost`

4. **Initialize System**:
   ```bash
   python final_db_seed.py
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```

## 🔒 Security & Best Practices

The system is built with professional security standards to ensure tactical data integrity:
- **Environment Isolation**: Sensitive credentials (PostgreSQL passwords, API keys) are strictly isolated in a `.env` file and excluded from version control via `.gitignore`.
- **Role-Based Security**: Access to Admin and Fireman dashboards is protected by strict server-side role validation.
- **Session Protection**: Flask sessions are cryptographically signed using a unique secret key to prevent session hijacking.
- **Data Integrity**: All PostgreSQL queries use parameterized inputs to protect against SQL injection.

---
**Developed by mmam64358-lgtm**