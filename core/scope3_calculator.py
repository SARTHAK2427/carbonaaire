"""
core/scope3_calculator.py
=========================
Calculates Scope 3 (value-chain) emissions for IT SMEs.

Categories covered:
  Cat 1  — Cloud / hosted services (usage-based or spend-based)
  Cat 2  — Devices lifecycle (capital goods embodied carbon, annualised)
  Cat 3  — T&D losses on purchased electricity
  Cat 4  — Purchased services / SaaS (spend-based EEIO)
  Cat 5  — On-premise server lifecycle (capital goods)

Formula references:
  Cloud    : Cloud_kWh × Cloud_EF ÷ 1000   (or spend × EEIO if no kWh)
  Devices  : (N × Lifecycle_EF) ÷ Useful_life  → annualised → ÷ 12 for monthly
  T&D      : Scope2_tco2e × 0.08
  Services : Spend_INR × Spend_EF

All results in tCO2e per MONTH unless stated.
"""

from core.emission_factors import SCOPE3_FACTORS, CLOUD_PROVIDER_EF, TD_LOSS_FACTOR_FORMULA
from core.input_schema import CarbonInputData


# ─────────────────────────────────────────────────────────────
# CLOUD  (Category 1)
# ─────────────────────────────────────────────────────────────

def _calc_cloud(data: CarbonInputData) -> dict:
    """
    Priority order:
      1. If cloud_kwh_per_month is provided → use kWh method
      2. Else if compute_hours_per_month → use provider EF × hours
      3. Else if monthly_bill_inr → use spend EEIO method
      4. Else → 0
    """
    ef = SCOPE3_FACTORS["cloud_ef"]
    method = "none"
    tco2e = 0.0
    detail = {}

    if data.cloud_kwh_per_month > 0:
        tco2e = (data.cloud_kwh_per_month * ef) / 1000
        method = "kwh_based"
        detail = {
            "cloud_kwh": data.cloud_kwh_per_month,
            "ef_kg_per_kwh": ef,
        }

    elif data.cloud_compute_hours_per_month > 0:
        provider_key = data.cloud_provider.lower() if data.cloud_provider else "default"
        provider_ef  = CLOUD_PROVIDER_EF.get(provider_key, CLOUD_PROVIDER_EF["default"])
        tco2e = data.cloud_compute_hours_per_month * provider_ef
        method = "compute_hour_based"
        detail = {
            "compute_hours": data.cloud_compute_hours_per_month,
            "provider_ef_kg_per_hour": provider_ef,
        }

    elif data.cloud_monthly_bill_inr > 0:
        spend_ef = SCOPE3_FACTORS["cloud_spend_ef"]
        tco2e = data.cloud_monthly_bill_inr * spend_ef
        method = "spend_based_eeio"
        detail = {
            "spend_inr": data.cloud_monthly_bill_inr,
            "spend_ef_kg_per_inr": spend_ef,
        }

    return {
        "tco2e":  round(tco2e, 6),
        "method": method,
        **detail,
    }


# ─────────────────────────────────────────────────────────────
# DEVICES  (Category 2 — embodied / lifecycle carbon)
# ─────────────────────────────────────────────────────────────

def _calc_devices(data: CarbonInputData) -> dict:
    """
    Annualised lifecycle emissions → divide by 12 for monthly figure.
    Formula: (N × Lifecycle_EF) ÷ Useful_life_years ÷ 12
    """
    f = SCOPE3_FACTORS

    laptop_annual   = (data.num_laptops        * f["laptop_lifecycle_ef"])   / f["laptop_useful_life"]
    desktop_annual  = (data.num_desktops       * f["desktop_lifecycle_ef"])  / f["desktop_useful_life"]
    server_annual   = (data.num_servers_onprem * f["server_lifecycle_ef"])   / f["server_useful_life"]
    monitor_annual  = (data.num_monitors       * f["monitor_lifecycle_ef"])  / f["monitor_useful_life"]

    total_annual_kg = laptop_annual + desktop_annual + server_annual + monitor_annual
    total_monthly_tco2e = total_annual_kg / 1000 / 12

    return {
        "laptop_annual_kg":   round(laptop_annual, 4),
        "desktop_annual_kg":  round(desktop_annual, 4),
        "server_annual_kg":   round(server_annual, 4),
        "monitor_annual_kg":  round(monitor_annual, 4),
        "total_annual_kg":    round(total_annual_kg, 4),
        "total_monthly_tco2e": round(total_monthly_tco2e, 6),
    }


# ─────────────────────────────────────────────────────────────
# T&D LOSSES  (Category 3)
# ─────────────────────────────────────────────────────────────

def _calc_td_losses(scope2_total_tco2e: float) -> dict:
    """
    T&D = Scope2 × TD_loss_factor (8% per formula)
    """
    tco2e = scope2_total_tco2e * TD_LOSS_FACTOR_FORMULA
    return {
        "tco2e":        round(tco2e, 6),
        "loss_factor":  TD_LOSS_FACTOR_FORMULA,
        "scope2_base":  round(scope2_total_tco2e, 6),
    }


# ─────────────────────────────────────────────────────────────
# PURCHASED SERVICES  (Category 4)
# ─────────────────────────────────────────────────────────────

def _calc_services(data: CarbonInputData) -> dict:
    spend_ef = SCOPE3_FACTORS["services_spend_ef"]
    tco2e = (data.purchased_services_spend_inr_per_month * spend_ef) / 1000
    return {
        "tco2e":              round(tco2e, 6),
        "spend_inr":          data.purchased_services_spend_inr_per_month,
        "ef_kg_per_inr":      spend_ef,
    }


# ─────────────────────────────────────────────────────────────
# MASTER SCOPE 3 FUNCTION
# ─────────────────────────────────────────────────────────────

def calculate_scope3(data: CarbonInputData, scope2_total_tco2e: float) -> dict:
    """
    Returns full Scope 3 breakdown and total.

    scope2_total_tco2e: pass the result from scope2_calculator
    (needed for T&D loss calculation).

    Returns:
    {
        "cloud":     { method, tco2e, ... },
        "devices":   { breakdown, total_monthly_tco2e },
        "td_losses": { tco2e, loss_factor },
        "services":  { tco2e, spend_inr },
        "total_tco2e": float,
    }
    """
    cloud    = _calc_cloud(data)
    devices  = _calc_devices(data)
    td       = _calc_td_losses(scope2_total_tco2e)
    services = _calc_services(data)

    total = (
        cloud["tco2e"]
        + devices["total_monthly_tco2e"]
        + td["tco2e"]
        + services["tco2e"]
    )

    return {
        "cloud":         cloud,
        "devices":       devices,
        "td_losses":     td,
        "services":      services,
        "total_tco2e":   round(total, 6),
    }
