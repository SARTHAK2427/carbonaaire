"""
rules/scope3_rules.py
=====================
Rule definitions for Scope 3 (value chain) emissions.

HOW TO ADD A NEW RULE:
  1. Write a function: def rule_my_rule(result, data) -> list[Finding]
  2. Append it to SCOPE3_RULES at the bottom.
"""

from rules.rule_engine import Finding, Severity


# ── Thresholds ────────────────────────────────────────────────────────────────
CLOUD_HIGH_SPEND_INR        = 100_000   # ₹1 lakh/month cloud bill — flag
CLOUD_VERY_HIGH_SPEND_INR   = 500_000   # ₹5 lakh/month — critical
DEVICES_PER_EMPLOYEE_HIGH   = 2.5       # devices per employee — flag high
SERVER_PER_RACK_EXPECTED     = 10       # expected servers per rack minimum
SCOPE3_HIGH_SHARE_PCT        = 70.0     # % — if scope3 > 70% of total


def rule_cloud_spend_level(result: dict, data) -> list:
    """Assess cloud spend and associated emissions."""
    findings = []
    spend    = data.cloud_monthly_bill_inr
    tco2e    = result["scope3"]["cloud"]["tco2e"]
    method   = result["scope3"]["cloud"]["method"]

    if method == "none" or (spend == 0 and data.cloud_compute_hours_per_month == 0
                            and data.cloud_kwh_per_month == 0):
        return findings  # No cloud data — nothing to flag here

    if spend >= CLOUD_VERY_HIGH_SPEND_INR:
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 3",
            category="Cloud Services",
            message=(
                f"Cloud spend is very high (₹{spend:,.0f}/month → {tco2e:.3f} tCO2e/month). "
                "Cloud is a major emission lever for IT companies."
            ),
            recommendation=(
                "Request sustainability reports from your cloud provider. "
                "Use provider tools (AWS Carbon Footprint Tool, Azure Emissions Dashboard, "
                "GCP Carbon Sense) to identify the highest-emitting services. "
                "Migrate workloads to low-carbon cloud regions. "
                "Implement auto-scaling to avoid idle compute. "
                "Consider switching to providers with higher renewable commitments."
            ),
        ))
    elif spend >= CLOUD_HIGH_SPEND_INR:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 3",
            category="Cloud Services",
            message=(
                f"Cloud spend: ₹{spend:,.0f}/month ({tco2e:.3f} tCO2e/month)."
            ),
            recommendation=(
                "Audit underutilised cloud resources (idle VMs, unused storage). "
                "Right-size instances — oversized VMs waste both money and carbon. "
                "Use spot/preemptible instances for batch workloads."
            ),
        ))
    elif spend > 0:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Cloud Services",
            message=f"Cloud spend: ₹{spend:,.0f}/month ({tco2e:.4f} tCO2e/month). Moderate level.",
            recommendation="Use cloud provider sustainability dashboards to track trends.",
        ))

    return findings


def rule_cloud_data_quality(result: dict, data) -> list:
    """Encourage better cloud data (kWh vs spend-based)."""
    findings = []
    method = result["scope3"]["cloud"]["method"]

    if method == "spend_based_eeio":
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Scope 3",
            category="Cloud Data Quality",
            message=(
                "Cloud emissions are estimated using a spend-based EEIO proxy. "
                "This is an approximation with ±50% uncertainty."
            ),
            recommendation=(
                "Use your cloud provider's native carbon tool to get kWh-based estimates: "
                "AWS → Carbon Footprint Tool, Azure → Emissions Dashboard, "
                "GCP → Carbon Sense. Export and use kWh data for better accuracy."
            ),
        ))
    elif method == "compute_hour_based":
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Cloud Data Quality",
            message="Cloud emissions calculated using compute hours — medium-quality estimate.",
            recommendation="Upgrade to kWh-based data for highest accuracy.",
        ))

    return findings


def rule_server_arrangement_efficiency(result: dict, data) -> list:
    """Flag inefficient server cooling arrangements."""
    findings = []
    arrangement = data.server_arrangement.lower()

    if data.server_rack_count == 0 and data.num_servers_onprem == 0:
        return findings

    if arrangement == "stacked_high_density":
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 3",
            category="Server Cooling",
            message=(
                "Stacked high-density arrangement has a PUE of ~2.0 — "
                "meaning 50% of energy is wasted on cooling."
            ),
            recommendation=(
                "Transition to hot-aisle/cold-aisle containment (PUE ~1.5). "
                "This can reduce server energy use by ~25%. "
                "Long term: evaluate direct liquid cooling (PUE ~1.2)."
            ),
        ))
    elif arrangement in ("custom", "default", ""):
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Scope 3",
            category="Server Cooling",
            message="Server cooling arrangement is unspecified or custom. PUE assumed at 1.6.",
            recommendation=(
                "Document your server arrangement. Measure actual PUE. "
                "Implement hot-aisle/cold-aisle if not already done."
            ),
        ))
    elif arrangement == "direct_liquid_cooling":
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Server Cooling",
            message="Direct liquid cooling (PUE ~1.2) — highly efficient arrangement.",
            recommendation="Maintain this standard as you scale server capacity.",
        ))
    elif arrangement == "hot_aisle_cold_aisle":
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Server Cooling",
            message="Hot-aisle/cold-aisle containment (PUE ~1.5) — efficient arrangement.",
            recommendation="Consider liquid cooling for your highest-density racks.",
        ))

    return findings


def rule_device_refresh_cycle(result: dict, data) -> list:
    """Inform about device lifecycle and circular economy options."""
    findings = []
    total_devices = data.num_laptops + data.num_desktops + data.num_servers_onprem + data.num_monitors

    if total_devices == 0:
        return findings

    monthly_device_tco2e = result["scope3"]["devices"]["total_monthly_tco2e"]

    if monthly_device_tco2e > 0.5:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 3",
            category="Device Lifecycle",
            message=(
                f"Device embodied carbon is significant: {monthly_device_tco2e:.3f} tCO2e/month "
                f"({monthly_device_tco2e * 12:.2f} tCO2e/year) across {total_devices} devices."
            ),
            recommendation=(
                "Extend device useful life — each additional year of laptop use reduces "
                "embodied carbon by ~25%. "
                "Use refurbished/certified second-hand hardware where possible. "
                "Partner with OEM take-back programmes (Dell Renew, HP Planet Partners). "
                "Centralise computing with thin clients to reduce device count."
            ),
        ))
    elif total_devices > 0:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Device Lifecycle",
            message=f"Device lifecycle emissions: {monthly_device_tco2e:.4f} tCO2e/month ({total_devices} devices).",
            recommendation=(
                "Track asset refresh cycles. "
                "Delay hardware replacement where performance allows."
            ),
        ))

    return findings


def rule_scope3_dominance(result: dict, data) -> list:
    """Flag if Scope 3 dominates total emissions."""
    findings = []
    pct   = result["scope_percentages"]["scope3_pct"]
    tco2e = result["monthly"]["scope3_tco2e"]

    if pct >= SCOPE3_HIGH_SHARE_PCT:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 3",
            category="Scope Balance",
            message=(
                f"Scope 3 represents {pct:.1f}% of total emissions "
                f"({tco2e:.3f} tCO2e/month). "
                "This is expected for IT companies but warrants a value-chain strategy."
            ),
            recommendation=(
                "Develop a Scope 3 action plan. Focus first on the largest contributors: "
                "cloud services and purchased services. "
                "Engage key suppliers on their own emission reduction targets."
            ),
        ))

    return findings


def rule_purchased_services(result: dict, data) -> list:
    """Inform about purchased services emissions."""
    findings = []
    spend  = data.purchased_services_spend_inr_per_month
    tco2e  = result["scope3"]["services"]["tco2e"]

    if spend > 0:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 3",
            category="Purchased Services",
            message=(
                f"Purchased services spend: ₹{spend:,.0f}/month → "
                f"{tco2e:.4f} tCO2e/month (EEIO estimate)."
            ),
            recommendation=(
                "Request sustainability/ESG disclosures from your top 5 service providers. "
                "Prefer suppliers with SBTi (Science Based Targets) commitments."
            ),
        ))

    return findings


# ── Register all Scope 3 rules ────────────────────────────────────────────────
SCOPE3_RULES = [
    rule_cloud_spend_level,
    rule_cloud_data_quality,
    rule_server_arrangement_efficiency,
    rule_device_refresh_cycle,
    rule_scope3_dominance,
    rule_purchased_services,
]
