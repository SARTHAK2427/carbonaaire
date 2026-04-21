"""
ml/auth_system.py
==================
Fresh auth system for Carbonaire.
Handles: users, tokens, assessments, feedback, auto-retraining, personalization.
"""

import os
import json
import sqlite3
import hashlib
import secrets
import threading
import pickle
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import Counter

# ─── DB PATH ──────────────────────────────────────────────────
# Goes in the project root (one level above ml/)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "carbonaire.db")
DB_PATH = os.path.abspath(DB_PATH)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
RETRAIN_THRESHOLD = 100

# ─── CONNECTION ───────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ─── SCHEMA ───────────────────────────────────────────────────

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           TEXT PRIMARY KEY,
            email        TEXT UNIQUE NOT NULL,
            name         TEXT NOT NULL,
            company_name TEXT,
            password_hash TEXT NOT NULL,
            created_at   TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token      TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id         TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            inputs     TEXT NOT NULL,
            results    TEXT NOT NULL,
            ml_output  TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id             TEXT PRIMARY KEY,
            user_id        TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            input_snapshot TEXT,
            created_at     TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] Carbonaire DB initialized:", DB_PATH)


# Initialize immediately on import
init_db()


# ─── PASSWORD ─────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """SHA-256 hash — no extra dependencies needed."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ─── TOKENS ───────────────────────────────────────────────────

def _create_token(user_id: str, conn: sqlite3.Connection) -> str:
    token = secrets.token_hex(32)
    conn.execute(
        "INSERT INTO tokens (token, user_id, created_at) VALUES (?,?,?)",
        (token, user_id, datetime.utcnow().isoformat())
    )
    conn.commit()
    return token


# ─── AUTH ─────────────────────────────────────────────────────

def register_user(email: str, name: str, password: str, company_name: str = "") -> Dict:
    if not email or not name or not password:
        return {"ok": False, "error": "Email, name and password are required."}
    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters."}

    conn = get_db()
    try:
        user_id = secrets.token_hex(16)
        conn.execute(
            "INSERT INTO users (id, email, name, company_name, password_hash, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                user_id,
                email.strip().lower(),
                name.strip(),
                company_name.strip(),
                _hash_password(password),
                datetime.utcnow().isoformat(),
            )
        )
        conn.commit()
        token = _create_token(user_id, conn)
        return {
            "ok": True,
            "token": token,
            "user_id": user_id,
            "name": name.strip(),
            "email": email.strip().lower(),
        }
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "An account with this email already exists."}
    finally:
        conn.close()


def login_user(email: str, password: str) -> Dict:
    if not email or not password:
        return {"ok": False, "error": "Email and password are required."}

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email=? AND password_hash=?",
            (email.strip().lower(), _hash_password(password))
        ).fetchone()

        if not row:
            return {"ok": False, "error": "Invalid email or password."}

        token = _create_token(row["id"], conn)
        return {
            "ok": True,
            "token": token,
            "user_id": row["id"],
            "name": row["name"],
            "email": row["email"],
        }
    finally:
        conn.close()


def validate_token(token: str) -> Optional[str]:
    """Returns user_id if token is valid, else None."""
    if not token:
        return None
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT user_id FROM tokens WHERE token=?", (token,)
        ).fetchone()
        return row["user_id"] if row else None
    finally:
        conn.close()


def logout_user(token: str) -> Dict:
    conn = get_db()
    try:
        conn.execute("DELETE FROM tokens WHERE token=?", (token,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def get_user_profile(user_id: str) -> Optional[Dict]:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, email, name, company_name, created_at FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── ASSESSMENTS ──────────────────────────────────────────────

# Full list of input fields we snapshot for personalization comparison
_INPUT_FIELDS = [
    "electricity_kwh_per_month",
    "renewable_energy_percent",
    "diesel_litres_per_month",
    "petrol_litres_per_month",
    "natural_gas_m3_per_month",
    "lpg_litres_per_month",
    "num_employees",
    "cloud_provider",
    "cloud_monthly_bill_inr",
    "server_rack_count",
    "num_servers_onprem",
    "num_laptops",
    "num_desktops",
    "num_monitors",
    "server_arrangement",
    "purchased_services_spend_inr_per_month",
    "annual_revenue_inr_cr",
    "location_state",
    "industry_type",
]


def save_assessment(user_id: str, data: Any, result: Dict, ml_out: Dict) -> str:
    """
    Save a completed assessment to the DB.
    Returns the new assessment_id.
    """
    conn = get_db()
    try:
        assessment_id = secrets.token_hex(16)

        # Safely extract from Pydantic model or dict
        def _get(field):
            if hasattr(data, field):
                return getattr(data, field)
            if isinstance(data, dict):
                return data.get(field)
            return None

        inputs = json.dumps({f: _get(f) for f in _INPUT_FIELDS})

        monthly = result.get("monthly", {})
        results = json.dumps({
            "total_tco2e":  monthly.get("total_tco2e", 0),
            "scope1_tco2e": monthly.get("scope1_tco2e", 0),
            "scope2_tco2e": monthly.get("scope2_tco2e", 0),
            "scope3_tco2e": monthly.get("scope3_tco2e", 0),
            "intensity":    result.get("intensity", {}).get("revenue_intensity_tco2e_per_cr", 0),
        })

        ml_json = json.dumps({
            "primary":    ml_out.get("ml_primary_recommendation"),
            "confidence": ml_out.get("ml_confidence"),
            "cluster":    ml_out.get("ml_cluster"),
        })

        conn.execute(
            "INSERT INTO assessments (id, user_id, inputs, results, ml_output, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (
                assessment_id, user_id, inputs, results, ml_json,
                datetime.utcnow().isoformat()
            )
        )
        conn.commit()
        return assessment_id
    finally:
        conn.close()


def get_user_history(user_id: str, limit: int = 10) -> List[Dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM assessments WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        history = []
        for r in rows:
            entry = dict(r)
            # Parse JSON blobs back to dicts
            try: entry["inputs"]    = json.loads(entry["inputs"])
            except: pass
            try: entry["results"]   = json.loads(entry["results"])
            except: pass
            try: entry["ml_output"] = json.loads(entry["ml_output"])
            except: pass
            history.append(entry)
        return history
    finally:
        conn.close()


# ─── PERSONALIZATION ──────────────────────────────────────────

def get_personalization_context(user_id: str, current_result: Dict = None) -> Dict:
    """
    Returns a rich personalization object that MLDashboard.jsx expects:
    {
        has_previous: bool,
        has_preferences: bool,
        preferred_recommendations: [...],
        prev_tco2e, curr_tco2e, emission_delta_pct, emission_direction,
        prev_assessment_date,
        deltas: [ {field, label, prev_value, curr_value, direction, abs_pct, is_positive} ]
    }
    """
    conn = get_db()
    try:
        # ── Preferred recommendations (from feedback checkboxes) ──
        fb_rows = conn.execute(
            "SELECT recommendations FROM feedback WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        ).fetchall()

        all_recs: List[str] = []
        for row in fb_rows:
            try:
                all_recs.extend(json.loads(row["recommendations"]))
            except:
                pass
        top_recs = [r for r, _ in Counter(all_recs).most_common(3)]

        # ── Previous assessment comparison ──
        past = conn.execute(
            "SELECT results, inputs, created_at FROM assessments "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT 2",
            (user_id,)
        ).fetchall()

        if len(past) < 2 or not current_result:
            return {
                "has_previous": False,
                "has_preferences": len(top_recs) > 0,
                "preferred_recommendations": top_recs,
            }

        # Most recent previous assessment
        prev_row = past[1]
        try:
            prev_results = json.loads(prev_row["results"])
            prev_inputs  = json.loads(prev_row["inputs"])
        except:
            return {
                "has_previous": False,
                "has_preferences": len(top_recs) > 0,
                "preferred_recommendations": top_recs,
            }

        # Current totals
        monthly = current_result.get("monthly", {})
        curr_total = monthly.get("total_tco2e", 0) or 0
        prev_total = prev_results.get("total_tco2e", 0) or 0

        if prev_total == 0:
            delta_pct = 0.0
        else:
            delta_pct = ((curr_total - prev_total) / prev_total) * 100

        direction = "decreased" if curr_total < prev_total else "increased"

        # ── Field-level deltas ──
        DELTA_FIELDS = [
            ("electricity_kwh_per_month",  "Electricity",     "kWh/mo",  False),  # lower = better
            ("renewable_energy_percent",   "Renewables",      "%",       True),   # higher = better
            ("diesel_litres_per_month",    "Diesel",          "L/mo",    False),
            ("cloud_monthly_bill_inr",     "Cloud spend",     "Rs/mo",   False),
            ("num_servers_onprem",         "On-prem servers", "units",   False),
        ]

        deltas = []
        # Get most recent assessment's inputs for current
        try:
            curr_inputs_row = conn.execute(
                "SELECT inputs FROM assessments WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            curr_inputs = json.loads(curr_inputs_row["inputs"]) if curr_inputs_row else {}
        except:
            curr_inputs = {}

        for field, label, unit, higher_is_better in DELTA_FIELDS:
            prev_val = prev_inputs.get(field) or 0
            curr_val = curr_inputs.get(field) or 0
            if prev_val == 0 and curr_val == 0:
                continue
            if prev_val == 0:
                continue
            pct = ((curr_val - prev_val) / prev_val) * 100
            if abs(pct) < 1:
                continue
            went_up = curr_val > prev_val
            is_positive = (went_up and higher_is_better) or (not went_up and not higher_is_better)
            deltas.append({
                "field":      field,
                "label":      label,
                "unit":       unit,
                "prev_value": round(prev_val, 1),
                "curr_value": round(curr_val, 1),
                "direction":  "increased" if went_up else "decreased",
                "abs_pct":    round(abs(pct), 1),
                "is_positive": is_positive,
            })

        # Parse date for display
        try:
            prev_date = prev_row["created_at"][:10]
        except:
            prev_date = "previous run"

        return {
            "has_previous":              True,
            "has_preferences":           len(top_recs) > 0,
            "preferred_recommendations": top_recs,
            "prev_tco2e":                round(prev_total, 3),
            "curr_tco2e":                round(curr_total, 3),
            "emission_delta_pct":        round(abs(delta_pct), 1),
            "emission_direction":        direction,
            "prev_assessment_date":      prev_date,
            "deltas":                    deltas,
        }
    finally:
        conn.close()


# ─── FEEDBACK ─────────────────────────────────────────────────

def save_feedback(user_id: str, recommendations: List[str], input_snapshot: Dict = None) -> Dict:
    """
    Save checked recommendation preferences.
    Triggers auto-retrain every RETRAIN_THRESHOLD feedbacks.
    """
    conn = get_db()
    try:
        feedback_id = secrets.token_hex(16)
        conn.execute(
            "INSERT INTO feedback (id, user_id, recommendations, input_snapshot, created_at) "
            "VALUES (?,?,?,?,?)",
            (
                feedback_id,
                user_id,
                json.dumps(recommendations),
                json.dumps(input_snapshot or {}),
                datetime.utcnow().isoformat(),
            )
        )
        conn.commit()

        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

        retrain_triggered = False
        if total > 0 and total % RETRAIN_THRESHOLD == 0:
            threading.Thread(target=_auto_retrain, daemon=True).start()
            retrain_triggered = True

        return {
            "ok": True,
            "feedback_id": feedback_id,
            "total_feedback": total,
            "retrain_triggered": retrain_triggered,
        }
    finally:
        conn.close()


# ─── AUTO RETRAIN ─────────────────────────────────────────────

def _auto_retrain():
    """
    Background thread: pulls feedback data from DB,
    builds a training dataframe, retrains RandomForest,
    and hot-swaps the .pkl file.
    """
    print("[RE-TRAIN] Auto-retrain started...")
    try:
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        conn = get_db()
        rows = conn.execute(
            "SELECT f.recommendations, f.input_snapshot "
            "FROM feedback f "
            "ORDER BY f.created_at DESC LIMIT 2000"
        ).fetchall()
        conn.close()

        if len(rows) < 20:
            print("[WARN] Not enough feedback to retrain (need 20+). Skipping.")
            return

        # ── Load original training CSV as base ──
        csv_path = os.path.join(os.path.dirname(__file__), "data", "carbonaire_training_data.csv")
        if os.path.exists(csv_path):
            base_df = pd.read_csv(csv_path)
        else:
            base_df = pd.DataFrame()

        # ── Build feedback rows ──
        fb_records = []
        for row in rows:
            try:
                recs  = json.loads(row["recommendations"])
                snap  = json.loads(row["input_snapshot"])
                if not recs or not snap:
                    continue
                # Use most-checked recommendation as the label
                label = recs[0] if recs else None
                if label:
                    snap["recommendation"] = label
                    fb_records.append(snap)
            except:
                continue

        if not fb_records:
            print("[WARN] No usable feedback records. Skipping retrain.")
            return

        fb_df = pd.DataFrame(fb_records)

        # ── Combine base + feedback ──
        if not base_df.empty and "recommendation" in base_df.columns:
            combined = pd.concat([base_df, fb_df], ignore_index=True)
        else:
            combined = fb_df

        # ── Load existing model metadata to match feature columns ──
        meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
        if not os.path.exists(meta_path):
            print("[WARN] model_metadata.json not found. Skipping retrain.")
            return

        with open(meta_path) as f:
            meta = json.load(f)

        feature_cols = meta.get("feature_columns", [])
        target_col   = "recommendation"

        if target_col not in combined.columns:
            print("[WARN] No target column in combined data. Skipping.")
            return

        # Fill missing columns with 0
        for col in feature_cols:
            if col not in combined.columns:
                combined[col] = 0

        combined = combined.dropna(subset=[target_col])
        X = combined[feature_cols].fillna(0)
        y = combined[target_col]

        if len(y.unique()) < 2:
            print("[WARN] Not enough class diversity. Skipping retrain.")
            return

        # ── Retrain ──
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )
        model.fit(X, y)

        # ── Backup old model then hot-swap ──
        dt_path     = os.path.join(MODELS_DIR, "decision_tree.pkl")
        backup_path = os.path.join(MODELS_DIR, "decision_tree_backup.pkl")

        if os.path.exists(dt_path):
            with open(dt_path, "rb") as f:
                old_model = pickle.load(f)
            with open(backup_path, "wb") as f:
                pickle.dump(old_model, f)

        with open(dt_path, "wb") as f:
            pickle.dump(model, f)

        # Update metadata
        meta["last_retrained"]   = datetime.utcnow().isoformat()
        meta["feedback_samples"] = len(fb_records)
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Reload the global recommender instance
        try:
            from ml.recommender import get_recommender_v2
            rec = get_recommender_v2()
            rec._load_models()
            print("[OK] Recommender hot-reloaded with new model.")
        except Exception as e:
            print(f"[WARN] Could not hot-reload recommender: {e}")

        print(f"[OK] Auto-retrain complete. Trained on {len(X)} samples.")

    except Exception as e:
        print(f"[ERROR] Auto-retrain failed: {e}")


# ─── LEARNING STATUS ──────────────────────────────────────────

def get_learning_status() -> Dict:
    """Returns the continuous learning progress for MLDashboard."""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        progress     = (total % RETRAIN_THRESHOLD) / RETRAIN_THRESHOLD * 100
        remaining    = RETRAIN_THRESHOLD - (total % RETRAIN_THRESHOLD)
        next_retrain = total + remaining

        # Check when last retrain happened
        last_retrain = None
        meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                last_retrain = meta.get("last_retrained")
            except:
                pass

        return {
            "logged_samples":       total,
            "progress_pct":         round(progress, 1),
            "samples_until_retrain": remaining,
            "next_retrain_at":      next_retrain,
            "last_retrained":       last_retrain,
            "retrain_threshold":    RETRAIN_THRESHOLD,
        }
    finally:
        conn.close()
