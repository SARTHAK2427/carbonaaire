"""
ml/user_system.py
==================
User authentication, session management, history tracking,
personalization, and continuous learning trigger.

Features:
  - JWT-based login (lightweight, no external DB needed — SQLite)
  - Store per-user assessment history
  - Compare current vs previous run (delta tracking)
  - Log new data to CSV for periodic retraining
  - Trigger retraining after every 100 new logged samples
"""

import os
import csv
import json
import uuid
import hashlib
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

DB_PATH       = os.path.join(os.path.dirname(__file__), "data", "carbonaire_users.db")
LOG_CSV_PATH  = os.path.join(os.path.dirname(__file__), "data", "continuous_learning_log.csv")
RETRAIN_EVERY = 100       # rows accumulated before auto-retrain triggers
SECRET_KEY    = os.getenv("CARBONAIRE_SECRET_KEY", "carbonaire-secret-change-in-prod-2025")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

_retrain_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     TEXT PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            company_name TEXT
        );

        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id  TEXT PRIMARY KEY,
            user_id        TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            input_snapshot TEXT NOT NULL,
            result_snapshot TEXT NOT NULL,
            ml_snapshot    TEXT NOT NULL,
            total_tco2e_monthly REAL,
            primary_recommendation TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ─────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────

def _hash_password(pw: str) -> str:
    return hashlib.sha256((pw + SECRET_KEY).encode()).hexdigest()


def _make_token(user_id: str) -> str:
    token = str(uuid.uuid4())
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (token, user_id, expires_at) VALUES (?,?,?)",
        (token, user_id, expires)
    )
    conn.commit()
    conn.close()
    return token


def register_user(email: str, name: str, password: str, company_name: str = "") -> Dict:
    """Register a new user. Returns {ok, user_id, token} or {ok:False, error}."""
    conn = _get_conn()
    existing = conn.execute("SELECT user_id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return {"ok": False, "error": "Email already registered"}
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users (user_id,email,name,password_hash,created_at,company_name) VALUES (?,?,?,?,?,?)",
        (user_id, email.lower().strip(), name, _hash_password(password),
         datetime.utcnow().isoformat(), company_name)
    )
    conn.commit()
    conn.close()
    token = _make_token(user_id)
    return {"ok": True, "user_id": user_id, "token": token, "name": name, "email": email}


def login_user(email: str, password: str) -> Dict:
    """Verify credentials. Returns {ok, user_id, token, name} or error."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT user_id,name,password_hash FROM users WHERE email=?",
        (email.lower().strip(),)
    ).fetchone()
    conn.close()
    if not row or row["password_hash"] != _hash_password(password):
        return {"ok": False, "error": "Invalid email or password"}
    token = _make_token(row["user_id"])
    return {"ok": True, "user_id": row["user_id"], "token": token, "name": row["name"], "email": email}


def validate_token(token: str) -> Optional[str]:
    """Return user_id if token is valid and not expired, else None."""
    if not token:
        return None
    conn = _get_conn()
    row  = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE token=?", (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        return None
    return row["user_id"]


def logout_user(token: str):
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE token=?", (token,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# ASSESSMENT HISTORY
# ─────────────────────────────────────────────────────────────

def save_assessment(user_id: str, input_data: Any, result: Dict, ml_out: Dict) -> str:
    """Persist an assessment run for a user. Returns assessment_id."""
    assessment_id = str(uuid.uuid4())
    created_at    = datetime.utcnow().isoformat()

    # Serialise input data
    try:
        from dataclasses import asdict
        input_dict = asdict(input_data)
    except Exception:
        input_dict = {k: getattr(input_data, k, None)
                      for k in dir(input_data) if not k.startswith("_")}

    total = result.get("monthly", {}).get("total_tco2e", 0)
    primary = ml_out.get("ml_primary_recommendation", "")

    conn = _get_conn()
    conn.execute(
        """INSERT INTO assessments
           (assessment_id,user_id,created_at,input_snapshot,result_snapshot,
            ml_snapshot,total_tco2e_monthly,primary_recommendation)
           VALUES (?,?,?,?,?,?,?,?)""",
        (assessment_id, user_id, created_at,
         json.dumps(input_dict, default=str),
         json.dumps(_safe_result(result)),
         json.dumps(_safe_ml(ml_out)),
         total, primary)
    )
    conn.commit()
    conn.close()

    # Log to CSV for continuous learning
    _log_for_retraining(input_dict, result, ml_out)

    return assessment_id


def get_user_history(user_id: str, limit: int = 10) -> List[Dict]:
    """Return last N assessments for a user (newest first)."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT assessment_id,created_at,total_tco2e_monthly,primary_recommendation,
                  input_snapshot,result_snapshot,ml_snapshot
           FROM assessments WHERE user_id=? ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            "assessment_id":       r["assessment_id"],
            "created_at":          r["created_at"],
            "total_tco2e_monthly": r["total_tco2e_monthly"],
            "primary_recommendation": r["primary_recommendation"],
            "input": json.loads(r["input_snapshot"]),
            "result": json.loads(r["result_snapshot"]),
            "ml": json.loads(r["ml_snapshot"]),
        })
    return out


def get_personalization_context(user_id: str) -> Dict:
    """
    Compare the two most recent assessments and return delta insights.
    Used for the "You increased electricity by 10%" UI feature.
    """
    history = get_user_history(user_id, limit=2)
    if len(history) < 2:
        return {"has_previous": False, "deltas": [], "history_count": len(history)}

    curr = history[0]
    prev = history[1]

    curr_inp = curr["input"]
    prev_inp = prev["input"]

    TRACKED_FIELDS = [
        ("electricity_kwh_per_month",       "Electricity usage",      "kWh/month"),
        ("renewable_energy_percent",         "Renewable energy",       "%"),
        ("diesel_litres_per_month",          "Diesel consumption",     "L/month"),
        ("num_employees",                    "Headcount",              "employees"),
        ("cloud_monthly_bill_inr",           "Cloud spend",            "₹/month"),
        ("server_rack_count",                "Server racks",           "racks"),
        ("purchased_services_spend_inr_per_month", "Service spend",   "₹/month"),
    ]

    deltas = []
    for field, label, unit in TRACKED_FIELDS:
        c_val = curr_inp.get(field) or 0
        p_val = prev_inp.get(field) or 0
        if p_val == 0 and c_val == 0:
            continue
        if p_val == 0:
            pct_change = 100.0
        else:
            pct_change = ((c_val - p_val) / p_val) * 100

        if abs(pct_change) < 1:   # skip negligible changes
            continue

        direction = "increased" if pct_change > 0 else "decreased"
        abs_pct   = abs(round(pct_change, 1))

        deltas.append({
            "field":      field,
            "label":      label,
            "unit":       unit,
            "prev_value": round(p_val, 1),
            "curr_value": round(c_val, 1),
            "pct_change": round(pct_change, 1),
            "direction":  direction,
            "abs_pct":    abs_pct,
            "message":    f"You {direction} {label.lower()} by {abs_pct}% ({round(p_val,1)} → {round(c_val,1)} {unit})",
            "is_positive": (direction == "decreased" and field != "renewable_energy_percent")
                            or (direction == "increased" and field == "renewable_energy_percent"),
        })

    # Emission delta
    curr_tco2 = curr["total_tco2e_monthly"] or 0
    prev_tco2 = prev["total_tco2e_monthly"] or 0
    if prev_tco2 > 0:
        emission_delta = round(((curr_tco2 - prev_tco2) / prev_tco2) * 100, 1)
    else:
        emission_delta = 0

    return {
        "has_previous":       True,
        "history_count":      len(get_user_history(user_id, limit=100)),
        "deltas":             deltas,
        "emission_delta_pct": emission_delta,
        "emission_direction": "increased" if emission_delta > 0 else "decreased",
        "prev_assessment_date": prev["created_at"][:10],
        "prev_tco2e":         round(prev_tco2, 2),
        "curr_tco2e":         round(curr_tco2, 2),
        "prev_recommendation": prev["primary_recommendation"],
        "curr_recommendation": curr["primary_recommendation"],
    }


def get_user_profile(user_id: str) -> Optional[Dict]:
    conn = _get_conn()
    row  = conn.execute(
        "SELECT user_id,email,name,company_name,created_at FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


# ─────────────────────────────────────────────────────────────
# CONTINUOUS LEARNING
# ─────────────────────────────────────────────────────────────

_LOG_FIELDNAMES = [
    "logged_at","industry_type","company_size","num_employees",
    "electricity_kwh_per_month","renewable_energy_percent",
    "diesel_litres_per_month","server_rack_count","cloud_monthly_bill_inr",
    "purchased_services_spend_inr_per_month","scope1_pct","scope2_pct","scope3_pct",
    "total_tco2e_monthly","primary_recommendation",
]

def _log_for_retraining(input_dict: Dict, result: Dict, ml_out: Dict):
    """Append one row to the continuous learning CSV."""
    scope_pct = result.get("scope_percentages", {})
    row = {
        "logged_at":                    datetime.utcnow().isoformat(),
        "industry_type":                input_dict.get("industry_type",""),
        "company_size":                 _size_from_emp(input_dict.get("num_employees",50)),
        "num_employees":                input_dict.get("num_employees",0),
        "electricity_kwh_per_month":    input_dict.get("electricity_kwh_per_month",0),
        "renewable_energy_percent":     input_dict.get("renewable_energy_percent",0),
        "diesel_litres_per_month":      input_dict.get("diesel_litres_per_month",0),
        "server_rack_count":            input_dict.get("server_rack_count",0),
        "cloud_monthly_bill_inr":       input_dict.get("cloud_monthly_bill_inr",0),
        "purchased_services_spend_inr_per_month": input_dict.get("purchased_services_spend_inr_per_month",0),
        "scope1_pct":                   scope_pct.get("scope1",0),
        "scope2_pct":                   scope_pct.get("scope2",0),
        "scope3_pct":                   scope_pct.get("scope3",0),
        "total_tco2e_monthly":          result.get("monthly",{}).get("total_tco2e",0),
        "primary_recommendation":       ml_out.get("ml_primary_recommendation",""),
    }
    file_exists = os.path.exists(LOG_CSV_PATH)
    with open(LOG_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_LOG_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    # Check if retraining threshold has been reached
    _maybe_retrain()


def _maybe_retrain():
    """If log CSV has grown by RETRAIN_EVERY rows since last retrain, trigger retrain in background."""
    if not os.path.exists(LOG_CSV_PATH):
        return
    with open(LOG_CSV_PATH) as f:
        row_count = sum(1 for _ in f) - 1   # subtract header

    if row_count > 0 and row_count % RETRAIN_EVERY == 0:
        thread = threading.Thread(target=_background_retrain, daemon=True)
        thread.start()


def _background_retrain():
    """Retrain models on accumulated real data merged with synthetic base."""
    with _retrain_lock:
        try:
            print(f"🔄  Auto-retrain triggered ({RETRAIN_EVERY} new samples accumulated)...")
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "run_training.py")],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print("✅  Auto-retrain complete.")
            else:
                print(f"⚠️  Auto-retrain failed:\n{result.stderr[:500]}")
        except Exception as e:
            print(f"⚠️  Auto-retrain exception: {e}")


def get_learning_status() -> Dict:
    """Return current continuous learning status."""
    if not os.path.exists(LOG_CSV_PATH):
        return {"logged_samples": 0, "next_retrain_at": RETRAIN_EVERY, "progress_pct": 0}
    with open(LOG_CSV_PATH) as f:
        count = sum(1 for _ in f) - 1
    next_at  = ((count // RETRAIN_EVERY) + 1) * RETRAIN_EVERY
    progress = round((count % RETRAIN_EVERY) / RETRAIN_EVERY * 100, 1)
    return {
        "logged_samples":   count,
        "retrain_every":    RETRAIN_EVERY,
        "next_retrain_at":  next_at,
        "samples_until_retrain": next_at - count,
        "progress_pct":     progress,
    }


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _size_from_emp(n):
    if n <= 50:  return "small"
    if n <= 300: return "medium"
    return "large"

def _safe_result(r):
    """Strip non-serialisable objects from result dict."""
    try:
        return json.loads(json.dumps(r, default=str))
    except Exception:
        return {}

def _safe_ml(ml):
    try:
        return json.loads(json.dumps(ml, default=str))
    except Exception:
        return {}
