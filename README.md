# 🛡️ AI-Powered UEBA for Fraud Detection
**Bank of Baroda Hackathon Submission**

---

## 📌 Overview
This project is a **User and Entity Behavior Analytics (UEBA)** platform designed to detect and visualize fraudulent banking transactions in real time.  
It combines **machine learning (Isolation Forest)** with **rule-based anomaly checks** to flag unusual activities, providing a clear and interactive dashboard for monitoring.

- **Backend** → FastAPI + SQLite/Postgres for transaction storage & risk scoring  
- **Simulator** → Continuously streams synthetic transactions to mimic real-world bank traffic  
- **Frontend** → React (Vite + Tailwind) dashboard for anomaly monitoring, CSV export, and risk visualization  

---

## 🏗️ Features
- 🔍 **Anomaly Detection** → Isolation Forest ML + rule-based scoring (impossible travel, new device, large withdrawals, etc.)  
- 📊 **Real-Time Dashboard** → View transactions, anomalies, and risk trends in an interactive React UI  
- ⚡ **Auto Refresh & Search** → Live updates with filters (risk threshold, transaction type, user search)  
- 📥 **CSV Export** → Download transactions/anomalies for audit & reporting  
- 🛠️ **Simulator** → Generates realistic banking transactions across multiple geographies & devices  
- 🗄️ **Backend APIs** → REST endpoints for health, transactions, anomalies, and transaction submission  

---

## 🖼️ Architecture
Simulator → Backend API → Database → Frontend Dashboard
↑ ML + Rules

yaml
Copy code

- **Simulator**: Generates continuous transactions  
- **Backend**: FastAPI service scoring fraud risk & storing in DB  
- **Frontend**: React app with Tailwind, charts, and export tools  

---

## ⚙️ Tech Stack
- **Frontend**: React + Vite + Tailwind + Recharts  
- **Backend**: Python, FastAPI, SQLite/Postgres, scikit-learn  
- **ML**: Isolation Forest for unsupervised anomaly detection  
- **Other**: Node.js, npm, SQLAlchemy, Axios
---
https://github.com/user-attachments/assets/91b4832d-29ac-4705-a4df-0825169e935d

## 🚀 Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/mr-lupin007/CAI-Powered-UEBA-for-Fraud-Detection-BOB-Hackathon-.git
cd CAI-Powered-UEBA-for-Fraud-Detection-BOB-Hackathon-
2. Backend Setup
bash
Copy code
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
uvicorn main:app --reload --port 8000

https://github.com/user-attachments/assets/53d44aad-a41d-408a-89df-61977d92953f


📍 Backend runs on: http://127.0.0.1:8000
📍 API Docs available at: http://127.0.0.1:8000/docs

3. Simulator Setup
Open a new terminal (keep backend running) and run:

bash
Copy code
cd backend
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Mac/Linux

python simulator.py
This starts generating transactions in real time.

4. Frontend Setup
Open another new terminal and run:

bash
Copy code
cd frontend
npm install
npm run dev
📍 Frontend runs on: http://127.0.0.1:5173

📊 Key API Endpoints
GET /api/health → Check backend health

GET /api/transactions?limit=50 → Fetch latest transactions

GET /api/anomalies?min_risk=0.75&limit=20 → Fetch anomalies above risk threshold

POST /api/transaction → Submit new transaction

📂 Project Structure
bash
Copy code
├── backend
│   ├── main.py            # FastAPI backend
│   ├── risk_engine.py     # ML + rules engine
│   ├── simulator.py       # Transaction generator
│   ├── requirements.txt   # Python dependencies
│   └── schema.sql         # DB schema
│
├── frontend
│   ├── src/
│   │   ├── App.jsx        # Main dashboard
│   │   ├── components/    # UI components
│   │   └── apis/api.js    # API calls
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md              # This file
📥 Database
Uses SQLite by default for local demo (auto-created).

Can be switched to PostgreSQL/MySQL easily.

If DB is used → dump can be submitted with:

bash
Copy code
# PostgreSQL dump example
pg_dump -U postgres -d ueba > db_dump.sql
(Make sure pg_dump is installed with PostgreSQL)

🏆 Evaluation Fit
Innovation: AI-powered UEBA + hybrid rules engine

Feasibility: Lightweight FastAPI backend with ready DB + frontend dashboard

Business Potential: Detects fraud in real-time, scalable to core banking

Scalability: Can integrate with live transaction streams & cloud DBs

User Experience: Clean dashboard, filters, auto-refresh, CSV export

📽️ Demo Flow
Start backend → uvicorn main:app --reload --port 8000

Run simulator → python simulator.py

Open frontend → npm run dev

Show judges:

Live transactions streaming

Anomaly detection (rules + ML)

Risk chart visualization

CSV export feature

👥 Team McLaren
Jyotsna arya & Surya shukla
IIT Kanpur | Bank of Baroda Hackathon 2025






