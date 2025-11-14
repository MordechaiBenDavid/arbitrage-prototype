<<<<<<< HEAD
# 🧠 API Hop Arbitrage Prototype

This project is a **working FastAPI app** that simulates an “API-hopping” process — where financed inventory moves across multiple systems (METRC → POS → Logistics → Payment → PMSI Registry).  

It’s a lightweight prototype that demonstrates how an asset can be tracked and logged across mock APIs, similar to how a real lien-tracking or arbitrage system would work.

---

## ⚙️ 1. Install and Run the App

### 🧩 Requirements
- Python 3.9 or higher
- Git

### 🪄 Setup (first time)

Open your terminal and run these commands:

```bash
# 1. Clone the repository
git clone https://github.com/MordechaiBenDavid/arbitrage-prototype.git

# 2. Enter the folder
cd arbitrage-prototype

# 3. Create a virtual environment
python3 -m venv venv

# 4. Activate it
source venv/bin/activate     # Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
=======
# SKU Lifecycle Tracker

Modern stack for tracing a product's journey from production to consumer using FastAPI, Postgres, Redis/RQ, OpenSearch, and a Next.js dashboard.

## Stack Overview

- **Backend:** Python 3.11, FastAPI, SQLModel, JWT-ready auth hooks
- **Database:** PostgreSQL (swap in TimescaleDB later for time-series optimizations)
- **Async jobs:** Redis + RQ worker scaffold for connector ingestion
- **Search:** OpenSearch container ready for SKU identity/event indexing
- **Frontend:** Next.js (React + TypeScript) single-page dashboard
- **Infra:** Docker + docker-compose wiring backend, db, redis, search, and frontend

## Getting Started

1. Copy env vars: `cp backend/.env.example backend/.env` and edit secrets.
2. Build + run: `docker compose up --build`.
3. Backend docs live at http://localhost:8000/docs, frontend at http://localhost:3000.

### Database migrations

Use SQLModel/Alembic (not wired yet) to evolve schema. A placeholder `init_db()` call auto-creates tables for local prototyping.

### Async ingestion

`backend/app/worker.py` holds an RQ worker entrypoint bound to the `ingestion` queue—extend with connectors that pull from manufacturing ERPs, carriers, ecommerce APIs, etc.

### Frontend

The Next.js app ships with:
- SKU search (temporary Postgres `ILIKE` search until OpenSearch sync is implemented)
- Timeline view showing inferred status + last known location

## Next Steps

- Finish auth (JWT issuing/verification + role policies).
- Implement OpenSearch indexing + dedicated `/search` resolver.
- Add Alembic migrations + TimescaleDB hypertables for `sku_events`.
- Wire ingestion connectors into Redis queues and persist normalized events.
- Harden deployment (Render/Fly deploy files, CI/CD, monitoring).
>>>>>>> dfe725e (project base)
