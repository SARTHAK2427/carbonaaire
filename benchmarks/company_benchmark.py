"""
benchmarks/company_benchmark.py
================================
Placeholder module for real large-company benchmark data.

STATUS: Future implementation — no real data available yet.

When real company data is available, add entries to COMPANY_DATA
following the structure below. The report generator will automatically
display comparisons if data is present.

Data should come from:
  - Published BRSR reports (SEBI mandate for top-1000 listed companies)
  - GRI sustainability reports
  - CDP (Carbon Disclosure Project) disclosures
  - Company investor presentations

HOW TO ADD A COMPANY:
  Add to COMPANY_DATA:
  "Company Name": {
      "tco2e_per_cr":     float,    # tCO2e per ₹ Crore revenue (annual)
      "total_tco2e":      float,    # Total annual tCO2e
      "revenue_cr":       float,    # Annual revenue in ₹ Crore
      "scope1_tco2e":     float,
      "scope2_tco2e":     float,
      "scope3_tco2e":     float,    # If disclosed
      "year":             int,      # Reporting year
      "employees":        int,
      "source":           str,      # e.g. "BRSR FY2023", "CDP 2023"
      "notes":            str,      # Any caveats
  }
"""

# ── Company benchmark data ────────────────────────────────────────────────────
# Currently empty — to be populated with real data
COMPANY_DATA = {
    # ── Example structure (commented out — replace with real data) ──
    # "Infosys": {
    #     "tco2e_per_cr":     1.8,
    #     "total_tco2e":      262000,
    #     "revenue_cr":       146767,
    #     "scope1_tco2e":     15000,
    #     "scope2_tco2e":     85000,
    #     "scope3_tco2e":     162000,
    #     "year":             2023,
    #     "employees":        343234,
    #     "source":           "Infosys ESG Report FY2023 / BRSR",
    #     "notes":            "Includes significant renewable PPA purchases",
    # },
}

# ── Status flag ──────────────────────────────────────────────────────────────
COMPANY_BENCHMARKS_AVAILABLE = len(COMPANY_DATA) > 0


def get_company_benchmark(company_name: str) -> dict | None:
    """
    Retrieve benchmark data for a named company.
    Returns None if data is not available.
    """
    return COMPANY_DATA.get(company_name)


def list_available_companies() -> list:
    """Return list of companies for which benchmark data exists."""
    return list(COMPANY_DATA.keys())


def get_company_comparison(user_intensity: float) -> list:
    """
    Compare user's intensity against all available company benchmarks.
    Returns a list of comparison dicts sorted by company intensity ascending.
    """
    comparisons = []
    for name, data in COMPANY_DATA.items():
        comparisons.append({
            "company":        name,
            "intensity":      data["tco2e_per_cr"],
            "year":           data.get("year"),
            "user_vs_company": round(user_intensity - data["tco2e_per_cr"], 3),
            "user_better":    user_intensity < data["tco2e_per_cr"],
            "source":         data.get("source", ""),
        })
    comparisons.sort(key=lambda x: x["intensity"])
    return comparisons
