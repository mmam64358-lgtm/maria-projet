# Multi-Objective Optimization for Firefighting Under Domino Effects (maria projet) 🚒⚡

**maria projet** is a sophisticated Intelligent Decision Support System (DSS) developed for the Chlef region. It addresses the critical multi-objective optimization challenge of firefighting resource allocation, particularly in scenarios involving **domino effects** and cascade failures across interconnected zones.

## 🔬 Scientific Abstract

Efficient allocation of firefighting resources is a complex problem involving conflicting objectives: **Cost Minimization**, **Response Time Optimization**, and **Fire Containment Effectiveness**. This project implements and evaluates advanced metaheuristic approaches—Genetic Algorithms (GA) and a novel Hybrid Particle Swarm Optimization-Grey Wolf Optimizer (PSO-GWO)—to provide real-time, near-optimal deployment strategies in high-pressure emergency scenarios.

---

## 🤖 Optimization Metaheuristics

### 1. Genetic Algorithm (GA / NSGA-II Inspired)
The system evolves a population of potential dispatch plans using evolutionary operators:
- **Two-Point Crossover**: Preserves contiguous zone-resource blocks to maintain coherent sub-plans.
- **Uniform Integer Mutation**: Enables global exploration and prevents premature convergence into local optima.
- **Elitist Selection**: Ensures that the highest-quality non-dominated solutions are preserved across generations.
- **Objective**: Finds a Pareto-optimal front balancing operational expenditure against risk mitigation.

### 2. Hybrid PSO-GWO Algorithm
A high-performance hybrid model combining the strengths of two swarm-based paradigms:
- **PSO Component**: Leverages velocity-based momentum and global communication to explore the search space.
- **GWO Component**: Implements a hierarchical leadership structure (Alpha, Beta, Delta wolves) for refined local exploitation.
- **Synergy**: PSO provides the exploration breadth while GWO ensures rapid convergence (typically within 10-15 iterations), making it ideal for real-time operational response.

### 3. Domino Effect Modeling & Cascade Propagation
The system explicitly models the temporal dynamics of fire spread:
- **Threshold-Based Ignition**: If a fire is not contained within a specific time window ($\Delta z$), it triggers a cascade to adjacent zones.
- **Adjacency Logic**: Uses Haversine-based spatial analysis to define neighbors ($N(z)$) and propagate fire start times ($t_{start}$) across the network.

---

## 🔐 System Architecture & Security

- **Backend**: Flask-powered API handling complex mathematical formulations.
- **Database**: **PostgreSQL** for high-integrity tactical data storage and role claims.
- **Security**: Environment isolation using `.env` for credentials and server-side RBAC (Role-Based Access Control) to protect sensitive command interfaces.
- **GIS Integration**: Leaflet.js engine for real-time spatial visualization of incident propagation and unit telemetry.

---

## 📦 Technical Setup & Execution

1. **Environment Initialization**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Strategic Database Seeding**:
   ```powershell
   python final_db_seed.py  # Populates the PostgreSQL schema with tactical assets
   ```

3. **Engine Launch**:
   ```powershell
   python app.py
   ```

---

## 📊 Performance Analytics
The **Optimization Hub** provides:
- **Convergence Tracking**: Monitoring how fast the hybrid solver reaches a stable solution.
- **Performance Radar**: Visualizing the trade-offs between Cost, Time, Safety, and Reliability.
- **Tactical Logs**: Detailed execution traces of the AI decision-making process.

---
**Developed for Academic Research & Emergency Response Practice**
**Maintained by mmam64358-lgtm**