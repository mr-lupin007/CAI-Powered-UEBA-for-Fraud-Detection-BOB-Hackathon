import os, json
import numpy as np, pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import OneHotEncoder
from joblib import dump
from dotenv import load_dotenv
from risk_engine import rules_score, final_risk, build_explanations
from psycopg2.extras import Json
load_dotenv()
DSN = os.getenv("DB_DSN")

def fetch_df():
    conn = psycopg2.connect(DSN, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("""SELECT t.*, u.profile AS user_profile
                   FROM transactions t JOIN users u ON t.user_id=u.id
                   ORDER BY t.ts""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    df = pd.DataFrame(rows)

    # --- CRITICAL: ensure numeric columns are float (Postgres NUMERIC -> Decimal) ---
    if not df.empty:
        df["amount"] = df["amount"].astype(float)
    return df

def feature_df(df: pd.DataFrame):
    # timestamps -> hour of day
    df["hour"] = pd.to_datetime(df["ts"]).dt.tz_localize(None).dt.hour if hasattr(df["ts"].iloc[0], "tzinfo") else pd.to_datetime(df["ts"]).dt.hour

    # per-user median amount (float)
    med = df.groupby("user_id")["amount"].transform(lambda s: float(np.median(s.astype(float))) if len(s) else 1.0)
    med = med.replace(0, 1.0)
    df["amt_norm"] = (df["amount"].astype(float) / med.astype(float)).astype(float)

    # one-hot encode type, country
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_cat = enc.fit_transform(df[["type","country"]])
    X_num = df[["amt_norm","hour"]].to_numpy(dtype=float)
    X_all = np.hstack([X_num, X_cat])
    return df, X_all, enc

def fit_model(X):
    model = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
    model.fit(X)
    return model

def update_profiles(df):
    if df.empty: return
    df["hour"] = pd.to_datetime(df["ts"]).dt.hour

    # per-user medians + top countries
    agg = df.groupby("user_id").agg(
        avg_amount=("amount","median"),
        ctries=("country", lambda s: list(pd.Series(s).value_counts().head(3).index)),
    ).reset_index()

    # per-user per-hour median -> dict of hour->median
    hour_med = df.groupby(["user_id","hour"])["amount"].median().reset_index()
    hour_maps = {uid: {int(h): float(m) for _,h,m in rows.to_numpy()}
                 for uid, rows in hour_med.groupby("user_id")}

    conn = psycopg2.connect(DSN); cur = conn.cursor()
    for _, r in agg.iterrows():
        uid = r["user_id"]
        cur.execute(
            """UPDATE users
               SET profile = jsonb_set(
                   jsonb_set(
                       jsonb_set(COALESCE(profile,'{}'::jsonb), '{avg_amount}', to_jsonb(%s::numeric), true),
                       '{usual_countries}', %s::jsonb, true
                   ),
                   '{hourly_median}', %s::jsonb, true
               )
               WHERE id=%s""",
            (float(r["avg_amount"]), Json(r["ctries"]), Json(hour_maps.get(uid, {})), uid)
        )
    conn.commit(); cur.close(); conn.close()

def write_back(df):
    conn = psycopg2.connect(DSN); cur = conn.cursor()
    for _, r in df.iterrows():
        cur.execute(
            """UPDATE transactions SET
                 anomaly_score=%s, rules_score=%s, final_risk=%s,
                 anomaly_flag=%s, explanations=%s
               WHERE id=%s""",
            (float(r["anomaly_score"]), float(r["rules_score"]), float(r["final_risk"]),
             int(r["anomaly_flag"]), json.dumps(list(r["explanations"])), r["id"])
        )
    conn.commit(); cur.close(); conn.close()

if __name__ == "__main__":
    df = fetch_df()
    if df.empty:
        raise SystemExit("No transactions found. Run seed_data.py first.")

    update_profiles(df)
    df, X_all, enc = feature_df(df)
    model = fit_model(X_all)

    # IsolationForest outputs
    df["anomaly_score"] = model.decision_function(X_all)
    df["anomaly_flag"]  = model.predict(X_all)

    # Hybrid risk + explanations
    rules, risks, exps = [], [], []
    for _, row in df.iterrows():
        prof = row["user_profile"] or {}
        tx = dict(amount=float(row["amount"]),
                  country=row["country"], type=row["type"],
                  hour=int(row["hour"]), ts=str(row["ts"]),
                  device_fingerprint=row["device_fingerprint"])
        rs = rules_score(tx, prof); rules.append(rs)
        risks.append(final_risk(df.loc[_,"anomaly_score"], rs))
        exps.append(build_explanations(tx, prof, df.loc[_,"anomaly_score"]))
    df["rules_score"] = rules; df["final_risk"] = risks; df["explanations"] = exps

    write_back(df)
    dump(model, "anomaly_model.pkl"); dump(enc, "enc.pkl")
    print("Model trained, DB updated, model+encoder saved.")
