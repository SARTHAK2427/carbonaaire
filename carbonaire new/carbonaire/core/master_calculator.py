"""
core/master_calculator.py
=========================
Orchestrates Scope 1, 2, 3 calculators and produces the final
consolidated emission result.

Master equation:
  Total CO2e = Scope 1 + Scope 2 + Scope 3

Output includes:
  - Monthly totals (tCO2e/month)
  - Annualised totals (tCO2e/year)
  - Per-employee intensity (tCO2e/employee/year)
  - Revenue intensity (tCO2e/₹Cr/year) — for benchmark comparison
  - Scope-wise percentage breakdown
"""

from core.input_schema import CarbonInputData, validate_inputs
from core.scope1_calculator import calculate_scope1
from core.scope2_calculator import calculate_scope2
from core.scope3_calculator import calculate_scope3


def run_calculation(data: CarbonInputData) -> dict:
    """
    Main entry point.
    Returns a comprehensive result dict ready for reporting and rule-engine.

    Raises ValueError if there are hard validation errors.
    """
    # ── Validate ─────────────────────────────────────────────────
    validation = validate_inputs(data)
    if validation["errors"]:
        raise ValueError(
            "Input validation failed:\n" +
            "\n".join(f"  ✗ {e}" for e in validation["errors"])
        )

    # ── Calculate scopes ─────────────────────────────────────────
    s1 = calculate_scope1(data)
    s2 = calculate_scope2(data)
    s3 = calculate_scope3(data, scope2_total_tco2e=s2["total_tco2e"])

    # ── Monthly totals ────────────────────────────────────────────
    scope1_monthly = s1["total_tco2e"]
    scope2_monthly = s2["total_tco2e"]
    scope3_monthly = s3["total_tco2e"]
    total_monthly  = scope1_monthly + scope2_monthly + scope3_monthly

    # ── Annual totals ─────────────────────────────────────────────
    scope1_annual  = scope1_monthly * 12
    scope2_annual  = scope2_monthly * 12
    scope3_annual  = scope3_monthly * 12
    total_annual   = total_monthly  * 12

    # ── Intensity metrics ─────────────────────────────────────────
    per_employee = (
        total_annual / data.num_employees
        if data.num_employees > 0 else None
    )
    revenue_intensity = (
        total_annual / data.annual_revenue_inr_cr
        if data.annual_revenue_inr_cr > 0 else None
    )

    # ── Percentage breakdown ──────────────────────────────────────
    def pct(part, whole):
        return round((part / whole * 100), 2) if whole > 0 else 0.0

    scope1_pct = pct(scope1_monthly, total_monthly)
    scope2_pct = pct(scope2_monthly, total_monthly)
    scope3_pct = pct(scope3_monthly, total_monthly)

    return {
        # Raw scope results (full breakdown available inside each)
        "scope1": s1,
        "scope2": s2,
        "scope3": s3,

        # Summary — monthly (tCO2e/month)
        "monthly": {
            "scope1_tco2e": round(scope1_monthly, 4),
            "scope2_tco2e": round(scope2_monthly, 4),
            "scope3_tco2e": round(scope3_monthly, 4),
            "total_tco2e":  round(total_monthly,  4),
        },

        # Summary — annual (tCO2e/year)
        "annual": {
            "scope1_tco2e": round(scope1_annual, 4),
            "scope2_tco2e": round(scope2_annual, 4),
            "scope3_tco2e": round(scope3_annual, 4),
            "total_tco2e":  round(total_annual,  4),
        },

        # Intensity metrics
        "intensity": {
            "per_employee_tco2e_per_year":  round(per_employee, 4)      if per_employee      is not None else None,
            "revenue_intensity_tco2e_per_cr": round(revenue_intensity, 4) if revenue_intensity is not None else None,
        },

        # Percentage breakdown
        "scope_percentages": {
            "scope1_pct": scope1_pct,
            "scope2_pct": scope2_pct,
            "scope3_pct": scope3_pct,
        },

        # Validation notes
        "validation": validation,

        # Input echo (for report)
        "input_summary": {
            "company_name":       data.company_name,
            "industry_type":      data.industry_type,
            "location_state":     data.location_state,
            "num_employees":      data.num_employees,
            "annual_revenue_cr":  data.annual_revenue_inr_cr,
        },
    }
