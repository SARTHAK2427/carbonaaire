"""
utils/helpers.py
================
Shared utility functions used across Carbonaire modules.
"""

import os
import re
import shutil
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

try:
    from PIL import Image
    import pytesseract
    # Set Tesseract path: Environment variable > shutil.which > Default Windows path
    tesseract_exe = os.getenv('TESSERACT_CMD')
    if not tesseract_exe:
        tesseract_exe = shutil.which('tesseract')
    if not tesseract_exe:
        # Fallback to default Windows installation path
        default_win_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(default_win_path):
            tesseract_exe = default_win_path

    if tesseract_exe:
        pytesseract.pytesseract.tesseract_cmd = tesseract_exe
except ImportError:
    Image = None
    pytesseract = None


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
        industry_type                        = "IT",
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
        industry_type                          = "IT",
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
        industry_type                          = "IT",
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
    if pd is None:
        raise RuntimeError("pandas is not installed.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path, header=None)
    if df.empty:
        raise ValueError("Excel file is empty.")

    first_col_values = df.iloc[:, 0].astype(str).str.strip().tolist()
    known_fields = {
        "company_name", "industry_type", "location_state", "num_employees",
        "electricity_kwh_per_month", "annual_revenue_inr_cr"
    }
    col0_set = set(v.strip() for v in first_col_values)
    is_template_format = len(known_fields & col0_set) >= 2

    cleaned: Dict[str, Any] = {}

    if is_template_format:
        for _, row in df.iterrows():
            key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            val = row.iloc[1] if len(row) > 1 else None
            if not key or key.startswith("──") or key.startswith("Fill") or key == "Field" or key.startswith("🌿"):
                continue
            if pd.isna(val) or str(val).strip() == "" or str(val).strip() == "nan":
                continue
            if isinstance(val, str):
                v = val.strip()
                if v:
                    cleaned[key] = v
            else:
                cleaned[key] = val
    else:
        row = df.iloc[0].to_dict()
        for key, value in row.items():
            if isinstance(value, str):
                v = value.strip()
                if v:
                    cleaned[str(key)] = v
            elif not pd.isna(value):
                cleaned[str(key)] = value

    cleaned["uploaded_docs"] = [os.path.basename(path)]

    missing = []
    for field_name in _EXCEL_REQUIRED_FIELDS:
        if field_name not in cleaned or cleaned[field_name] is None:
            missing.append(field_name)
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))

    data = inputs_from_dict(cleaned)
    issues = validate_inputs(data)
    if issues["errors"]:
        raise ValueError("Excel data failed validation: " + "; ".join(issues["errors"]))

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
    if not os.path.exists(path):
        return ""

    text_parts: List[str] = []
    
    # 1. Try standard text extraction
    try:
        if pdfplumber:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    pt = page.extract_text() or ""
                    text_parts.append(pt)
    except Exception:
        pass

    full_text = "\n".join(text_parts).strip()
    
    # 2. If text is suspiciously small, fallback to OCR
    if len(full_text) < 100 and pytesseract and Image:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(path)
            ocr_parts = []
            # OCR first 3 pages only to keep it fast
            for i in range(min(len(doc), 3)):
                page = doc[i]
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_parts.append(pytesseract.image_to_string(img))
            doc.close()
            full_text = "\n".join(ocr_parts).strip()
        except Exception:
            pass

    return full_text


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


def _extract_text_from_image(path: str) -> str:
    if pytesseract is None or Image is None:
        raise RuntimeError(
            "pytesseract or Pillow is not installed. Please install dependencies (e.g. pip install pytesseract Pillow) and Tesseract OCR engine."
        )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    return pytesseract.image_to_string(Image.open(path))


def extract_from_electricity_document(path: str) -> Dict[str, Any]:
    text = _extract_text_from_pdf(path) if path.lower().endswith(".pdf") else (
           _extract_text_from_excel_generic(path) if path.lower().endswith((".xls", ".xlsx")) else
           _extract_text_from_image(path) if path.lower().endswith((".png", ".jpg", ".jpeg")) else "")

    result: Dict[str, Any] = {"uploaded_docs": [os.path.basename(path)]}
    
    # More robust Electricity patterns
    lowered = text.lower()
    
    # Pattern 1: Look for "Units: 1234" or "Total Units 1234" or "1234 kWh"
    # We clean up common noise like commas in numbers
    clean_text = re.sub(r"[,\s]+", " ", lowered)
    
    kwh_patterns = [
    re.compile(r"total\s*units\s*[=:\-\s]*(\d+(?:\.\d+)?)"),
    re.compile(r"units?\s*consumed\s*[=:\-\s]*(\d+(?:\.\d+)?)"),
    re.compile(r"billed\s*units\s*[=:\-\s]*(\d+(?:\.\d+)?)"),
    re.compile(r"kwh\s+[\d\-]+\s+[\d\.]+\s+[\d\-]+\s+[\d\.]+\s+[\d\.]+\s+\d+\s+(\d+(?:\.\d+)?)"),
    re.compile(r"1\.00\s+\d+\s+(\d+(?:\.\d+)?)"),
    re.compile(r"(\d+(?:\.\d+)?)\s*kwh"),
    
    ]
    
    for pat in kwh_patterns:
        m = pat.search(clean_text)
        if m:
            val = float(m.group(1))


            if val < 100000:

                result["electricity_kwh_per_month"] = val

                break

    # Look for location
    for state_name in _INDIAN_STATES:
        if state_name in lowered:
            result["location_state"] = state_name.replace(" ", "_")
            break

    return result


def extract_from_cloud_document(path: str) -> Dict[str, Any]:
    """
    Parse a cloud bill to infer:
      - cloud_provider
      - cloud_monthly_bill_inr
    """
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
    elif ext in (".xls", ".xlsx"):
        text = _extract_text_from_excel_generic(path)
    elif ext in (".png", ".jpg", ".jpeg"):
        text = _extract_text_from_image(path)
    else:
        raise ValueError("Unsupported cloud document type. Please upload PDF, Excel, or image.")

    result: Dict[str, Any] = {"uploaded_docs": [os.path.basename(path)]}
    text_lower = text.lower()

    # 1. Look for cloud provider
    providers = {"aws": ["aws", "amazon web services"], "gcp": ["gcp", "google cloud"], "azure": ["azure", "microsoft cloud"]}
    for provider_key, aliases in providers.items():
        if any(alias in text_lower for alias in aliases):
            result["cloud_provider"] = provider_key
            break

    # 2. Look for spending amount
    block = re.sub(r"[,\s]+", " ", text_lower)
    money_pattern = re.compile(r"(inr|rs\.?|₹|\$|usd)\s*(\d+(\.\d+)?)")
    match = money_pattern.search(block)
    
    if match:
        try:
            val = float(match.group(2))
            # Rough heuristic: if it was $ or USD, multiply by 83 to get INR
            currency = match.group(1).replace(".", "").strip()
            if currency in ("$", "usd"):
                val *= 83.0
            result["cloud_monthly_bill_inr"] = round(val, 2)
        except ValueError:
            pass

    return result


def extract_from_fuel_document(path: str) -> Dict[str, Any]:
    """
    Parse a fuel record to infer:
      - diesel_litres_per_month
      - petrol_litres_per_month
    """
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
    elif ext in (".xls", ".xlsx"):
        text = _extract_text_from_excel_generic(path)
    elif ext in (".png", ".jpg", ".jpeg"):
        text = _extract_text_from_image(path)
    else:
        raise ValueError("Unsupported fuel document type. Please upload PDF, Excel, or image.")

    result: Dict[str, Any] = {"uploaded_docs": [os.path.basename(path)]}
    block = re.sub(r"[,\s]+", " ", text.lower())

    diesel_pattern = re.compile(r"(\d+(\.\d+)?)\s*(litres?|liters?|ltrs?|l)\s*(of\s*)?diesel")
    petrol_pattern = re.compile(r"(\d+(\.\d+)?)\s*(litres?|liters?|ltrs?|l)\s*(of\s*)?petrol")

    match_diesel = diesel_pattern.search(block)
    if match_diesel:
        try:
            result["diesel_litres_per_month"] = float(match_diesel.group(1))
        except ValueError:
            pass

    match_petrol = petrol_pattern.search(block)
    if match_petrol:
        try:
            result["petrol_litres_per_month"] = float(match_petrol.group(1))
        except ValueError:
            pass

    return result


def extract_from_hardware_document(path: str) -> Dict[str, Any]:
    """
    Parse an IT invoice for:
      - num_laptops
      - num_desktops
      - num_servers_onprem
      - num_monitors
    """
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
    elif ext in (".xls", ".xlsx"):
        text = _extract_text_from_excel_generic(path)
    elif ext in (".png", ".jpg", ".jpeg"):
        text = _extract_text_from_image(path)
    else:
        raise ValueError("Unsupported hardware document type. Please upload PDF, Excel, or image.")

    result: Dict[str, Any] = {"uploaded_docs": [os.path.basename(path)]}
    block = re.sub(r"[,\s]+", " ", text.lower())

    patterns = {
        "num_laptops": re.compile(r"(?:qty|quantity)?\s*(\d+)\s*(?:x|units?)?\s*laptops?"),
        "num_desktops": re.compile(r"(?:qty|quantity)?\s*(\d+)\s*(?:x|units?)?\s*desktops?"),
        "num_servers_onprem": re.compile(r"(?:qty|quantity)?\s*(\d+)\s*(?:x|units?)?\s*servers?"),
        "num_monitors": re.compile(r"(?:qty|quantity)?\s*(\d+)\s*(?:x|units?)?\s*monitors?"),
    }

    for key, pattern in patterns.items():
        match = pattern.search(block)
        if match:
            try:
                result[key] = int(match.group(1))
            except ValueError:
                pass

    return result
