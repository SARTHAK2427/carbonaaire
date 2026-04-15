"""
utils/helpers.py
================
Shared utility functions used across Carbonaire modules.
"""

import os
import re
from typing import Any, Dict, List, Optional

from core.input_schema import CarbonInputData, inputs_from_dict, validate_inputs

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None  # type: ignore

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pdfplumber = None  # type: ignore


def kwh_to_tco2e(kwh: float, ef_kg_per_kwh: float) -> float:
    """Convert kWh to tCO2e using a given emission factor."""
    return (kwh * ef_kg_per_kwh) / 1000


def litres_to_tco2e(litres: float, ef_kg_per_litre: float) -> float:
    """Convert fuel litres to tCO2e."""
    return (litres * ef_kg_per_litre) / 1000


def annualise(monthly_value: float, months: int = 12) -> float:
    """Convert a monthly value to annual."""
    return monthly_value * months


def per_employee(annual_value: float, num_employees: int) -> float | None:
    """Calculate per-employee metric. Returns None if employees = 0."""
    if num_employees <= 0:
        return None
    return annual_value / num_employees


def revenue_intensity(annual_tco2e: float, revenue_inr_cr: float) -> float | None:
    """Calculate tCO2e per ₹ Crore. Returns None if revenue = 0."""
    if revenue_inr_cr <= 0:
        return None
    return annual_tco2e / revenue_inr_cr


def normalise_state_name(state: str) -> str:
    """Normalise state name for lookup in STATE_GRID_EF."""
    return state.lower().strip().replace(" ", "_").replace("-", "_")


def build_demo_input() -> CarbonInputData:
    """
    Returns a realistic demo CarbonInputData for a mid-sized Indian IT SME.
    Used by: main.py --demo, tests
    """
    return CarbonInputData(
        company_name                         = "TechNova Solutions Pvt Ltd",
        industry_type                        = "IT/ITES",
        location_state                       = "karnataka",
        num_employees                        = 120,
        working_hours_per_day                = 9.0,
        annual_revenue_inr_cr                = 25.0,

        # Scope 1 — moderate diesel generator, small petrol fleet
        diesel_litres_per_month              = 600.0,
        petrol_litres_per_month              = 150.0,
        natural_gas_m3_per_month             = 0.0,
        lpg_litres_per_month                 = 0.0,
        power_backup_runtime_hours           = 40.0,

        # Scope 2 — medium office + server room
        electricity_kwh_per_month            = 18000.0,
        renewable_energy_percent             = 15.0,

        # On-premise server
        server_rack_count                    = 4,
        server_operating_hours_per_day       = 24.0,
        server_arrangement                   = "hot_aisle_cold_aisle",
        server_area_sqft                     = 400.0,

        # Scope 3 — devices
        num_laptops                          = 110,
        num_desktops                         = 10,
        num_servers_onprem                   = 20,
        num_monitors                         = 120,

        # Scope 3 — cloud (AWS, spend-based)
        cloud_provider                       = "aws",
        cloud_monthly_bill_inr               = 80000.0,
        cloud_compute_hours_per_month        = 0.0,
        cloud_kwh_per_month                  = 0.0,

        # Scope 3 — purchased services
        purchased_services_spend_inr_per_month = 50000.0,

        cooling_system_type                  = "precision_cooling",
        uploaded_docs                        = ["electricity_bill_march.pdf"],
    )


def build_minimal_input() -> CarbonInputData:
    """
    Minimal valid input — only electricity provided.
    Used for testing error/warning paths.
    """
    return CarbonInputData(
        company_name              = "Minimal Test Co",
        electricity_kwh_per_month = 5000.0,
        location_state            = "delhi",
    )


def build_excellent_input() -> CarbonInputData:
    """
    Best-case scenario — high renewables, no diesel, efficient cloud.
    Should land in 'Excellent' benchmark band.
    """
    return CarbonInputData(
        company_name                           = "GreenTech India",
        industry_type                          = "IT/ITES",
        location_state                         = "karnataka",
        num_employees                          = 100,
        annual_revenue_inr_cr                  = 20.0,
        diesel_litres_per_month                = 0.0,
        petrol_litres_per_month                = 50.0,
        electricity_kwh_per_month              = 12000.0,
        renewable_energy_percent               = 80.0,
        server_rack_count                      = 2,
        server_arrangement                     = "direct_liquid_cooling",
        num_laptops                            = 90,
        num_desktops                           = 10,
        num_servers_onprem                     = 8,
        num_monitors                           = 100,
        cloud_provider                         = "gcp",
        cloud_kwh_per_month                    = 500.0,
        purchased_services_spend_inr_per_month = 20000.0,
    )


def build_high_emission_input() -> CarbonInputData:
    """
    High-emission scenario — poor practices.
    Should land in 'High' / 'Carbon Heavy' band.
    """
    return CarbonInputData(
        company_name                           = "OldSchool IT",
        industry_type                          = "IT/ITES",
        location_state                         = "rajasthan",
        num_employees                          = 80,
        annual_revenue_inr_cr                  = 12.0,
        diesel_litres_per_month                = 1500.0,
        petrol_litres_per_month                = 400.0,
        natural_gas_m3_per_month               = 100.0,
        electricity_kwh_per_month              = 30000.0,
        renewable_energy_percent               = 0.0,
        server_rack_count                      = 8,
        server_arrangement                     = "stacked_high_density",
        num_laptops                            = 70,
        num_desktops                           = 30,
        num_servers_onprem                     = 40,
        num_monitors                           = 80,
        cloud_provider                         = "aws",
        cloud_monthly_bill_inr                 = 300000.0,
        purchased_services_spend_inr_per_month = 200000.0,
    )


# ─────────────────────────────────────────────────────────────
# EXCEL + DOCUMENT PARSING HELPERS
# ─────────────────────────────────────────────────────────────

_EXCEL_REQUIRED_FIELDS: List[str] = [
    # Core company and activity fields expected in the official template
    "company_name",
    "industry_type",
    "location_state",
    "num_employees",
    "annual_revenue_inr_cr",
    # Minimum technical requirement for the model to run
    "electricity_kwh_per_month",
]


def load_inputs_from_excel(path: str) -> CarbonInputData:
    """
    Load CarbonInputData from a single-row Excel file.

    - Expects at least the required fields in _EXCEL_REQUIRED_FIELDS.
    - Column names should match CarbonInputData field names (snake_case).
    - Raises ValueError with a clear message if requirements are not met.
    """
    if pd is None:
        raise RuntimeError(
            "pandas is not installed. Please install dependencies (e.g. pip install -r requirements.txt)."
        )

    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path)  # type: ignore[arg-type]
    if df.empty:
        raise ValueError("Excel file is empty.")

    row = df.iloc[0].to_dict()

    # Check required fields presence and non-null
    missing: List[str] = []
    for field_name in _EXCEL_REQUIRED_FIELDS:
        if field_name not in row or (pd.isna(row[field_name]) if pd is not None else row[field_name] is None):  # type: ignore[func-returns-value]
            missing.append(field_name)

    if missing:
        raise ValueError(
            "Excel file is missing required fields or values: "
            + ", ".join(missing)
        )

    cleaned: Dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, str):
            v = value.strip()
            if v == "":
                continue
            cleaned[key] = v
        else:
            cleaned[key] = value

    cleaned["uploaded_docs"] = [os.path.basename(path)]

    data = inputs_from_dict(cleaned)
    issues = validate_inputs(data)
    if issues["errors"]:
        raise ValueError(
            "Excel data failed validation: " + "; ".join(issues["errors"])
        )

    return data


_INDIAN_STATES: List[str] = [
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
    "andaman and nicobar islands",
    "chandigarh",
    "dadra and nagar haveli and daman and diu",
    "delhi",
    "jammu and kashmir",
    "ladakh",
    "lakshadweep",
    "puducherry",
]


def _extract_text_from_pdf(path: str) -> str:
    if pdfplumber is None:
        raise RuntimeError(
            "pdfplumber is not installed. Please install dependencies (e.g. pip install -r requirements.txt)."
        )
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")

    text_parts: List[str] = []
    with pdfplumber.open(path) as pdf:  # type: ignore[call-arg]
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_text_from_excel_generic(path: str) -> str:
    if pd is None:
        raise RuntimeError(
            "pandas is not installed. Please install dependencies (e.g. pip install -r requirements.txt)."
        )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path, header=None)  # type: ignore[arg-type]
    values: List[str] = []
    for value in df.to_numpy().flatten():
        if pd.isna(value):  # type: ignore[call-arg]
            continue
        values.append(str(value))
    return "\n".join(values)


def extract_from_electricity_document(path: str) -> Dict[str, Any]:
    """
    Parse an electricity bill (PDF or Excel) and try to infer:
      - electricity_kwh_per_month
      - location_state
      - uploaded_docs entry

    The parsing is heuristic; if values cannot be inferred reliably, the
    corresponding keys will simply be absent from the returned dict.
    """
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
    elif ext in (".xls", ".xlsx"):
        text = _extract_text_from_excel_generic(path)
    else:
        raise ValueError("Unsupported electricity document type. Please upload a PDF or Excel file.")

    result: Dict[str, Any] = {"uploaded_docs": [os.path.basename(path)]}

    # Try to extract kWh-like numbers (e.g. "1234 kWh" or "1234 units")
    numeric_block = re.sub(r"[,\s]+", " ", text.lower())
    kwh_pattern = re.compile(r"(\d+(\.\d+)?)\s*(kwh|unit[s]?)")
    match = kwh_pattern.search(numeric_block)
    if match:
        try:
            result["electricity_kwh_per_month"] = float(match.group(1))
        except ValueError:
            pass

    # Try to infer location_state by looking for any known Indian state name
    lowered = text.lower()
    for state_name in _INDIAN_STATES:
        if state_name in lowered:
            result["location_state"] = state_name.replace(" ", "_")
            break

    return result
