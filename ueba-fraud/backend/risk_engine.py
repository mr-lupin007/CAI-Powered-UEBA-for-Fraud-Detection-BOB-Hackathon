# -*- coding: utf-8 -*-
import math
from datetime import datetime, timezone

# --- coarse country centroids (km calc is rough but good enough) ---
COUNTRY_LATLON = {
    "IN": (22.0, 79.0), "US": (39.8, -98.6), "GB": (54.0, -2.5), "SG": (1.3, 103.8),
    "RU": (61.5, 105.3), "DE": (51.1, 10.4), "AE": (23.4, 53.8), "FR": (46.2, 2.2),
    "JP": (36.2, 138.2), "BR": (-14.2, -51.9),
}

def _haversine_km(a, b):
    from math import radians, sin, cos, asin, sqrt
    if not a or not b: return 0.0
    lat1, lon1 = map(radians, a); lat2, lon2 = map(radians, b)
    dlat = lat2 - lat1; dlon = lon2 - lon1
    x = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2*6371*asin(sqrt(x))

def ml_to_01(anom_score):
    # IsolationForest decision_function: higher==more normal
    return 1.0 / (1.0 + math.exp(10 * anom_score))

def final_risk(anomaly_score, rules_s):
    return 0.6 * ml_to_01(anomaly_score) + 0.4 * rules_s

def _odd_hour(tx):
    hr = tx.get("hour")
    return tx["type"] == "transfer" and (hr < 5 or hr > 23)

def build_explanations(tx, user_profile, anomaly_score):
    user_profile = user_profile or {}
    exps = []
    avg_amt = float(user_profile.get("avg_amount", 50.0) or 50.0)
    if avg_amt > 0:
        ratio = tx["amount"] / avg_amt
        if ratio > 5:
            exps.append(f"Amount {ratio:.1f}x above 30-day median")
    if tx.get("country") and user_profile.get("usual_countries"):
        if tx["country"] not in user_profile["usual_countries"]:
            exps.append(f"New country {tx['country']} (usual: {','.join(user_profile['usual_countries'])})")
    if _odd_hour(tx): exps.append("Out-of-hours high-risk transfer")
    exps.append(f"Anomaly score {anomaly_score:.3f} (IForest)")
    return exps

# ---------------- advanced rules with context ----------------
def advanced_rules_score(tx, user_profile, ctx):
    """
    tx: {'amount','type','country','hour','ts','device_fingerprint'}
    user_profile: JSON from users.profile (may include 'avg_amount','usual_countries','hourly_median')
    ctx: {
        'prev_country': 'IN'|'US'|...|None,
        'prev_ts': datetime|None,
        'recent_cnt_10m': int,
        'recent_sum_transfers_30m': float,
        'device_seen_countries': set[str],
    }
    returns (score, explanations_list)
    """
    s = 0.0
    exps = []
    up = user_profile or {}
    avg_amt = float(up.get("avg_amount", 50.0) or 50.0)
    usual_countries = set(up.get("usual_countries", []) or [])
    usual_devices   = set(up.get("usual_devices", []) or [])

    # A) amount spike vs personal baseline
    if avg_amt > 0 and tx["amount"] > 5 * avg_amt:
        s += 0.25; exps.append("Amount spike vs user median")

    # B) geo novelty
    if tx.get("country") and usual_countries and tx["country"] not in usual_countries:
        s += 0.20; exps.append("New geography for this user")

    # C) odd-hour transfer
    if _odd_hour(tx):
        s += 0.10; exps.append("Out-of-hours transfer")

    # D) device novelty
    if tx.get("device_fingerprint") and usual_devices and tx["device_fingerprint"] not in usual_devices:
        s += 0.10; exps.append("New device for this user")

    # E) velocity (count)
    if (ctx.get("recent_cnt_10m", 0) or 0) >= 8:
        s += 0.20; exps.append("High velocity (>=8 tx in 10m)")
    elif (ctx.get("recent_cnt_10m", 0) or 0) >= 5:
        s += 0.12; exps.append("Elevated velocity (>=5 tx in 10m)")

    # F) value burst (transfers)
    if (ctx.get("recent_sum_transfers_30m", 0.0) or 0.0) > 10 * avg_amt:
        s += 0.20; exps.append("Value burst (30m sum >> median)")

    # G) device-geo mismatch: device never seen in this country recently
    dev_countries = set(ctx.get("device_seen_countries") or [])
    if tx.get("device_fingerprint") and tx.get("country") and dev_countries and tx["country"] not in dev_countries:
        s += 0.15; exps.append("Device-geo mismatch")

    # H) impossible travel from previous transaction
    prev_country = ctx.get("prev_country"); prev_ts = ctx.get("prev_ts")
    if prev_country and prev_ts and tx.get("country"):
        a = COUNTRY_LATLON.get(prev_country); b = COUNTRY_LATLON.get(tx["country"])
        if a and b:
            dt = (tx["ts"] - prev_ts).total_seconds() / 3600.0
            if dt > 0:
                speed = _haversine_km(a, b) / dt  # km/h
                if speed > 900:          # > commercial jet
                    s += 0.25; exps.append(f"Impossible travel (~{int(speed)} km/h)")

    # I) hour-of-day amount profile (if available)
    hourly = up.get("hourly_median") or {}
    try:
        hour_med = float(hourly.get(str(tx["hour"])) or hourly.get(tx["hour"]) or 0.0)
        if hour_med > 0 and (tx["amount"] / hour_med) > 5:
            s += 0.15; exps.append("Spike vs usual-for-this-hour")
    except Exception:
        pass

    return min(s, 0.95), exps
# --- compatibility shim for older callers (e.g., train_model.py) ---
def rules_score(tx, user_profile):
    """
    Backward-compatible wrapper that maps to advanced_rules_score with empty context.
    Returns only the score (ignores explanation list).
    """
    score, _ = advanced_rules_score(tx, user_profile, ctx={})
    return score
