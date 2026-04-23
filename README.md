# maria projet - FireSafe AI Tactical Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)](https://flask.palletsprojects.com/)

**maria projet** is a sophisticated Fire & Emergency Management System designed for tactical coordination and citizen reporting. It leverages AI-driven dispatch algorithms and real-time GIS mapping to optimize response times and resource allocation during critical fire incidents.

## 🚀 Key Features

- **Tactical Mission Center**: Real-time dashboard for firemen with pulsing emergency alerts and audio notifications.
- **Citizen Reporting Portal**: Simplified gateway for public emergency reports with precise GPS targeting.
- **Admin Control Center**: Comprehensive hub for unit deployment, incident logging, and system analysis.
- **AI Optimization Hub**: Advanced algorithms (Genetic Algorithm & Hybrid PSO-GWO) for optimal resource routing.
- **Dynamic GIS Mapping**: Integrated Leaflet.js maps with multi-layer tactical data (Units, Incidents, Water Sources, Risk Zones).
- **Security Directory**: Role-based access control (Admin, Agent, Citizen) with secure authentication.

## 🛠️ Tech Stack

- **Backend**: Python / Flask
- **Frontend**: HTML5, Vanilla CSS3 (Premium Glassmorphism), Javascript (ES6+)
- **Database**: SQLite3 (Scalable for production)
- **Mapping**: Leaflet.js / OpenStreetMap
- **Charts**: Chart.js for mission telemetry
- **Icons**: FontAwesome 6

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/maria-projet.git
   cd maria-projet
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**:
   ```bash
   python add_units.py  # Seed initial units and equipment
   ```

5. **Run the Application**:
   ```bash
   python app.py
   ```

## 📸 Screenshots

*(Add your tactical dashboard screenshots here)*

## 🎓 Academic Thesis
This project was developed as part of a Master's Thesis focusing on AI-integrated emergency response systems.

---
**Developed by Hamza Zourkane**