import os
import json
import pathlib
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel
from dotenv import load_dotenv

from db import get_conn
from risk_engine import advanced_rules_score, final_risk, build_explanations
from pydantic import BaseModel as _BM

# -------------------------------------------------------------------
# Env & model load
# -------------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY", "hackathon-secret")

# Friendly check: tell the user to train first
if not (pathlib.Path("anomaly_model.pkl").exists() and pathlib.Path("enc.pkl").exists()):
    raise RuntimeError(
        "Model files not found. Run:  python seed_data.py  &&  python train_model.py  (in backend dir)"
    )

MODEL = load("anomaly_model.pkl")
ENC = load("enc.pkl")

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(title="UEBA Fraud API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def require_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

# -------------------------------------------------------------------
# Schemas
# -------------------------------------------------------------------
class TxnIn(BaseModel):
    user_id: str
    amount: float
    type: str
    country: str
    device_fingerprint: Optional[str] = None
    ip: Optional[str] = None
    ts: Optional[str] = None  # optional client-provided timestamp (unused server-side)

# -------------------------------------------------------------------
# Health & simple list endpoints
# -------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/users")
def users(limit: int = 20):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email, country, created_at FROM users ORDER BY created_at DESC LIMIT %s",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return {"users": rows}

@app.get("/api/transactions")
def transactions(limit: int = 100):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """SELECT t.id, u.name AS user_name, t.user_id, t.ts, t.amount, t.type, t.country,
                  t.final_risk, t.explanations, t.anomaly_score, t.rules_score
           FROM transactions t JOIN users u ON t.user_id = u.id
           ORDER BY t.ts DESC
           LIMIT %s""",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return {"transactions": rows}

@app.get("/api/anomalies")
def anomalies(min_risk: float = Query(0.5, ge=0, le=1), limit: int = 100):
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """SELECT t.id, u.name AS user_name, t.user_id, t.ts, t.amount, t.type, t.country,
                  t.final_risk, t.explanations
           FROM transactions t JOIN users u ON t.user_id = u.id
           WHERE t.final_risk >= %s
           ORDER BY t.final_risk DESC, t.ts DESC
           LIMIT %s""",
        (min_risk, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return {"anomalies": rows}

# -------------------------------------------------------------------
# Feature builder (2-D array for sklearn)
# -------------------------------------------------------------------
def featurize(row: dict):
    """
    row keys: user_id, amount, type, country, hour
    Returns a single 2-D feature row (shape: 1 x n_features).
    """
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY amount) AS med
           FROM transactions
           WHERE user_id=%s AND ts > now() - interval '30 days'""",
        (row["user_id"],)
    )
    r = cur.fetchone()
    conn.close()
    med = float((r or {}).get("med") or 1.0)

    import numpy as np
    num = np.array([[row["amount"] / med, row["hour"]]], dtype=float)  # (1,2)
    cats = ENC.transform([[row["type"], row["country"]]])              # (1,k)
    X = np.hstack([num, cats])                                         # (1, 2+k)
    return X

# -------------------------------------------------------------------
# Context builder for advanced rules
# -------------------------------------------------------------------
from datetime import timezone

def build_ctx(user_id: str, device_fp: str | None, now_dt: datetime, country: str | None):
    conn = get_conn(); cur = conn.cursor()

    # previous tx for user
    cur.execute(
        """SELECT ts, country
           FROM transactions
           WHERE user_id=%s
           ORDER BY ts DESC
           LIMIT 1""",
        (user_id,)
    )
    r = cur.fetchone() or {}
    prev_ts = r.get("ts")
    prev_country = r.get("country")

    # >>> Normalize timestamps so arithmetic never mixes aware/naive <<<
    # we use naive UTC everywhere in the rules
    if prev_ts is not None and getattr(prev_ts, "tzinfo", None) is not None:
        prev_ts = prev_ts.astimezone(timezone.utc).replace(tzinfo=None)
    if getattr(now_dt, "tzinfo", None) is not None:
        now_dt = now_dt.astimezone(timezone.utc).replace(tzinfo=None)
    # <<< done >>>

    # velocity: last 10 minutes
    cur.execute(
        """SELECT COUNT(*) AS c
           FROM transactions
           WHERE user_id=%s AND ts > now() - interval '10 minutes'""",
        (user_id,)
    )
    recent_cnt_10m = int(cur.fetchone().get("c", 0))

    # value burst: transfers over 30 minutes
    cur.execute(
        """SELECT COALESCE(SUM(amount),0) AS s
           FROM transactions
           WHERE user_id=%s AND type='transfer' AND ts > now() - interval '30 minutes'""",
        (user_id,)
    )
    recent_sum_transfers_30m = float(cur.fetchone().get("s", 0.0))

    # device country history (recent 90d)
    dev_countries = set()
    if device_fp:
        cur.execute(
            """SELECT DISTINCT country
               FROM transactions
               WHERE device_fingerprint=%s AND country IS NOT NULL
                     AND ts > now() - interval '90 days'
               LIMIT 20""",
            (device_fp,)
        )
        dev_countries = {row["country"] for row in cur.fetchall()}

    conn.close()
    return {
        "prev_country": prev_country,
        "prev_ts": prev_ts,  # now naive UTC (or None)
        "recent_cnt_10m": recent_cnt_10m,
        "recent_sum_transfers_30m": recent_sum_transfers_30m,
        "device_seen_countries": list(dev_countries),
    }


# -------------------------------------------------------------------
# Score + insert endpoint
# -------------------------------------------------------------------
@app.post("/api/transaction")
def score_and_insert(tx: TxnIn, _: None = Depends(require_key)):
    """
    Score a new transaction and insert it.
    Uses advanced rules with contextual signals, combines with IForest.
    """
    ts_dt = datetime.utcnow()

    # 1) get user profile
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT profile FROM users WHERE id=%s", (tx.user_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="User not found")
        prof = r["profile"] or {}

        # 2) features (2-D array for sklearn)
        hour = ts_dt.hour
        row = {
            "user_id": tx.user_id,
            "amount": float(tx.amount),
            "type": tx.type,
            "country": tx.country,
            "hour": int(hour),
        }
        X = featurize(row)  # shape (1, n_features)

        # 3) model & rules
        anom = float(MODEL.decision_function(X)[0])
        pred = int(MODEL.predict(X)[0])  # -1/1 -> already mapped by IF
        ctx = build_ctx(tx.user_id, tx.device_fingerprint, ts_dt, tx.country)

        rules_s, extra_exps = advanced_rules_score(
            {**row, "ts": ts_dt, "device_fingerprint": tx.device_fingerprint},
            prof,
            ctx
        )
        risk = final_risk(anom, rules_s)

        base_exps = build_explanations(
            {**row, "ts": ts_dt.isoformat(), "device_fingerprint": tx.device_fingerprint},
            prof,
            anom
        )
        # merge & de-duplicate explanations
        exps = list(dict.fromkeys(list(base_exps) + list(extra_exps)))

        # 4) insert transaction, return id
        cur.execute(
            """
            INSERT INTO transactions
              (user_id, ts, amount, type, country, device_fingerprint, ip,
               anomaly_score, rules_score, final_risk, anomaly_flag, explanations)
            VALUES
              (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                tx.user_id, ts_dt, float(tx.amount), tx.type, tx.country,
                tx.device_fingerprint, tx.ip,
                anom, rules_s, risk, pred, json.dumps(exps),
            ),
        )
        row_id = cur.fetchone()          # one fetch only
        tid = row_id["id"]               # RealDictCursor returns dict
        conn.commit()

        return {"id": str(tid), "final_risk": risk, "explanations": exps, "anomaly": risk >= 0.75}

    except HTTPException:
        raise
    except Exception as e:
        # bubble a readable error to client + log
        print("ERROR in /api/transaction:", repr(e))
        raise HTTPException(status_code=500, detail=f"server_error: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
       
        

class ActionIn(_BM):
    user_id: str
    txn_id: str | None = None
    action: str  # LOCK_ACCOUNT | STEP_UP | FALSE_POSITIVE
    note: str | None = None

@app.post("/api/actions")
def create_action(body: ActionIn, _: None = Depends(require_key)):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO actions (user_id, txn_id, action, note, actor)
                   VALUES (%s,%s,%s,%s,%s) RETURNING id, ts""",
                (body.user_id, body.txn_id, body.action, body.note, "analyst"))
    row = cur.fetchone(); conn.commit(); conn.close()
    return {"ok": True, "id": row["id"], "ts": row["ts"]}

@app.get("/api/actions")
def list_actions(user_id: str, limit: int = 20):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""SELECT id, user_id, txn_id, action, note, actor, ts
                   FROM actions WHERE user_id=%s ORDER BY ts DESC LIMIT %s""",
                (user_id, limit))
    rows = cur.fetchall(); conn.close()
    return {"actions": rows}
# --- NEW: light catalog endpoints for filters ---
@app.get("/api/catalog")
def catalog():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT country FROM transactions ORDER BY 1")
    countries = [r["country"] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT type FROM transactions ORDER BY 1")
    types = [r["type"] for r in cur.fetchall()]
    cur.execute("SELECT id, name FROM users ORDER BY name")
    users = cur.fetchall()
    conn.close()
    return {"countries": countries, "types": types, "users": users}

# --- NEW: metrics for chart (risk over time) ---
@app.get("/api/metrics/risk_over_time")
def risk_over_time(
    minutes: int = Query(60, ge=5, le=24*60),
    bucket_sec: int = Query(300, ge=60, le=3600),  # 5 min default
    user_id: str | None = None,
    ttype: str | None = None,
    country: str | None = None,
    min_risk: float = 0.0,
):
    conn = get_conn(); cur = conn.cursor()
    where = ["ts > now() - interval %s"]
    params = [f"{minutes} minutes"]
    if user_id: where.append("user_id=%s"); params.append(user_id)
    if ttype:   where.append("type=%s");    params.append(ttype)
    if country: where.append("country=%s"); params.append(country)
    if min_risk: where.append("final_risk >= %s"); params.append(min_risk)

    # bucket by N seconds
    cur.execute(f"""
      WITH b AS (
        SELECT date_trunc('second', ts) - mod(extract(epoch from ts)::int, %s) * interval '1 second' AS bucket,
               final_risk
        FROM transactions
        WHERE {" AND ".join(where)}
      )
      SELECT bucket, avg(final_risk) AS avg_risk, count(*) AS n
      FROM b
      GROUP BY bucket
      ORDER BY bucket
    """, [bucket_sec, *params])
    rows = cur.fetchall(); conn.close()
    return {"points": rows}

# --- NEW: paged transactions with filters (for tables) ---
@app.get("/api/transactions/search")
@app.get("/api/transactions/search")
def tx_search(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str | None = None,
    ttype: str | None = None,
    country: str | None = None,
    min_risk: float = 0.0,
):
    conn = get_conn(); cur = conn.cursor()

    where = ["1=1"]
    params = []
    if user_id:
        where.append("t.user_id=%s"); params.append(user_id)
    if ttype:
        where.append("t.type=%s"); params.append(ttype)
    if country:
        where.append("t.country=%s"); params.append(country)
    if min_risk:
        where.append("t.final_risk >= %s"); params.append(min_risk)

    where_clause = " AND ".join(where)

    # rows
    sql_rows = (
        "SELECT t.id, u.name as user_name, t.user_id, t.ts, t.amount, t.type, t.country, "
        "       t.final_risk, t.explanations, t.anomaly_score, t.rules_score "
        "FROM transactions t JOIN users u ON t.user_id=u.id "
        f"WHERE {where_clause} "
        "ORDER BY t.ts DESC "
        "LIMIT %s OFFSET %s"
    )
    cur.execute(sql_rows, [*params, limit, offset])
    rows = cur.fetchall()

    # total
    sql_total = f"SELECT count(*) AS c FROM transactions t WHERE {where_clause}"
    cur.execute(sql_total, params)
    total = int(cur.fetchone()["c"])

    conn.close()
    return {"rows": rows, "total": total}


# --- NEW: transaction detail by id (for drill-down) ---
@app.get("/api/transaction/{tx_id}")
def tx_detail(tx_id: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
      SELECT t.*, u.name as user_name
      FROM transactions t JOIN users u ON t.user_id=u.id
      WHERE t.id=%s
    """, (tx_id,))
    r = cur.fetchone(); conn.close()
    if not r: raise HTTPException(404, "Not found")
    return r

# --- NEW: CSV export of anomalies for demo handoff ---
from fastapi.responses import StreamingResponse
import io, csv

@app.get("/api/export/anomalies.csv")
def export_anoms(min_risk: float = 0.75):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
      SELECT t.ts, u.name as user_name, t.amount, t.type, t.country,
             t.final_risk, t.anomaly_score, t.rules_score, t.explanations
      FROM transactions t JOIN users u ON t.user_id=u.id
      WHERE t.final_risk >= %s
      ORDER BY t.final_risk DESC, t.ts DESC
      LIMIT 1000
    """, (min_risk,))
    rows = cur.fetchall(); conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ts","user","amount","type","country","final_risk","anom","rules","explanations"])
    for r in rows:
        writer.writerow([r["ts"], r["user_name"], r["amount"], r["type"], r["country"],
                         r["final_risk"], r["anomaly_score"], r["rules_score"],
                         "; ".join(r.get("explanations", [])) if isinstance(r.get("explanations"), list) else r.get("explanations")])
    buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=anomalies.csv"})

