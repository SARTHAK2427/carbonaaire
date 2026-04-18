"""
api_server.py  (v2 — drop-in replacement)
==========================================
Carbonaire FastAPI server with:
  - All original endpoints preserved
  - ML v2 recommendations (scope-wise, XAI, priority colours, top-3)
  - User auth (register / login / logout)
  - Assessment history & personalization context
  - Continuous learning status endpoint
"""

import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
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

# ML v2
from ml.recommender import get_recommender_v2
from ml.user_system import (
    register_user, login_user, validate_token, logout_user,
    save_assessment, get_user_history, get_personalization_context,
    get_user_profile, get_learning_status,
)

# ─────────────────────────────────────────────────────────────
app = FastAPI(title="Carbonaire API v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

recommender = get_recommender_v2(models_dir=os.path.join(
    os.path.dirname(__file__), "ml", "models"
))


# ─────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────

def _current_user(authorization: Optional[str] = None) -> Optional[str]:
    """Extract user_id from Bearer token header. Returns None if not authenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return validate_token(authorization[7:])


# ─────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
def api_register(payload: RegisterPayload):
    return register_user(payload.email, payload.name, payload.password, payload.company_name or "")


@app.post("/api/auth/login")
def api_login(payload: LoginPayload):
    return login_user(payload.email, payload.password)


@app.post("/api/auth/logout")
def api_logout(authorization: Optional[str] = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    logout_user(token)
    return {"ok": True}


@app.get("/api/auth/me")
def api_me(authorization: Optional[str] = Header(None)):
    user_id = _current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True, "user": profile}


# ─────────────────────────────────────────────────────────────
# MAIN ASSESSMENT ENDPOINT
# ─────────────────────────────────────────────────────────────

@app.post("/api/run")
def run_assessment(
    payload: CarbonInputPayload,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Run the full Carbonaire pipeline.
    If authenticated, saves history and returns personalization context.
    """
    data_dict: Dict[str, Any] = {k: v for k, v in payload.dict().items() if v is not None}
    data: CarbonInputData = inputs_from_dict(data_dict)

    validation = validate_inputs(data)
    if validation["errors"]:
        return {
            "ok": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "info": validation["info"],
        }

    result   = run_calculation(data)
    result["validation"] = validation

    engine   = RuleEngine()
    findings = engine.evaluate(result, data)

    # ML v2 — full recommendation suite
    ml_out = recommender.recommend(result, data, findings)

    # Personalization — only if user is logged in
    user_id       = _current_user(authorization)
    personalization = None
    if user_id:
        save_assessment(user_id, data, result, ml_out)
        personalization = get_personalization_context(user_id)

    return {
        "ok": True,
        "company": {
            "company_name":   data.company_name,
            "industry_type":  data.industry_type,
            "location_state": data.location_state,
        },
        "emissions": {
            "monthly":           result["monthly"],
            "annual":            result["annual"],
            "scope_percentages": result["scope_percentages"],
            "scope1":            result["scope1"],
            "scope2":            result["scope2"],
            "scope3":            result["scope3"],
        },
        "intensity":   result["intensity"],
        "benchmark":   _benchmark_block(result),
        # Rule-based findings (legacy, still included)
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
        # ML v2 layer — all new features
        "ml": ml_out,
        # Personalization (null if not logged in)
        "personalization": personalization,
        "validation": validation,
    }


# ─────────────────────────────────────────────────────────────
# USER HISTORY ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/api/user/history")
def api_history(
    authorization: Optional[str] = Header(None),
    limit: int = 10,
):
    user_id = _current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    history = get_user_history(user_id, limit=limit)
    return {"ok": True, "history": history}


@app.get("/api/user/compare")
def api_compare(authorization: Optional[str] = Header(None)):
    """Return delta between last two assessments for the current user."""
    user_id = _current_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"ok": True, **get_personalization_context(user_id)}


@app.get("/api/user/learning-status")
def api_learning_status():
    """Public endpoint — shows continuous learning progress."""
    return {"ok": True, **get_learning_status()}


# ─────────────────────────────────────────────────────────────
# DOCUMENT UPLOAD (unchanged from v1)
# ─────────────────────────────────────────────────────────────

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
            return {"ok": False, "error": f"Unrecognised document type: {doc_type}"}
        return {"ok": True, "data": extracted_data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
