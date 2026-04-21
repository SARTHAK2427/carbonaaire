"""
api_server.py — Carbonaire FastAPI server
"""

import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, Header, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.input_schema import CarbonInputData, inputs_from_dict, validate_inputs
from core.master_calculator import run_calculation
from rules.rule_engine import RuleEngine
from utils.helpers import (
    extract_from_cloud_document,
    extract_from_electricity_document,
    extract_from_fuel_document,
    extract_from_hardware_document,
    load_inputs_from_excel,
)
from utils.report_generator import _benchmark_block
from ml.recommender import get_recommender_v2

# ─── AUTH IMPORTS ─────────────────────────────────────────────
# Wrapped in try/except so server still starts if DB has an issue
try:
    from ml.auth_system import (
        register_user,
        login_user,
        validate_token,
        logout_user,
        save_assessment,
        get_user_history,
        get_personalization_context,
        get_user_profile,
        get_learning_status,
        save_feedback,
    )
    AUTH_AVAILABLE = True
    print("[OK] Auth system loaded.")
except Exception as _auth_err:
    AUTH_AVAILABLE = False
    print(f"[WARN] Auth system unavailable: {_auth_err}")

# ─── RAG DISABLED ───────────────────────────────────────────────
RAG_AVAILABLE = False
print("[INFO] RAG engine disabled by request.")

# ─── APP ──────────────────────────────────────────────────────

app = FastAPI(title="Carbonaire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

recommender = get_recommender_v2(models_dir=os.path.join(
    os.path.dirname(__file__), "ml", "models"
))


# ─── HELPERS ──────────────────────────────────────────────────

def _get_user_from_header(authorization: Optional[str]) -> Optional[str]:
    """Extract and validate Bearer token. Returns user_id or None."""
    if not AUTH_AVAILABLE or not authorization:
        return None
    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        return validate_token(token)
    except Exception:
        return None


def _strip_confidence(ml_out: Dict) -> Dict:
    """
    Remove confidence % from all ML output fields before
    sending to frontend — 51% looks weak, per product spec.
    """
    if not ml_out:
        return ml_out
    keys_to_remove = ["ml_confidence"]
    cleaned = {k: v for k, v in ml_out.items() if k not in keys_to_remove}

    # Also strip from top3 recommendations list
    if "ml_top3_recommendations" in cleaned:
        for rec in cleaned["ml_top3_recommendations"]:
            rec.pop("confidence", None)

    # Strip from enhanced findings
    if "ml_enhanced_findings" in cleaned:
        for finding in cleaned["ml_enhanced_findings"]:
            finding.pop("confidence", None)

    return cleaned


# ─── PYDANTIC MODELS ──────────────────────────────────────────

class CarbonInputPayload(BaseModel):
    company_name: Optional[str] = None
    industry_type: Optional[str] = None
    location_state: Optional[str] = None
    num_employees: Optional[int] = None
    working_hours_per_day: Optional[float] = None
    annual_revenue_inr_cr: Optional[float] = None
    diesel_litres_per_month: Optional[float] = None
    petrol_litres_per_month: Optional[float] = None
    natural_gas_m3_per_month: Optional[float] = None
    lpg_litres_per_month: Optional[float] = None
    power_backup_runtime_hours: Optional[float] = None
    electricity_kwh_per_month: Optional[float] = None
    renewable_energy_percent: Optional[float] = None
    server_rack_count: Optional[int] = None
    server_operating_hours_per_day: Optional[float] = None
    server_arrangement: Optional[str] = None
    server_area_sqft: Optional[float] = None
    server_model: Optional[str] = None
    num_laptops: Optional[int] = None
    num_desktops: Optional[int] = None
    num_servers_onprem: Optional[int] = None
    num_monitors: Optional[int] = None
    cloud_provider: Optional[str] = None
    cloud_monthly_bill_inr: Optional[float] = None
    cloud_compute_hours_per_month: Optional[float] = None
    cloud_kwh_per_month: Optional[float] = None
    purchased_services_spend_inr_per_month: Optional[float] = None
    cooling_system_type: Optional[str] = None
    uploaded_docs: Optional[List[str]] = None


class RegisterPayload(BaseModel):
    email: str
    name: str
    password: str
    company_name: Optional[str] = ""


class LoginPayload(BaseModel):
    email: str
    password: str


class FeedbackPayload(BaseModel):
    recommendations: List[str]
    input_snapshot: Optional[Dict[str, Any]] = None


# ─── AUTH ENDPOINTS ───────────────────────────────────────────

@app.post("/api/auth/register")
def api_register(payload: RegisterPayload) -> Dict:
    if not AUTH_AVAILABLE:
        return {"ok": False, "error": "Auth service unavailable."}
    return register_user(
        email=payload.email,
        name=payload.name,
        password=payload.password,
        company_name=payload.company_name or "",
    )


@app.post("/api/auth/login")
def api_login(payload: LoginPayload) -> Dict:
    if not AUTH_AVAILABLE:
        return {"ok": False, "error": "Auth service unavailable."}
    return login_user(email=payload.email, password=payload.password)


@app.post("/api/auth/logout")
def api_logout(authorization: Optional[str] = Header(None)) -> Dict:
    if not AUTH_AVAILABLE:
        return {"ok": True}
    user_id = _get_user_from_header(authorization)
    if not user_id or not authorization:
        return {"ok": True}
    _, _, token = authorization.partition(" ")
    return logout_user(token)


@app.get("/api/auth/me")
def api_me(authorization: Optional[str] = Header(None)) -> Dict:
    user_id = _get_user_from_header(authorization)
    if not user_id:
        return {"ok": False, "error": "Not authenticated."}
    profile = get_user_profile(user_id)
    return {"ok": True, "user": profile}


# ─── FEEDBACK ENDPOINT ────────────────────────────────────────

@app.post("/api/feedback")
def api_feedback(
    payload: FeedbackPayload,
    authorization: Optional[str] = Header(None),
) -> Dict:
    """
    Called when user checks recommendation checkboxes.
    Saves their preferences + input snapshot to DB.
    Triggers auto-retrain every 100 feedbacks.
    """
    if not AUTH_AVAILABLE:
        return {"ok": False, "error": "Auth service unavailable."}

    user_id = _get_user_from_header(authorization)
    if not user_id:
        return {"ok": False, "error": "Authentication required to save feedback."}

    if not payload.recommendations:
        return {"ok": False, "error": "No recommendations provided."}

    return save_feedback(
        user_id=user_id,
        recommendations=payload.recommendations,
        input_snapshot=payload.input_snapshot or {},
    )


# ─── USER HISTORY & LEARNING STATUS ──────────────────────────

@app.get("/api/user/history")
def api_user_history(authorization: Optional[str] = Header(None)) -> Dict:
    user_id = _get_user_from_header(authorization)
    if not user_id:
        return {"ok": False, "error": "Authentication required."}
    history = get_user_history(user_id)
    return {"ok": True, "history": history}


@app.get("/api/user/learning-status")
def api_learning_status() -> Dict:
    """Public endpoint — no auth needed. Powers the learning bar in MLDashboard."""
    if not AUTH_AVAILABLE:
        return {
            "logged_samples": 0,
            "progress_pct": 0,
            "samples_until_retrain": 100,
            "next_retrain_at": 100,
            "last_retrained": None,
            "retrain_threshold": 100,
        }
    return get_learning_status()


@app.get("/api/user/profile")
def api_user_profile(authorization: Optional[str] = Header(None)) -> Dict:
    user_id = _get_user_from_header(authorization)
    if not user_id:
        return {"ok": False, "error": "Authentication required."}
    profile = get_user_profile(user_id)
    return {"ok": True, "profile": profile}


# ─── MAIN ASSESSMENT ENDPOINT ────────────────────────────────

@app.post("/api/run")
def run_assessment(
    payload: CarbonInputPayload,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:

    data_dict = {k: v for k, v in payload.dict().items() if v is not None}
    data = inputs_from_dict(data_dict)

    validation = validate_inputs(data)
    if validation["errors"]:
        return {
            "ok": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "info": validation.get("info", []),
        }

    result = run_calculation(data)
    result["validation"] = validation

    engine = RuleEngine()
    findings = engine.evaluate(result, data)

    ml_out = recommender.recommend(result, data, findings)

    # ── Remove confidence % from output (looks weak at 51%) ──
    ml_out_clean = _strip_confidence(ml_out)

    # ── Personalization for logged-in users ──
    personalization = None
    user_id = _get_user_from_header(authorization)

    if user_id and AUTH_AVAILABLE:
        try:
            # Save assessment first so personalization can compare prev vs current
            save_assessment(user_id, data, result, ml_out)
            # Then get personalization context (compares last 2 assessments)
            personalization = get_personalization_context(user_id, result)
        except Exception as _e:
            print(f"⚠️  Personalization error: {_e}")

    return {
        "ok": True,
        "company": {
            "company_name":  data.company_name,
            "industry_type": data.industry_type,
            "location_state": data.location_state,
        },
        "emissions": {
            "monthly":          result["monthly"],
            "annual":           result["annual"],
            "scope_percentages": result["scope_percentages"],
            "scope1":           result["scope1"],
            "scope2":           result["scope2"],
            "scope3":           result["scope3"],
        },
        "intensity":       result["intensity"],
        "benchmark":       _benchmark_block(result),
        "findings": [
            {
                "severity":       f.severity.name,
                "severity_value": f.severity.value,
                "scope":          f.scope,
                "category":       f.category,
                "message":        f.message,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "ml":              ml_out_clean,
        "personalization": personalization,
        "validation":      validation,
    }


# ─── RAG / AI ADVISOR ENDPOINT ───────────────────────────────

class AskPayload(BaseModel):
    question: str
    user_data: Optional[Dict[str, Any]] = None

@app.post("/api/ask")
def api_ask(payload: AskPayload) -> Dict:
    """
    Accepts a natural-language question plus optional emission context,
    retrieves relevant knowledge via ChromaDB (RAG), and generates an
    answer using the local Mistral model via Ollama.
    """
    if not RAG_AVAILABLE:
        return {
            "ok": False,
            "answer": (
                "The RAG engine is not available. "
                "Please install chromadb and sentence-transformers, "
                "then run rag/index_documents.py to build the index."
            ),
        }
    try:
        answer = rag_get_answer(payload.question, payload.user_data)
        return {"ok": True, "answer": answer}
    except Exception as e:
        return {"ok": False, "answer": f"RAG error: {e}"}


# ─── DOCUMENT UPLOAD ──────────────────────────────────────────

@app.post("/api/upload-doc")
async def upload_document(doc_type: str = Form(...), file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    try:
        if doc_type == "electricity":
            extracted_data = extract_from_electricity_document(tmp_path)
        elif doc_type == "cloud":
            extracted_data = extract_from_cloud_document(tmp_path)
        elif doc_type == "fuel":
            extracted_data = extract_from_fuel_document(tmp_path)
        elif doc_type == "hardware":
            extracted_data = extract_from_hardware_document(tmp_path)
        elif doc_type == "template":
            from dataclasses import asdict
            data_obj = load_inputs_from_excel(tmp_path)
            extracted_data = asdict(data_obj)
        else:
            return {"ok": False, "error": f"Unrecognised doc type: {doc_type}"}
        return {"ok": True, "data": extracted_data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─── RUN ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
