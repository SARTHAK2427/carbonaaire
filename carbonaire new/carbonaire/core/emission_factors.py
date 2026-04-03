"""
core/emission_factors.py
========================
Single source of truth for ALL emission factors used in Carbonaire.

Sources:
  - CEA  : Central Electricity Authority, India
  - MoEFCC: Ministry of Environment, Forest and Climate Change, India
  - BRSR : Business Responsibility & Sustainability Report (SEBI)
  - LCA  : Life Cycle Assessment studies
  - EEIO : Environmentally Extended Input-Output models

HOW TO UPDATE:
  - To add a new fuel type → add a key to SCOPE1_FACTORS
  - To add a new state grid EF → add to STATE_GRID_EF
  - To change any factor → update the "ef" / "value" field here only.
    All calculators will automatically pick up the change.
"""

# ──────────────────────────────────────────────────────────────
# SCOPE 1  —  Direct Combustion Emission Factors
# Source: MoEFCC National GHG Inventory / India
# Unit: kg CO2e per litre (or per m³ for gas)
# ──────────────────────────────────────────────────────────────
SCOPE1_FACTORS = {
    "diesel": {
        "ef": 2.68,          # kg CO2e / litre
        "unit": "litres",
        "source": "MoEFCC National GHG Inventory"
    },
    "petrol": {
        "ef": 2.31,          # kg CO2e / litre
        "unit": "litres",
        "source": "MoEFCC"
    },
    "natural_gas": {
        "ef": 1.90,          # kg CO2e / m³
        "unit": "m3",
        "source": "MoEFCC"
    },
    "lpg": {
        "ef": 2.98,          # kg CO2e / litre (estimated, add official when available)
        "unit": "litres",
        "source": "MoEFCC (estimated)"
    },
}

# ──────────────────────────────────────────────────────────────
# SCOPE 2  —  Purchased Electricity Emission Factors
# Source: Central Electricity Authority (CEA), India
# Unit: kg CO2e per kWh
# ──────────────────────────────────────────────────────────────
GRID_EF_DEFAULT = 0.82      # Conservative national average (CEA 2022-23)
GRID_EF_MIN     = 0.70
GRID_EF_MAX     = 0.82

# State-wise grid emission factors (kg CO2e / kWh) — CEA 2022-23
# Add more states here as CEA updates data
STATE_GRID_EF = {
    "andhra_pradesh":  0.72,
    "assam":           0.72,
    "bihar":           0.88,
    "chhattisgarh":    0.92,
    "delhi":           0.78,
    "goa":             0.70,
    "gujarat":         0.88,
    "haryana":         0.86,
    "himachal_pradesh":0.30,   # High hydro share
    "jharkhand":       0.90,
    "karnataka":       0.60,   # High renewables share
    "kerala":          0.55,
    "madhya_pradesh":  0.86,
    "maharashtra":     0.82,
    "odisha":          0.89,
    "punjab":          0.74,
    "rajasthan":       0.90,
    "tamil_nadu":      0.75,
    "telangana":       0.80,
    "uttar_pradesh":   0.88,
    "uttarakhand":     0.40,
    "west_bengal":     0.85,
    "default":         0.82,   # Fallback if state not listed
}

# T&D loss factor — 8% used in formula (conservative); BRSR benchmark uses 18%
# We keep both and use them appropriately
TD_LOSS_FACTOR_FORMULA   = 0.08   # Used in Scope 3 T&D formula
TD_LOSS_FACTOR_BENCHMARK = 0.18   # Used in benchmark derivation (CEA grid loss)

# ──────────────────────────────────────────────────────────────
# SCOPE 3  —  Value Chain Emission Factors (Estimated / LCA)
# ──────────────────────────────────────────────────────────────
SCOPE3_FACTORS = {

    # Cloud / Data-centre electricity
    "cloud_ef": 0.40,            # kg CO2e / kWh (mid estimate)
    "cloud_ef_min": 0.35,
    "cloud_ef_max": 0.45,
    "cloud_source": "LCA studies / no official Indian govt EF available",

    # Cloud spend-based fallback (EEIO proxy)
    "cloud_spend_ef": 0.001,     # kg CO2e / INR spent on cloud

    # Device lifecycle embodied carbon (LCA)
    "laptop_lifecycle_ef": 300,  # kg CO2e per unit (mid of 250–350)
    "laptop_useful_life":  3.5,  # years (mid of 3–4)

    "desktop_lifecycle_ef": 400, # kg CO2e per unit (estimated)
    "desktop_useful_life":  4.0,

    "server_lifecycle_ef": 1000, # kg CO2e per unit (mid of 800–1200)
    "server_useful_life":  5.0,

    "monitor_lifecycle_ef": 150, # kg CO2e per unit (LCA estimate)
    "monitor_useful_life":  5.0,

    # Purchased services / SaaS (EEIO spend-based)
    "services_spend_ef": 0.001,  # kg CO2e / INR  (mid of 0.0005–0.002)
    "services_source": "EEIO models",
}

# ──────────────────────────────────────────────────────────────
# SERVER COOLING PUE MULTIPLIERS
# PUE = Power Usage Effectiveness (total facility power / IT power)
# Source: ASHRAE / Green Grid / Uptime Institute estimates for India
# ──────────────────────────────────────────────────────────────
SERVER_COOLING_PUE = {
    "hot_aisle_cold_aisle": 1.5,   # Standard efficient arrangement
    "stacked_high_density":  2.0,  # Dense stacking, less efficient
    "direct_liquid_cooling": 1.2,  # Most efficient
    "custom":                1.6,  # Generic fallback for custom setups
    "default":               1.6,  # If not specified
}

# ──────────────────────────────────────────────────────────────
# CLOUD PROVIDER AVERAGE EMISSION FACTORS  (kg CO2e / compute-hour)
# These are rough industry estimates; actual depends on region.
# Source: Provider sustainability reports & third-party studies
# ──────────────────────────────────────────────────────────────
CLOUD_PROVIDER_EF = {
    "aws":     0.0002,   # kg CO2e / compute hour (global avg, estimated)
    "azure":   0.0002,
    "gcp":     0.00015,  # GCP claims lower due to renewable PPAs
    "default": 0.0002,
}
