"""
ml/dataset_generator.py
========================
Synthetic dataset generator for Carbonaire ML recommendation system.
Generates 500 diverse company profiles and labels them using rule-based logic.
"""

import random
import json
import csv
import os
from dataclasses import dataclass, asdict, fields
from typing import List, Dict, Any

random.seed(42)

# ─────────────────────────────────────────────────────────────
# RECOMMENDATION LABELS (maps to rule engine severity/category)
# ─────────────────────────────────────────────────────────────

RECOMMENDATIONS = [
    "switch_to_renewables",          # 0 — Low renewable %, high electricity
    "reduce_electricity_consumption", # 1 — Very high kWh, no action taken
    "optimize_server_infrastructure", # 2 — High server count, poor PUE
    "electrify_fleet_reduce_fuel",    # 3 — High scope1 fuel usage
    "adopt_cloud_migration",          # 4 — Many on-prem servers, no cloud
    "reduce_cloud_carbon",            # 5 — High cloud bill, dirty provider
    "improve_cooling_efficiency",     # 6 — High server area, bad arrangement
    "low_emission_maintain_practices",# 7 — Already green, keep going
    "reduce_scope3_purchases",        # 8 — High purchased services spend
    "hybrid_work_policy",             # 9 — High employees, high electricity
]

# Priority levels
PRIORITY = {
    "switch_to_renewables": "HIGH",
    "reduce_electricity_consumption": "HIGH",
    "optimize_server_infrastructure": "MEDIUM",
    "electrify_fleet_reduce_fuel": "HIGH",
    "adopt_cloud_migration": "MEDIUM",
    "reduce_cloud_carbon": "MEDIUM",
    "improve_cooling_efficiency": "LOW",
    "low_emission_maintain_practices": "LOW",
    "reduce_scope3_purchases": "LOW",
    "hybrid_work_policy": "MEDIUM",
}


# ─────────────────────────────────────────────────────────────
# INPUT FEATURE SCHEMA
# ─────────────────────────────────────────────────────────────

@dataclass
class CompanyProfile:
    # Categorical
    industry_type: str           # IT, manufacturing, retail, finance, healthcare
    company_size: str            # small, medium, large
    electricity_level: str       # low, medium, high, very_high
    server_arrangement: str      # hot_aisle_cold_aisle, stacked_high_density, direct_liquid_cooling

    # Numeric (normalised 0–1 or raw)
    num_employees: int
    electricity_kwh_per_month: float
    renewable_energy_percent: float
    diesel_litres_per_month: float
    petrol_litres_per_month: float
    natural_gas_m3_per_month: float
    server_rack_count: int
    num_servers_onprem: int
    num_laptops: int
    num_desktops: int
    cloud_monthly_bill_inr: float
    cloud_provider: str          # aws, azure, gcp, none
    purchased_services_spend_inr_per_month: float
    server_area_sqft: float
    annual_revenue_inr_cr: float

    # Calculated emissions (from rule engine proxy)
    scope1_tco2e_monthly: float
    scope2_tco2e_monthly: float
    scope3_tco2e_monthly: float
    total_tco2e_monthly: float
    scope1_pct: float
    scope2_pct: float
    scope3_pct: float

    # Label
    primary_recommendation: str
    recommendation_priority: str
    recommendation_label: int    # integer class for classifier


# ─────────────────────────────────────────────────────────────
# EMISSION FACTOR PROXIES (simplified, same logic as master_calculator)
# ─────────────────────────────────────────────────────────────

GRID_FACTOR = 0.82          # tCO2e per MWh (India average)
DIESEL_FACTOR = 2.68        # kg CO2 per litre
PETROL_FACTOR = 2.31
NATURAL_GAS_FACTOR = 2.04   # per m3
LPG_FACTOR = 1.51
CLOUD_FACTOR_PER_INR = 0.000015   # rough: tCO2e per ₹ cloud spend
SERVICES_FACTOR_PER_INR = 0.000008

CLOUD_DIRTY = {"aws": 1.0, "azure": 0.9, "gcp": 0.6, "none": 0.0}

ARRANGEMENT_PUE = {
    "hot_aisle_cold_aisle": 1.5,
    "stacked_high_density": 2.2,
    "direct_liquid_cooling": 1.2,
    "custom": 1.7,
}

LAPTOP_W  = 45
DESKTOP_W = 150
MONITOR_W = 30
HOURS_PER_MONTH = 22 * 8


def calc_emissions(p: dict) -> tuple:
    """Calculate scope 1/2/3 monthly tCO2e from a profile dict."""
    # Scope 1
    scope1 = (
        p["diesel_litres_per_month"]  * DIESEL_FACTOR / 1000 +
        p["petrol_litres_per_month"]  * PETROL_FACTOR / 1000 +
        p["natural_gas_m3_per_month"] * NATURAL_GAS_FACTOR / 1000
    )

    # Scope 2 — electricity (accounting for renewables)
    net_kwh = p["electricity_kwh_per_month"] * (1 - p["renewable_energy_percent"] / 100)
    scope2  = net_kwh * GRID_FACTOR / 1000

    # Servers add to scope 2
    pue = ARRANGEMENT_PUE.get(p["server_arrangement"], 1.7)
    server_kwh = p["server_rack_count"] * 2 * pue * 24 * 30 / 1000  # 2kW per rack est
    scope2 += server_kwh * GRID_FACTOR / 1000

    # Scope 3
    cloud_multiplier = CLOUD_DIRTY.get(p["cloud_provider"], 0.8)
    scope3 = (
        p["cloud_monthly_bill_inr"] * CLOUD_FACTOR_PER_INR * cloud_multiplier +
        p["purchased_services_spend_inr_per_month"] * SERVICES_FACTOR_PER_INR +
        (p["num_laptops"] * LAPTOP_W + p["num_desktops"] * DESKTOP_W) * HOURS_PER_MONTH / 1e6
    )

    total = scope1 + scope2 + scope3
    if total == 0:
        return scope1, scope2, scope3, 0.001, 33.3, 33.3, 33.3

    return (
        round(scope1, 4), round(scope2, 4), round(scope3, 4),
        round(total, 4),
        round(scope1 / total * 100, 1),
        round(scope2 / total * 100, 1),
        round(scope3 / total * 100, 1),
    )


# ─────────────────────────────────────────────────────────────
# RULE-BASED LABELLER (mirrors rule_engine logic)
# ─────────────────────────────────────────────────────────────

def label_recommendation(p: dict, s1_pct, s2_pct, s3_pct) -> str:
    """Deterministic rule-based labeller — same logic as RuleEngine."""

    renewable = p["renewable_energy_percent"]
    kwh       = p["electricity_kwh_per_month"]
    servers   = p["server_rack_count"] + p["num_servers_onprem"]
    fuel      = p["diesel_litres_per_month"] + p["petrol_litres_per_month"]
    cloud_bill= p["cloud_monthly_bill_inr"]
    arrange   = p["server_arrangement"]
    employees = p["num_employees"]
    services  = p["purchased_services_spend_inr_per_month"]

    # Priority waterfall — first matching rule wins
    if s1_pct > 40 and fuel > 200:
        return "electrify_fleet_reduce_fuel"

    if renewable < 10 and kwh > 8000:
        return "switch_to_renewables"

    if kwh > 15000:
        return "reduce_electricity_consumption"

    if servers > 20 and arrange == "stacked_high_density":
        return "optimize_server_infrastructure"

    if servers > 30 and cloud_bill < 5000:
        return "adopt_cloud_migration"

    if cloud_bill > 100000 and p["cloud_provider"] in ("aws", "azure"):
        return "reduce_cloud_carbon"

    if arrange == "stacked_high_density" and servers > 5:
        return "improve_cooling_efficiency"

    if s3_pct > 50 and services > 50000:
        return "reduce_scope3_purchases"

    if renewable < 20 and kwh > 5000:
        return "switch_to_renewables"

    if employees > 200 and kwh > 10000:
        return "hybrid_work_policy"

    return "low_emission_maintain_practices"


# ─────────────────────────────────────────────────────────────
# PROFILE GENERATOR
# ─────────────────────────────────────────────────────────────

INDUSTRIES  = ["IT", "Manufacturing", "Retail", "Finance", "Healthcare", "Logistics", "Education"]
CLOUD_PROVIDERS = ["aws", "azure", "gcp", "none"]
ARRANGEMENTS = ["hot_aisle_cold_aisle", "stacked_high_density", "direct_liquid_cooling", "custom"]
SIZES = ["small", "medium", "large"]


def _electricity_level(kwh):
    if kwh < 3000:   return "low"
    if kwh < 8000:   return "medium"
    if kwh < 15000:  return "high"
    return "very_high"


def generate_profile(seed_override=None) -> dict:
    """Generate a single random company profile."""
    size = random.choice(SIZES)

    emp_range = {"small": (5, 50), "medium": (51, 300), "large": (301, 2000)}[size]
    employees = random.randint(*emp_range)

    kwh_base = employees * random.uniform(30, 120)
    kwh = round(kwh_base + random.gauss(0, kwh_base * 0.2), 1)
    kwh = max(500, kwh)

    renewable = round(random.choice([
        random.uniform(0, 5),
        random.uniform(5, 30),
        random.uniform(30, 80),
        random.uniform(80, 100),
    ]), 1)

    industry = random.choice(INDUSTRIES)

    # Fuel — manufacturing/logistics have more
    fuel_mult = 3.0 if industry in ("Manufacturing", "Logistics") else 0.5
    diesel  = round(max(0, random.gauss(50 * fuel_mult, 30)), 1)
    petrol  = round(max(0, random.gauss(20 * fuel_mult, 15)), 1)
    nat_gas = round(max(0, random.gauss(10 * fuel_mult, 8)), 1)

    # Servers
    has_servers = random.random() > 0.3
    rack_count  = random.randint(0, 40) if has_servers else 0
    onprem_srv  = random.randint(0, 20) if has_servers else 0
    arrangement = random.choice(ARRANGEMENTS)
    server_area = rack_count * random.uniform(15, 40)

    # Devices
    laptops  = int(employees * random.uniform(0.5, 1.0))
    desktops = int(employees * random.uniform(0.0, 0.6))

    # Cloud
    cloud_prov  = random.choice(CLOUD_PROVIDERS)
    cloud_bill  = round(max(0, random.gauss(30000, 25000)), 0) if cloud_prov != "none" else 0

    # Services
    services_spend = round(max(0, random.gauss(employees * 800, employees * 400)), 0)

    revenue = round(employees * random.uniform(0.05, 0.8), 2)

    return {
        "industry_type": industry,
        "company_size": size,
        "num_employees": employees,
        "electricity_kwh_per_month": round(kwh, 1),
        "renewable_energy_percent": renewable,
        "diesel_litres_per_month": diesel,
        "petrol_litres_per_month": petrol,
        "natural_gas_m3_per_month": nat_gas,
        "server_rack_count": rack_count,
        "num_servers_onprem": onprem_srv,
        "num_laptops": laptops,
        "num_desktops": desktops,
        "server_arrangement": arrangement,
        "server_area_sqft": round(server_area, 1),
        "cloud_provider": cloud_prov,
        "cloud_monthly_bill_inr": cloud_bill,
        "purchased_services_spend_inr_per_month": services_spend,
        "annual_revenue_inr_cr": revenue,
    }


def generate_dataset(n: int = 500) -> List[dict]:
    """Generate n diverse company profiles with labels."""
    dataset = []

    for i in range(n):
        p = generate_profile()
        s1, s2, s3, total, s1p, s2p, s3p = calc_emissions(p)

        rec   = label_recommendation(p, s1p, s2p, s3p)
        label = RECOMMENDATIONS.index(rec)

        row = {
            **p,
            "electricity_level": _electricity_level(p["electricity_kwh_per_month"]),
            "scope1_tco2e_monthly": s1,
            "scope2_tco2e_monthly": s2,
            "scope3_tco2e_monthly": s3,
            "total_tco2e_monthly":  total,
            "scope1_pct": s1p,
            "scope2_pct": s2p,
            "scope3_pct": s3p,
            "primary_recommendation": rec,
            "recommendation_priority": PRIORITY[rec],
            "recommendation_label": label,
        }
        dataset.append(row)

    return dataset


def save_dataset(dataset: List[dict], out_dir: str = "."):
    """Save dataset as CSV and JSON."""
    os.makedirs(out_dir, exist_ok=True)

    csv_path  = os.path.join(out_dir, "carbonaire_training_data.csv")
    json_path = os.path.join(out_dir, "carbonaire_training_data.json")

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
        writer.writeheader()
        writer.writerows(dataset)

    with open(json_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"✅ Dataset saved: {csv_path} ({len(dataset)} rows)")
    print(f"✅ Dataset saved: {json_path}")
    return csv_path, json_path


if __name__ == "__main__":
    ds = generate_dataset(500)
    save_dataset(ds, out_dir=".")

    # Print class distribution
    from collections import Counter
    dist = Counter(r["primary_recommendation"] for r in ds)
    print("\nClass distribution:")
    for k, v in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"  {k:40} {v:4d} ({v/5:.1f}%)")
