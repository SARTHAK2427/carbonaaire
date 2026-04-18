"""
core/scope1_calculator.py
=========================
Calculates Scope 1 (direct / on-site combustion) emissions.

Formula (MoEFCC / India):
  Scope1_fuel = Fuel_consumed (unit) × Emission_Factor (kgCO2e/unit) ÷ 1000
  → result in tCO2e/month

Final Scope 1 = sum of all fuel types.
"""

from core.emission_factors import SCOPE1_FACTORS
from core.input_schema import CarbonInputData


def calculate_scope1(data: CarbonInputData) -> dict:
    """
    Returns a breakdown dict:
    {
        "diesel_tco2e":       float,
        "petrol_tco2e":       float,
        "natural_gas_tco2e":  float,
        "lpg_tco2e":          float,
        "total_tco2e":        float,
        "breakdown":          { fuel: {"consumed": x, "ef": y, "tco2e": z} }
    }
    All values are in tCO2e per month.
    """
    breakdown = {}

    # ── Diesel ───────────────────────────────────────────────────
    diesel_ef = SCOPE1_FACTORS["diesel"]["ef"]
    diesel_tco2e = (data.diesel_litres_per_month * diesel_ef) / 1000
    breakdown["diesel"] = {
        "consumed": data.diesel_litres_per_month,
        "unit": SCOPE1_FACTORS["diesel"]["unit"],
        "ef_kg_per_unit": diesel_ef,
        "tco2e": round(diesel_tco2e, 6),
    }

    # ── Petrol ───────────────────────────────────────────────────
    petrol_ef = SCOPE1_FACTORS["petrol"]["ef"]
    petrol_tco2e = (data.petrol_litres_per_month * petrol_ef) / 1000
    breakdown["petrol"] = {
        "consumed": data.petrol_litres_per_month,
        "unit": SCOPE1_FACTORS["petrol"]["unit"],
        "ef_kg_per_unit": petrol_ef,
        "tco2e": round(petrol_tco2e, 6),
    }

    # ── Natural Gas ───────────────────────────────────────────────
    gas_ef = SCOPE1_FACTORS["natural_gas"]["ef"]
    gas_tco2e = (data.natural_gas_m3_per_month * gas_ef) / 1000
    breakdown["natural_gas"] = {
        "consumed": data.natural_gas_m3_per_month,
        "unit": SCOPE1_FACTORS["natural_gas"]["unit"],
        "ef_kg_per_unit": gas_ef,
        "tco2e": round(gas_tco2e, 6),
    }

    # ── LPG ──────────────────────────────────────────────────────
    lpg_ef = SCOPE1_FACTORS["lpg"]["ef"]
    lpg_tco2e = (data.lpg_litres_per_month * lpg_ef) / 1000
    breakdown["lpg"] = {
        "consumed": data.lpg_litres_per_month,
        "unit": SCOPE1_FACTORS["lpg"]["unit"],
        "ef_kg_per_unit": lpg_ef,
        "tco2e": round(lpg_tco2e, 6),
    }

    total = diesel_tco2e + petrol_tco2e + gas_tco2e + lpg_tco2e

    return {
        "diesel_tco2e":      round(diesel_tco2e, 6),
        "petrol_tco2e":      round(petrol_tco2e, 6),
        "natural_gas_tco2e": round(gas_tco2e, 6),
        "lpg_tco2e":         round(lpg_tco2e, 6),
        "total_tco2e":       round(total, 6),
        "breakdown":         breakdown,
    }
