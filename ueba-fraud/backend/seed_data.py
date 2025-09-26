import os, random, math
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json
from faker import Faker
from dotenv import load_dotenv
load_dotenv()

DSN = os.getenv("DB_DSN")
fake = Faker()

TX_TYPES = ['payment','withdrawal','deposit','transfer']
COUNTRIES = ['IN','US','GB','DE','SG','JP','FR','AE','RU','BR']

def connect():
    return psycopg2.connect(DSN)

def create_users(cur, n=60):
    users = []
    for _ in range(n):
        name = fake.name()
        email = fake.unique.email()
        home = random.choice(['IN','IN','IN','US','GB','SG'])
        profile = {"avg_amount": 0, "usual_countries":[home], "usual_devices":[], "usual_hours":[8,22]}
        cur.execute(
            "INSERT INTO users (name,email,country,profile) VALUES (%s,%s,%s,%s) RETURNING id",
            (name, email, home, Json(profile))
        )
        users.append(cur.fetchone()[0])
    return users

def gaussian_amount(base):
    return max(5.0, random.lognormvariate(math.log(max(base,1.0)), 0.6))

def create_transactions(cur, users, days=60):
    now = datetime.utcnow()
    frauds = 0
    for uid in users:
        base = random.uniform(20, 200)
        devices = [fake.sha1()[:8] for _ in range(random.randint(1,3))]
        cur.execute(
            "UPDATE users SET profile = jsonb_set(COALESCE(profile,'{}'::jsonb), '{usual_devices}', %s::jsonb, true) WHERE id=%s",
            (Json(devices), uid)
        )
        for _ in range(random.randint(80,140)):
            delta = timedelta(days=random.random()*days, hours=random.randint(0,23), minutes=random.randint(0,59))
            ts = now - delta
            ttype = random.choice(TX_TYPES)
            amount = round(gaussian_amount(base), 2)
            ctry = random.choice(['IN','US','GB','SG'])
            device = random.choice(devices)
            ip = fake.ipv4_public()
            is_fraud = False
            if random.random() < 0.015:
                is_fraud = True
                amount = round(base * random.uniform(6,15), 2)
                ctry = random.choice(list(set(COUNTRIES) - set([ctry])))
                hour = random.choice(list(range(0,5)) + [23])
                ts = ts.replace(hour=hour)
            cur.execute(
                """INSERT INTO transactions (user_id, ts, amount, type, country, device_fingerprint, ip, is_fraud)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (uid, ts, amount, ttype, ctry, device, ip, is_fraud)
            )
            if is_fraud:
                frauds += 1
    return frauds

if __name__ == "__main__":
    conn = connect(); conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DELETE FROM actions; DELETE FROM transactions; DELETE FROM users;")
    users = create_users(cur, n=60)
    frauds = create_transactions(cur, users)
    print(f"Seeded {len(users)} users; injected ~{frauds} fraud txns.")
    cur.close(); conn.close()
