from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.input_schema import CarbonInputData, inputs_from_dict, validate_inputs
from core.master_calculator import run_calculation
from rules.rule_engine import RuleEngine
from utils.report_generator import _benchmark_block


app = FastAPI(title="Carbonaire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/api/run")
def run_assessment(payload: CarbonInputPayload) -> Dict[str, Any]:
    """
    Run the full Carbonaire pipeline from JSON input and return
    dashboard-friendly JSON.
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

    result = run_calculation(data)
    result["validation"] = validation

    engine = RuleEngine()
    findings = engine.evaluate(result, data)

    return {
        "ok": True,
        "company": {
            "company_name": data.company_name,
            "industry_type": data.industry_type,
            "location_state": data.location_state,
        },
        "emissions": {
            "monthly": result["monthly"],
            "annual": result["annual"],
            "scope_percentages": result["scope_percentages"],
            "scope1": result["scope1"],
            "scope2": result["scope2"],
            "scope3": result["scope3"],
        },
        "intensity": result["intensity"],
        "benchmark": _benchmark_block(result),
        "findings": [
            {
                "severity": f.severity.name,
                "severity_value": f.severity.value,
                "scope": f.scope,
                "category": f.category,
                "message": f.message,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "validation": validation,
    }

