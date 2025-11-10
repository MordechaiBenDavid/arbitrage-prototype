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
