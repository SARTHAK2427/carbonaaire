"""
benchmarks/industry_benchmark.py
=================================
Indian IT/ITES SME industry benchmarks derived from BRSR disclosures
and CEA data, as specified in the Carbonaire benchmark document.

Benchmark metric: tCO2e per ₹ Crore annual revenue

Derivation (from industry_benchmark.docx):
  Base (BRSR Scope 1+2 median)        : 2.00 tCO2e/₹Cr
  + T&D losses (Scope 3, CEA 18%)     : +0.32
  + Devices lifecycle (LCA)           : +0.25
  + Cloud services (spend proxy)      : +0.40
  + Purchased services (EEIO)         : +0.15
  ──────────────────────────────────────────
  Industry median                     : 3.12 → rounded to 3.1

HOW TO UPDATE:
  - Change PERFORMANCE_BANDS to adjust band thresholds.
  - Change BENCHMARK_DERIVATION if new data becomes available.
  - IDEAL_BENCHMARK represents the top-quartile / best-in-class target.
"""

# ── Core benchmark figure ─────────────────────────────────────────────────────
BENCHMARK_MEDIAN_TCO2E_PER_CR = 3.1    # Industry median (tCO2e per ₹ Crore)
BENCHMARK_BASE_SCOPE1_2       = 2.0    # BRSR Scope 1+2 median
BENCHMARK_BOUNDARY            = "Scope 1 + Scope 2 + Selected Scope 3"

# Ideal (top-quartile, best-in-class) — used for gap analysis
IDEAL_BENCHMARK = {
    "tco2e_per_cr": 2.4,
    "description":  "Top-quartile Indian IT SME performance (BRSR excellent band)",
    "boundary":     BENCHMARK_BOUNDARY,
}

# ── Performance bands (tCO2e / ₹ Crore) ──────────────────────────────────────
# Aligned with Carbonaire scoring:
#   Green      < 2.4
#   Efficient  2.4 – 3.0
#   Average    3.0 – 3.6
#   Carbon heavy > 3.6
PERFORMANCE_BANDS = [
    {"band": "Green",         "min": 0.0,  "max": 2.4,   "color": "green"},
    {"band": "Efficient",     "min": 2.4,  "max": 3.0,   "color": "lightgreen"},
    {"band": "Average",       "min": 3.0,  "max": 3.6,   "color": "yellow"},
    {"band": "Carbon heavy",  "min": 3.6,  "max": 9999,  "color": "red"},
]

# ── Derivation breakdown (for transparency / display) ────────────────────────
BENCHMARK_DERIVATION = [
    {"component": "Scope 1 + 2 (BRSR median)",           "value": 2.00, "source": "SEBI BRSR NIC-62"},
    {"component": "T&D losses (Scope 3 Cat 3, CEA 18%)", "value": 0.32, "source": "CEA grid loss data"},
    {"component": "Devices lifecycle (LCA, laptops)",    "value": 0.25, "source": "LCA / GHG Protocol"},
    {"component": "Cloud services (spend proxy)",        "value": 0.40, "source": "EEIO / cloud proxy"},
    {"component": "Purchased services (EEIO)",           "value": 0.15, "source": "EEIO models"},
]

# ── Comparison table ─────────────────────────────────────────────────────────
BOUNDARY_COMPARISON = [
    {"boundary": "Scope 1 + 2 only",              "benchmark": 2.0},
    {"boundary": "Your selected Scope 3 (partial)","benchmark": 3.1},
    {"boundary": "Full Scope 3 (global services)","benchmark": "3.5 – 4.0"},
]

# ── Future: Big company real-time data placeholder ───────────────────────────
# (will be populated when real company data is available)
COMPANY_BENCHMARKS = {
    # Example structure — to be filled in company_benchmark.py
    # "Infosys": {"tco2e_per_cr": ..., "year": ..., "source": "..."},
}


# ── Helper functions ──────────────────────────────────────────────────────────

def get_performance_band(tco2e_per_cr: float) -> str:
    """Return the performance band label for a given intensity."""
    for band in PERFORMANCE_BANDS:
        if band["min"] <= tco2e_per_cr < band["max"]:
            return band["band"]
    return "High"


def get_ideal_target_tco2e(annual_revenue_inr_cr: float) -> float:
    """
    Calculate the ideal annual tCO2e target based on revenue.
    ideal_tco2e = IDEAL_BENCHMARK × revenue_cr
    """
    return IDEAL_BENCHMARK["tco2e_per_cr"] * annual_revenue_inr_cr


def get_benchmark_summary(intensity: float) -> dict:
    """
    Full benchmark summary for a given intensity value.
    Returns all fields needed for the report.
    """
    band = get_performance_band(intensity)
    gap_to_median = round(intensity - BENCHMARK_MEDIAN_TCO2E_PER_CR, 3)
    gap_to_ideal  = round(intensity - IDEAL_BENCHMARK["tco2e_per_cr"], 3)

    return {
        "intensity_tco2e_per_cr":  round(intensity, 3),
        "industry_median":         BENCHMARK_MEDIAN_TCO2E_PER_CR,
        "ideal_target":            IDEAL_BENCHMARK["tco2e_per_cr"],
        "performance_band":        band,
        "gap_to_median":           gap_to_median,
        "gap_to_ideal":            gap_to_ideal,
        "above_median":            gap_to_median > 0,
        "above_ideal":             gap_to_ideal  > 0,
        "derivation":              BENCHMARK_DERIVATION,
        "boundary":                BENCHMARK_BOUNDARY,
    }
