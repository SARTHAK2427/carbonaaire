"""
rules/scope2_rules.py
=====================
Rule definitions for Scope 2 (purchased electricity) emissions.

HOW TO ADD A NEW RULE:
  1. Write a function: def rule_my_rule(result, data) -> list[Finding]
  2. Append it to SCOPE2_RULES at the bottom.
"""

from rules.rule_engine import Finding, Severity


# ── Thresholds ────────────────────────────────────────────────────────────────
SCOPE2_HIGH_SHARE_PCT        = 60.0   # % of total — Scope 2 dominant (normal for IT)
RENEWABLE_LOW_PCT            = 10.0   # % renewable — alert if very low
RENEWABLE_GOOD_PCT           = 30.0   # % renewable — good
RENEWABLE_EXCELLENT_PCT      = 60.0   # % renewable — excellent
ELECTRICITY_PER_EMPLOYEE_KWH = 150.0  # kWh/employee/month — high if exceeded
ELECTRICITY_HIGH_MONTHLY_KWH = 50000  # kWh/month — flag high consumers


def rule_renewable_energy_adoption(result: dict, data) -> list:
    """Assess renewable energy usage and recommend increase."""
    findings = []
    pct = data.renewable_energy_percent

    if pct == 0:
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 2",
            category="Renewable Energy",
            message="No renewable energy is being used. 100% grid electricity is carbon-intensive.",
            recommendation=(
                "Install rooftop solar (typical payback: 4–6 years in India). "
                "Alternatively, purchase Renewable Energy Certificates (RECs) from I-REC or REMC. "
                "Sign a Power Purchase Agreement (PPA) with a renewable energy provider. "
                "Target: at least 30% renewable mix within 2 years."
            ),
        ))
    elif pct < RENEWABLE_LOW_PCT:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 2",
            category="Renewable Energy",
            message=f"Only {pct:.1f}% renewable energy. Significant room for improvement.",
            recommendation=(
                "Expand solar capacity or procure additional RECs. "
                "Consider green tariff options offered by state DISCOMs."
            ),
        ))
    elif pct < RENEWABLE_GOOD_PCT:
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Scope 2",
            category="Renewable Energy",
            message=f"Renewable energy at {pct:.1f}%. On the right path.",
            recommendation="Set a target to reach 50%+ renewable within 3 years.",
        ))
    elif pct < RENEWABLE_EXCELLENT_PCT:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 2",
            category="Renewable Energy",
            message=f"Good renewable adoption at {pct:.1f}%.",
            recommendation="Aim for 80%+ renewable to qualify for green certification.",
        ))
    else:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 2",
            category="Renewable Energy",
            message=f"Excellent renewable energy usage: {pct:.1f}%. Well above industry norm.",
            recommendation="Maintain this level and explore 100% renewable through additional PPAs.",
        ))

    return findings


def rule_electricity_per_employee(result: dict, data) -> list:
    """Flag high per-employee electricity consumption."""
    findings = []
    if data.num_employees <= 0:
        return findings

    kwh_per_employee = data.electricity_kwh_per_month / data.num_employees

    if kwh_per_employee > ELECTRICITY_PER_EMPLOYEE_KWH * 1.5:
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Scope 2",
            category="Electricity Efficiency",
            message=(
                f"Electricity use per employee is very high: "
                f"{kwh_per_employee:.1f} kWh/employee/month "
                f"(industry typical: <{ELECTRICITY_PER_EMPLOYEE_KWH:.0f})."
            ),
            recommendation=(
                "Conduct an energy audit of the facility. "
                "Replace old ACs with 5-star BEE-rated inverter units. "
                "Switch to LED lighting throughout. "
                "Implement auto-shutdown policies for workstations after hours. "
                "Check server cooling efficiency — PUE above 2.0 is a major waste source."
            ),
        ))
    elif kwh_per_employee > ELECTRICITY_PER_EMPLOYEE_KWH:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 2",
            category="Electricity Efficiency",
            message=(
                f"Electricity per employee: {kwh_per_employee:.1f} kWh/month. "
                f"Slightly above benchmark of {ELECTRICITY_PER_EMPLOYEE_KWH:.0f}."
            ),
            recommendation=(
                "Check cooling system efficiency. "
                "Implement occupancy-based lighting and AC controls."
            ),
        ))
    else:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Scope 2",
            category="Electricity Efficiency",
            message=(
                f"Electricity per employee: {kwh_per_employee:.1f} kWh/month. "
                "Within normal range."
            ),
            recommendation="Continue monitoring monthly to detect trends early.",
        ))

    return findings


def rule_high_absolute_electricity(result: dict, data) -> list:
    """Flag very high absolute electricity consumption."""
    findings = []
    kwh = data.electricity_kwh_per_month

    if kwh >= ELECTRICITY_HIGH_MONTHLY_KWH:
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Scope 2",
            category="Electricity Volume",
            message=(
                f"Total electricity consumption is high: {kwh:,.0f} kWh/month. "
                "Qualifies for large consumer energy management measures."
            ),
            recommendation=(
                "As a large electricity consumer, you may be eligible for "
                "open-access renewable power procurement under state DISCOM regulations. "
                "This can significantly reduce both cost and emissions."
            ),
        ))

    return findings


def rule_scope2_grid_ef_note(result: dict, data) -> list:
    """Inform users about their state grid EF."""
    findings = []
    grid_ef = result["scope2"]["grid_ef_used"]
    state   = data.location_state

    findings.append(Finding(
        severity=Severity.INFO,
        scope="Scope 2",
        category="Grid Emission Factor",
        message=(
            f"Grid EF for {state.replace('_',' ').title()}: {grid_ef} kg CO2e/kWh (CEA 2022-23). "
            "States with high renewables (Karnataka, Kerala) have lower grid EFs."
        ),
        recommendation=(
            "If your state has a high grid EF, on-site solar or REC procurement "
            "has a proportionally higher impact on your footprint."
        ),
    ))

    return findings


# ── Register all Scope 2 rules ────────────────────────────────────────────────
SCOPE2_RULES = [
    rule_renewable_energy_adoption,
    rule_electricity_per_employee,
    rule_high_absolute_electricity,
    rule_scope2_grid_ef_note,
]
