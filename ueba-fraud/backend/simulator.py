import os, time, random, json, argparse
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("SIM_API_URL", "http://127.0.0.1:8000/api/transaction")
API_KEY = os.getenv("API_KEY", "hackathon-secret")
DSN = os.getenv("DB_DSN")

TX_TYPES   = ["payment", "withdrawal", "deposit", "transfer"]
SAFE_CTRY  = ["IN", "US", "GB", "SG"]
SPICY_CTRY = ["RU", "DE", "AE", "FR", "JP", "BR"]   # used for risky cases

def pick_user_ids(limit=100):
    conn = psycopg2.connect(DSN, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users ORDER BY created_at DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [r["id"] for r in rows]

def make_tx(user_id, high_risk=False):
    base = random.uniform(20, 200)
    amount = round(base * (random.uniform(0.5, 2.0) if not high_risk else random.uniform(6.0, 15.0)), 2)
    return {
        "user_id": str(user_id),
        "amount": float(amount),
        "type": random.choice(TX_TYPES),
        "country": random.choice(SPICY_CTRY if high_risk else SAFE_CTRY),
        "device_fingerprint": f"dev-{random.randint(1000,9999)}",
    }

def send_tx(payload, timeout=8):
    try:
        r = requests.post(
            API,
            headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=timeout,
        )
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, {"text": r.text[:200]}
    except Exception as e:
        return 0, {"error": repr(e)}

def run(rate_per_sec=0.7, fraud_rate=0.12, burst=1):
    users = pick_user_ids(200)
    if not users:
        print("No users found. Run seed_data.py first."); return
    print(f"[{datetime.utcnow().isoformat()}] Simulator: {len(users)} users loaded | "
          f"rate={rate_per_sec}/sec, fraud_rate={fraud_rate}, burst={burst}")
    sleep = 1.0 / max(rate_per_sec, 0.01)
    i = 0
    while True:
        i += 1
        for _ in range(burst):
            uid = random.choice(users)
            risky = (random.random() < fraud_rate)
            payload = make_tx(uid, high_risk=risky)
            code, data = send_tx(payload)
            risk = data.get("final_risk")
            anomaly = data.get("anomaly")
            tag = "HI" if risky else "ok"
            print(f"{i:05d} [{tag}] ? {payload}  ? ({code}) risk={risk} anomaly={anomaly} :: {str(data)[:120]}")
        time.sleep(random.uniform(0.6*sleep, 1.4*sleep))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="UEBA live transaction simulator")
    p.add_argument("--rate", type=float, default=0.7, help="events per second (default 0.7)")
    p.add_argument("--fraud", type=float, default=0.12, help="probability a tx is high-risk (default 0.12)")
    p.add_argument("--burst", type=int, default=1, help="how many tx per tick (default 1)")
    args = p.parse_args()
    run(rate_per_sec=args.rate, fraud_rate=args.fraud, burst=args.burst)
