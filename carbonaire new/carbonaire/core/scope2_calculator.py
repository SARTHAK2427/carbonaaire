"""
core/scope2_calculator.py
=========================
Calculates Scope 2 (purchased electricity) emissions.

Formula (CEA / India, location-based method):
  Scope2 = Electricity_kWh × (1 − Renewable%) × Grid_EF ÷ 1000
  → result in tCO2e/month

Grid EF is selected by state if available, else falls back to national default.
"""

from core.emission_factors import GRID_EF_DEFAULT, STATE_GRID_EF
from core.input_schema import CarbonInputData


def _get_grid_ef(state: str) -> float:
    """Return grid emission factor (kg CO2e/kWh) for the given state."""
    key = state.lower().strip().replace(" ", "_")
    return STATE_GRID_EF.get(key, STATE_GRID_EF["default"])


def calculate_scope2(data: CarbonInputData) -> dict:
    """
    Returns:
    {
        "grid_ef_used":           float,   # kg CO2e / kWh
        "renewable_fraction":     float,   # 0.0 – 1.0
        "effective_kwh":          float,   # kWh after subtracting renewables
        "gross_tco2e":            float,   # without renewables adjustment
        "total_tco2e":            float,   # with renewables adjustment
        "state":                  str,
    }
    All emission values in tCO2e/month.
    """
    grid_ef = _get_grid_ef(data.location_state)
    renewable_fraction = min(max(data.renewable_energy_percent / 100.0, 0.0), 1.0)

    # Gross (if no renewables)
    gross_tco2e = (data.electricity_kwh_per_month * grid_ef) / 1000

    # Net (with renewables offset)
    effective_kwh = data.electricity_kwh_per_month * (1 - renewable_fraction)
    net_tco2e = (effective_kwh * grid_ef) / 1000

    return {
        "grid_ef_used":       round(grid_ef, 4),
        "state":              data.location_state,
        "renewable_fraction": round(renewable_fraction, 4),
        "effective_kwh":      round(effective_kwh, 4),
        "gross_tco2e":        round(gross_tco2e, 6),
        "total_tco2e":        round(net_tco2e, 6),
    }
