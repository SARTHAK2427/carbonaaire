"""
core/input_schema.py
====================
Defines the full input data model for Carbonaire.
All inputs from the workflow are captured here as a structured dataclass.

HOW TO UPDATE:
  - Add a new field to CarbonInputData with a default of None (optional)
    or a sensible default value.
  - Add validation logic to validate_inputs() if needed.
  - The calculators will automatically receive the new field.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class CarbonInputData:
    """
    Complete input data collected from the user.
    All monetary values are in INR (₹).
    All energy values are per MONTH unless stated.
    """

    # ── Company / General Info ──────────────────────────────────
    company_name: str = "Unknown Company"
    industry_type: str = "IT"          # e.g. IT, Manufacturing, etc.
    location_state: str = "default"         # Indian state (for state grid EF)
    num_employees: int = 0                  # Total headcount
    working_hours_per_day: float = 8.0      # General working hours/day
    annual_revenue_inr_cr: float = 0.0      # Annual revenue in ₹ Crore (for benchmark)

    # ── SCOPE 1  —  Direct Fuel Consumption (per month) ─────────
    diesel_litres_per_month: float = 0.0    # Litres of diesel (generator, vehicles)
    petrol_litres_per_month: float = 0.0    # Litres of petrol (vehicles)
    natural_gas_m3_per_month: float = 0.0   # m³ of natural gas
    lpg_litres_per_month: float = 0.0       # Litres of LPG
    power_backup_runtime_hours: float = 0.0 # Hours/month backup generator runs

    # ── SCOPE 2  —  Electricity (per month) ─────────────────────
    electricity_kwh_per_month: float = 0.0  # Total grid electricity consumed
    renewable_energy_percent: float = 0.0   # % of electricity from renewables (0–100)

    # ── Server / Data Centre (on-premise) ────────────────────────
    server_rack_count: int = 0
    server_operating_hours_per_day: float = 24.0
    server_arrangement: str = "default"     # hot_aisle_cold_aisle / stacked_high_density
                                            # / direct_liquid_cooling / custom / default
    server_area_sqft: float = 0.0          # Area occupied by servers in sq ft
    server_model: str = ""                 # e.g. "Dell PowerEdge R750" (optional)

    # ── SCOPE 3  —  Devices (capital goods) ─────────────────────
    num_laptops: int = 0
    num_desktops: int = 0
    num_servers_onprem: int = 0             # On-premise servers
    num_monitors: int = 0

    # ── SCOPE 3  —  Cloud Services ───────────────────────────────
    cloud_provider: str = "none"            # aws / azure / gcp / none
    cloud_monthly_bill_inr: float = 0.0    # Monthly cloud spend in INR
    cloud_compute_hours_per_month: float = 0.0  # Alternative: compute hours
    cloud_kwh_per_month: float = 0.0       # If kWh data is available directly

    # ── SCOPE 3  —  Purchased Services ──────────────────────────
    purchased_services_spend_inr_per_month: float = 0.0  # SaaS, outsourced, etc.

    # ── Cooling (server room) ─────────────────────────────────────
    cooling_system_type: str = "default"    # ac / precision_cooling / free_cooling / default

    # ── Documents uploaded (filenames, for audit trail) ──────────
    uploaded_docs: List[str] = field(default_factory=list)
    # e.g. ["electricity_bill_jan.pdf", "diesel_record.xlsx"]


def validate_inputs(data: CarbonInputData) -> Dict[str, List[str]]:
    """
    Validates inputs and returns a dict:
      {
        "errors":   [...],   # must fix before calculation
        "warnings": [...],   # calculation proceeds but flag these
        "info":     [...],   # informational notes
      }
    """
    errors   = []
    warnings = []
    info     = []

    # ── Required fields ──────────────────────────────────────────
    if data.electricity_kwh_per_month <= 0:
        errors.append("Electricity consumption (kWh/month) is required and must be > 0.")

    if data.num_employees <= 0:
        warnings.append("Number of employees is 0. Per-employee intensity cannot be calculated.")

    if data.annual_revenue_inr_cr <= 0:
        warnings.append(
            "Annual revenue is 0. Benchmark comparison (tCO2e/₹Cr) cannot be calculated."
        )

    # ── Range checks ─────────────────────────────────────────────
    if not (0 <= data.renewable_energy_percent <= 100):
        errors.append("Renewable energy % must be between 0 and 100.")

    if data.working_hours_per_day > 24:
        errors.append("Working hours per day cannot exceed 24.")

    if data.server_operating_hours_per_day > 24:
        errors.append("Server operating hours per day cannot exceed 24.")

    # ── Consistency checks ────────────────────────────────────────
    if data.cloud_provider not in ("aws", "azure", "gcp", "none", ""):
        warnings.append(
            f"Unrecognised cloud provider '{data.cloud_provider}'. "
            "Using default emission factor."
        )

    if data.cloud_monthly_bill_inr == 0 and data.cloud_compute_hours_per_month == 0 \
            and data.cloud_kwh_per_month == 0 and data.cloud_provider != "none":
        warnings.append(
            "Cloud provider is set but no cloud usage data (bill/hours/kWh) provided. "
            "Cloud Scope 3 will be 0."
        )

    if data.diesel_litres_per_month > 0 and data.power_backup_runtime_hours == 0:
        info.append(
            "Diesel usage detected but power backup runtime is 0. "
            "Providing runtime hours improves accuracy."
        )

    if data.server_rack_count > 0 and data.num_servers_onprem == 0:
        info.append(
            "Server racks are listed but number of on-premise servers is 0. "
            "Lifecycle emissions for servers cannot be calculated."
        )

    valid_arrangements = {
        "hot_aisle_cold_aisle", "stacked_high_density",
        "direct_liquid_cooling", "custom", "default", ""
    }
    if data.server_arrangement not in valid_arrangements:
        warnings.append(
            f"Unrecognised server arrangement '{data.server_arrangement}'. "
            "Using default PUE."
        )

    return {"errors": errors, "warnings": warnings, "info": info}


def inputs_from_dict(d: dict) -> CarbonInputData:
    """
    Convenience function: build a CarbonInputData from a plain dictionary.
    Unknown keys are ignored. Useful for API / form submissions.
    """
    fields = CarbonInputData.__dataclass_fields__.keys()
    filtered = {k: v for k, v in d.items() if k in fields}
    return CarbonInputData(**filtered)
