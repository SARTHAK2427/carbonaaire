"""
rules/scope1_rules.py
=====================
Rule definitions for Scope 1 (direct combustion) emissions.

Each rule is a function that receives the full calculation result dict
and returns a list of Finding objects (defined in rule_engine.py).

HOW TO ADD A NEW RULE:
  1. Write a function: def rule_my_new_rule(result, data) -> list[Finding]
  2. Append it to SCOPE1_RULES at the bottom of this file.
  The rule engine will automatically pick it up.
"""

from rules.rule_engine import Finding, Severity


# ── Thresholds (edit here to update without touching rule logic) ────────────
DIESEL_HIGH_MONTHLY_LITRES   = 500     # litres/month — flag for high generator use
DIESEL_CRITICAL_MONTHLY_LITRES = 1000  # litres/month — critical
PETROL_HIGH_MONTHLY_LITRES   = 300
SCOPE1_HIGH_SHARE_PCT        = 30.0    # % of total — if Scope 1 is >30% → flag
SCOPE1_CRITICAL_SHARE_PCT    = 50.0


def rule_diesel_usage_level(result: dict, data) -> list:
    """Flag excessive diesel generator consumption."""
    findings = []
    litres = data.diesel_litres_per_month
    tco2e  = result["scope1"]["diesel_tco2e"]

    if litres >= DIESEL_CRITICAL_MONTHLY_LITRES:
        findings.append(Finding(
            severity=Severity.CRITICAL,
            scope="Scope 1",
            category="Diesel Generator",
            message=(
                f"Diesel consumption is very high ({litres:.0f} L/month = {tco2e:.3f} tCO2e/month). "
                "This is a significant direct emission source."
            ),
            recommendation=(
                "Consider switching to grid power or installing solar+battery backup. "
                "Audit generator runtime — idle running is a common source of waste. "
                "If diesel is unavoidable, explore HVO (Hydrotreated Vegetable Oil) as a drop-in substitute."
            ),
        ))
    elif litres >= DIESEL_HIGH_MONTHLY_LITRES:
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 1",
            category="Diesel Generator",
            message=(
                f"Diesel consumption is elevated ({litres:.0f} L/month = {tco2e:.3f} tCO2e/month)."
            ),
            recommendation=(
                "Track generator runtime hours. Reduce by improving grid reliability, "
                "adding UPS/battery systems, or reducing non-essential loads during outages."
            ),
        ))
    elif litres > 0:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 1",
            category="Diesel Generator",
            message=f"Diesel usage is within moderate range ({litres:.0f} L/month).",
            recommendation="Continue monitoring. Log runtime hours for audit trail.",
        ))

    return findings


def rule_petrol_usage_level(result: dict, data) -> list:
    """Flag high petrol (vehicle fleet) consumption."""
    findings = []
    litres = data.petrol_litres_per_month
    tco2e  = result["scope1"]["petrol_tco2e"]

    if litres >= PETROL_HIGH_MONTHLY_LITRES:
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 1",
            category="Petrol Vehicles",
            message=(
                f"Petrol vehicle consumption is high ({litres:.0f} L/month = {tco2e:.3f} tCO2e/month)."
            ),
            recommendation=(
                "Develop an EV transition roadmap for the fleet. "
                "Introduce a travel policy to encourage public transport, carpooling, or WFH. "
                "Install EV charging on-premise to incentivise the switch."
            ),
        ))
    elif litres > 0:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 1",
            category="Petrol Vehicles",
            message=f"Petrol vehicle fuel use: {litres:.0f} L/month.",
            recommendation="Track per-vehicle fuel efficiency. Consider EV conversion for high-mileage vehicles.",
        ))

    return findings


def rule_scope1_share_of_total(result: dict, data) -> list:
    """Warn if Scope 1 forms a disproportionately large share of total emissions."""
    findings = []
    pct   = result["scope_percentages"]["scope1_pct"]
    tco2e = result["monthly"]["scope1_tco2e"]

    if pct >= SCOPE1_CRITICAL_SHARE_PCT:
        findings.append(Finding(
            severity=Severity.CRITICAL,
            scope="Scope 1",
            category="Scope Balance",
            message=(
                f"Scope 1 represents {pct:.1f}% of total emissions ({tco2e:.3f} tCO2e/month). "
                "For IT/ITES companies, Scope 1 should ideally be <10%."
            ),
            recommendation=(
                "Conduct an immediate audit of all on-site combustion sources. "
                "Prioritise electrification of any fuel-based equipment. "
                "Set a target to reduce Scope 1 below 15% within 12 months."
            ),
        ))
    elif pct >= SCOPE1_HIGH_SHARE_PCT:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 1",
            category="Scope Balance",
            message=(
                f"Scope 1 is {pct:.1f}% of total emissions. "
                "Typical IT SMEs have Scope 1 at 5–15%."
            ),
            recommendation=(
                "Review on-site fuel use. Reducing generator dependency and "
                "petrol fleet use will bring Scope 1 to an industry-typical level."
            ),
        ))

    return findings


def rule_natural_gas_usage(result: dict, data) -> list:
    """Inform about natural gas usage and switching options."""
    findings = []
    m3 = data.natural_gas_m3_per_month

    if m3 > 0:
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Scope 1",
            category="Natural Gas",
            message=f"Natural gas usage: {m3:.1f} m³/month.",
            recommendation=(
                "Natural gas is the cleanest fossil fuel for Scope 1 but still emits CO2e. "
                "Explore electric alternatives for any gas-heated processes. "
                "If gas is needed, investigate biogas/CNG blending options."
            ),
        ))

    return findings


# ── Register all Scope 1 rules here ──────────────────────────────────────────
# To add a new rule: append it to this list — no other change needed.
SCOPE1_RULES = [
    rule_diesel_usage_level,
    rule_petrol_usage_level,
    rule_scope1_share_of_total,
    rule_natural_gas_usage,
]
