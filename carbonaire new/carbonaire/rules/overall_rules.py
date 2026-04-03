"""
rules/overall_rules.py
======================
Cross-scope and overall performance rules for Carbonaire.
These rules look at the big picture — total footprint, benchmark comparison,
and strategic-level insights.

HOW TO ADD A NEW RULE:
  1. Write a function: def rule_my_rule(result, data) -> list[Finding]
  2. Append it to OVERALL_RULES at the bottom.
"""

from rules.rule_engine import Finding, Severity
from benchmarks.industry_benchmark import (
    get_performance_band,
    BENCHMARK_MEDIAN_TCO2E_PER_CR,
    IDEAL_BENCHMARK,
    PERFORMANCE_BANDS,
)


def rule_benchmark_comparison(result: dict, data) -> list:
    """Compare company's revenue intensity against Indian IT SME benchmark."""
    findings = []
    intensity = result["intensity"]["revenue_intensity_tco2e_per_cr"]

    if intensity is None:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Overall",
            category="Benchmark",
            message="Revenue not provided — cannot calculate intensity vs industry benchmark.",
            recommendation="Enter annual revenue to enable benchmark comparison.",
        ))
        return findings

    band = get_performance_band(intensity)
    median = BENCHMARK_MEDIAN_TCO2E_PER_CR

    if band == "Green":
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Overall",
            category="Benchmark",
            message=(
                f"Revenue intensity: {intensity:.2f} tCO2e/₹Cr — "
                f"GREEN (industry median: {median} tCO2e/₹Cr). "
                "You are performing well ahead of Indian IT SME peers."
            ),
            recommendation=(
                "Maintain this standard. Consider publishing a sustainability report "
                "(BRSR/GRI) to leverage your strong performance for client and investor trust."
            ),
        ))
    elif band == "Efficient":
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Overall",
            category="Benchmark",
            message=(
                f"Revenue intensity: {intensity:.2f} tCO2e/₹Cr — "
                f"EFFICIENT (industry median: {median}). Slightly better than median."
            ),
            recommendation=(
                "Focus on the top 1–2 findings in this report to move into 'Green' band. "
                "Increasing renewable energy % is usually the fastest lever."
            ),
        ))
    elif band == "Average":
        findings.append(Finding(
            severity=Severity.MEDIUM,
            scope="Overall",
            category="Benchmark",
            message=(
                f"Revenue intensity: {intensity:.2f} tCO2e/₹Cr — "
                f"AT INDUSTRY AVERAGE (median: {median}). Meets but does not exceed the norm."
            ),
            recommendation=(
                "Address the HIGH and CRITICAL findings in this report. "
                "Set a target to reach 'Efficient' band (< 3.0 tCO2e/₹Cr) within 18 months."
            ),
        ))
    else:  # Carbon heavy
        findings.append(Finding(
            severity=Severity.HIGH,
            scope="Overall",
            category="Benchmark",
            message=(
                f"Revenue intensity: {intensity:.2f} tCO2e/₹Cr — "
                f"ABOVE INDUSTRY AVERAGE (median: {median}). "
                "Carbon performance is below sector norms."
            ),
            recommendation=(
                "Create an immediate carbon reduction roadmap. "
                "Prioritise: (1) Renewable energy for Scope 2, "
                "(2) Generator reduction for Scope 1, "
                "(3) Cloud optimisation for Scope 3. "
                "Set a science-based target aligned with India's NDC commitments."
            ),
        ))

    return findings


def rule_ideal_benchmark_gap(result: dict, data) -> list:
    """Show gap to ideal performance."""
    findings = []
    intensity = result["intensity"]["revenue_intensity_tco2e_per_cr"]
    annual    = result["annual"]["total_tco2e"]

    if intensity is None or annual == 0:
        return findings

    ideal = IDEAL_BENCHMARK["tco2e_per_cr"]
    gap   = intensity - ideal

    if gap > 0:
        # Calculate how many tCO2e/year need to be reduced
        if data.annual_revenue_inr_cr > 0:
            target_annual = ideal * data.annual_revenue_inr_cr
            reduction_needed = annual - target_annual
        else:
            reduction_needed = None

        msg = (
            f"Gap to ideal performance ({ideal} tCO2e/₹Cr): "
            f"{gap:.2f} tCO2e/₹Cr above ideal."
        )
        if reduction_needed is not None:
            msg += f" Requires a reduction of ~{reduction_needed:.1f} tCO2e/year."

        findings.append(Finding(
            severity=Severity.INFO,
            scope="Overall",
            category="Ideal Benchmark Gap",
            message=msg,
            recommendation=(
                f"Ideal benchmark is {ideal} tCO2e/₹Cr (top-performing Indian IT SMEs, BRSR data). "
                "Prioritise the highest-severity recommendations in this report."
            ),
        ))

    return findings


def rule_total_footprint_context(result: dict, data) -> list:
    """Give context to the raw total footprint number."""
    findings = []
    annual = result["annual"]["total_tco2e"]

    if annual < 10:
        label = "very small"
        note  = "Focus on accurate measurement and establishing a baseline."
    elif annual < 50:
        label = "small"
        note  = "Reduction of even 10 tCO2e/year is meaningful at this scale."
    elif annual < 200:
        label = "medium"
        note  = "Scope 2 renewable energy is likely your fastest emission-reduction lever."
    elif annual < 1000:
        label = "significant"
        note  = "Consider a formal SBTi target and annual GHG inventory."
    else:
        label = "large"
        note  = (
            "Your footprint warrants a dedicated sustainability team or officer. "
            "Consider third-party GHG verification."
        )

    findings.append(Finding(
        severity=Severity.INFO,
        scope="Overall",
        category="Footprint Context",
        message=(
            f"Total annual footprint: {annual:.2f} tCO2e/year — {label} for an IT SME."
        ),
        recommendation=note,
    ))

    return findings


def rule_data_quality_reminder(result: dict, data) -> list:
    """Remind users where estimates are being used vs actual data."""
    findings = []
    warnings = result["validation"]["warnings"]
    info     = result["validation"]["info"]

    if warnings:
        findings.append(Finding(
            severity=Severity.LOW,
            scope="Overall",
            category="Data Quality",
            message=(
                f"{len(warnings)} data quality warning(s) detected during input validation."
            ),
            recommendation=(
                "Review warnings: " + " | ".join(warnings) + ". "
                "Upload actual bills/records to improve accuracy."
            ),
        ))

    if info:
        findings.append(Finding(
            severity=Severity.INFO,
            scope="Overall",
            category="Data Quality",
            message=f"{len(info)} informational note(s) about input data.",
            recommendation=" | ".join(info),
        ))

    return findings


# ── Register all Overall rules ────────────────────────────────────────────────
OVERALL_RULES = [
    rule_benchmark_comparison,
    rule_ideal_benchmark_gap,
    rule_total_footprint_context,
    rule_data_quality_reminder,
]
