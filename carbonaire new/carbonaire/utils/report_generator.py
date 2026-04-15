"""
utils/report_generator.py
==========================
Generates formatted terminal reports and structured JSON output
from calculation results and rule engine findings.

Output formats:
  - print_report()       → rich terminal output (for CLI testing)
  - to_json()            → clean dict ready for API / frontend
  - to_summary_text()    → short plain-text summary
"""

import json
from datetime import datetime
from typing import List

from rules.rule_engine import Finding, Severity, summarise_findings
from benchmarks.industry_benchmark import get_benchmark_summary


try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        RED = YELLOW = GREEN = CYAN = WHITE = MAGENTA = BLUE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ── Colour helpers ────────────────────────────────────────────────────────────

def _sev_color(severity: Severity) -> str:
    if not HAS_COLOR:
        return ""
    return {
        Severity.CRITICAL: Fore.RED + Style.BRIGHT,
        Severity.HIGH:     Fore.RED,
        Severity.MEDIUM:   Fore.YELLOW,
        Severity.LOW:      Fore.CYAN,
        Severity.INFO:     Fore.WHITE,
    }.get(severity, "")


def _reset():
    return Style.RESET_ALL if HAS_COLOR else ""


# ── Terminal report ───────────────────────────────────────────────────────────

def print_report(result: dict, findings: List[Finding], data=None):
    """Print a full formatted report to stdout."""
    sep  = "═" * 70
    sep2 = "─" * 70

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{sep}")
    print("  🌿  CARBONAIRE — CARBON FOOTPRINT REPORT")
    print(f"  {datetime.now().strftime('%d %b %Y, %H:%M')}")
    if data:
        print(f"  Company : {data.company_name}")
        print(f"  Industry: {data.industry_type}  |  State: {data.location_state.replace('_',' ').title()}")
    print(f"{sep}{_reset()}")

    # ── Emission Summary ────────────────────────────────────────────
    print(f"\n{Style.BRIGHT}EMISSION SUMMARY (Monthly / Annual){_reset()}")
    print(sep2)

    monthly = result["monthly"]
    annual  = result["annual"]
    pct     = result["scope_percentages"]

    rows = [
        ["Scope 1 — Direct Fuel",    f"{monthly['scope1_tco2e']:.3f}",  f"{annual['scope1_tco2e']:.2f}",  f"{pct['scope1_pct']:.1f}%"],
        ["Scope 2 — Electricity",    f"{monthly['scope2_tco2e']:.3f}",  f"{annual['scope2_tco2e']:.2f}",  f"{pct['scope2_pct']:.1f}%"],
        ["Scope 3 — Value Chain",    f"{monthly['scope3_tco2e']:.3f}",  f"{annual['scope3_tco2e']:.2f}",  f"{pct['scope3_pct']:.1f}%"],
        ["─────────────────────────", "─────────", "─────────", "──────"],
        ["TOTAL",                    f"{monthly['total_tco2e']:.3f}",   f"{annual['total_tco2e']:.2f}",   "100%"],
    ]
    headers = ["", "tCO2e/month", "tCO2e/year", "Share"]

    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
        print(f"{'':30} {'Monthly':>12} {'Annual':>12} {'Share':>8}")
        for r in rows:
            print(f"{r[0]:30} {r[1]:>12} {r[2]:>12} {r[3]:>8}")

    # ── Scope 3 Breakdown ────────────────────────────────────────────
    s3 = result["scope3"]
    print(f"\n{Style.BRIGHT}SCOPE 3 BREAKDOWN{_reset()}")
    print(sep2)
    s3_rows = [
        ["Cloud Services",       f"{s3['cloud']['tco2e']:.4f}",              f"{s3['cloud']['method']}"],
        ["Device Lifecycle",     f"{s3['devices']['total_monthly_tco2e']:.4f}", "LCA annualised"],
        ["T&D Losses",           f"{s3['td_losses']['tco2e']:.4f}",           f"Scope2 × {s3['td_losses']['loss_factor']*100:.0f}%"],
        ["Purchased Services",   f"{s3['services']['tco2e']:.4f}",            "EEIO spend-based"],
    ]
    if HAS_TABULATE:
        print(tabulate(s3_rows, headers=["Category", "tCO2e/month", "Method"], tablefmt="simple"))
    else:
        for r in s3_rows:
            print(f"  {r[0]:25} {r[1]:>12}  ({r[2]})")

    # ── Intensity Metrics ────────────────────────────────────────────
    intensity = result["intensity"]
    print(f"\n{Style.BRIGHT}INTENSITY METRICS{_reset()}")
    print(sep2)
    if intensity["per_employee_tco2e_per_year"] is not None:
        print(f"  Per employee          : {intensity['per_employee_tco2e_per_year']:.3f} tCO2e/employee/year")
    if intensity["revenue_intensity_tco2e_per_cr"] is not None:
        ri = intensity["revenue_intensity_tco2e_per_cr"]
        bm = get_benchmark_summary(ri)
        band = bm["performance_band"]
        band_color = {
            "Green":         Fore.GREEN,
            "Efficient":     Fore.GREEN,
            "Average":       Fore.YELLOW,
            "Carbon heavy":  Fore.RED,
        }.get(band, "")
        print(f"  Revenue intensity     : {ri:.3f} tCO2e/₹Cr/year")
        print(f"  Performance band      : {band_color}{band}{_reset()}")
        print(f"  vs Industry median    : {bm['gap_to_median']:+.3f} tCO2e/₹Cr  (median = {bm['industry_median']})")
        print(f"  vs Ideal target       : {bm['gap_to_ideal']:+.3f} tCO2e/₹Cr  (ideal  = {bm['ideal_target']})")

    # ── Benchmark Table ──────────────────────────────────────────────
    print(f"\n{Style.BRIGHT}INDUSTRY BENCHMARK (Indian IT SME, BRSR-derived){_reset()}")
    print(sep2)
    bm_rows = [
        ["Green",         "< 2.4",    "Top-quartile IT SMEs"],
        ["Efficient",     "2.4 – 3.0","Above average"],
        ["Average",       "3.0 – 3.6","BRSR median ≈ 3.1"],
        ["Carbon heavy",  "> 3.6",    "Below sector norms"],
    ]
    if HAS_TABULATE:
        print(tabulate(bm_rows, headers=["Band", "tCO2e/₹Cr", "Notes"], tablefmt="simple"))
    else:
        for r in bm_rows:
            print(f"  {r[0]:20} {r[1]:12} {r[2]}")

    # ── Findings / Insights ──────────────────────────────────────────
    summary = summarise_findings(findings)
    print(f"\n{Style.BRIGHT}INSIGHTS & RECOMMENDATIONS  "
          f"({summary['total']} findings: "
          f"{summary['CRITICAL']} CRIT, {summary['HIGH']} HIGH, "
          f"{summary['MEDIUM']} MED, {summary['LOW']} LOW, {summary['INFO']} INFO){_reset()}")
    print(sep2)

    if not findings:
        print("  No significant issues found.")
    else:
        for i, f in enumerate(findings, 1):
            color = _sev_color(f.severity)
            print(f"\n  {color}{f.severity.emoji()} [{f.severity.name}] {f.scope} — {f.category}{_reset()}")
            print(f"     - {f.message}")
            print(f"       Recommendation: {f.recommendation}")

    # ── Validation Notes ─────────────────────────────────────────────
    val = result["validation"]
    if val["warnings"] or val["info"]:
        print(f"\n{Style.BRIGHT}DATA NOTES{_reset()}")
        print(sep2)
        for w in val["warnings"]:
            print(f"  WARNING: {w}")
        for note in val["info"]:
            print(f"  INFO   : {note}")

    print(f"\n{Fore.CYAN}{sep}")
    print("  Report generated by Carbonaire Expert System")
    print(f"  Boundary: Scope 1 + Scope 2 + Selected Scope 3")
    print(f"  Emission factors: MoEFCC, CEA India, LCA studies")
    print(f"{sep}{_reset()}\n")


# ── JSON output ───────────────────────────────────────────────────────────────

def to_json(result: dict, findings: List[Finding], data=None, indent: int = 2) -> str:
    """
    Serialize the full result + findings to a clean JSON string.
    Safe for API responses.
    """
    output = {
        "metadata": {
            "generated_at":  datetime.now().isoformat(),
            "system":        "Carbonaire Expert System v1.0",
            "boundary":      "Scope 1 + Scope 2 + Selected Scope 3",
        },
        "company": result.get("input_summary", {}),
        "emissions": {
            "monthly": result["monthly"],
            "annual":  result["annual"],
            "scope_percentages": result["scope_percentages"],
            "scope1_breakdown":  result["scope1"],
            "scope2_breakdown":  result["scope2"],
            "scope3_breakdown":  result["scope3"],
        },
        "intensity":   result["intensity"],
        "benchmark":   _benchmark_block(result),
        "findings":    _findings_to_list(findings),
        "validation":  result["validation"],
    }
    return json.dumps(output, indent=indent, default=str)


def _benchmark_block(result: dict) -> dict:
    ri = result["intensity"].get("revenue_intensity_tco2e_per_cr")
    if ri is None:
        return {"available": False, "reason": "Revenue not provided"}
    bm = get_benchmark_summary(ri)
    bm["available"] = True
    return bm


def _findings_to_list(findings: List[Finding]) -> list:
    return [
        {
            "severity":       f.severity.name,
            "severity_value": f.severity.value,
            "scope":          f.scope,
            "category":       f.category,
            "message":        f.message,
            "recommendation": f.recommendation,
        }
        for f in findings
    ]


# ── Short summary text ────────────────────────────────────────────────────────

def to_summary_text(result: dict, findings: List[Finding]) -> str:
    """One-paragraph plain-text summary (for email/SMS/dashboard widget)."""
    annual   = result["annual"]["total_tco2e"]
    s1_pct   = result["scope_percentages"]["scope1_pct"]
    s2_pct   = result["scope_percentages"]["scope2_pct"]
    s3_pct   = result["scope_percentages"]["scope3_pct"]
    ri       = result["intensity"].get("revenue_intensity_tco2e_per_cr")
    summary  = summarise_findings(findings)

    text = (
        f"Total carbon footprint: {annual:.2f} tCO2e/year "
        f"(Scope1: {s1_pct:.0f}%, Scope2: {s2_pct:.0f}%, Scope3: {s3_pct:.0f}%). "
    )
    if ri is not None:
        text += f"Revenue intensity: {ri:.2f} tCO2e/₹Cr vs industry median of 3.1. "
    text += (
        f"Analysis found {summary['total']} insights: "
        f"{summary['CRITICAL']} critical, {summary['HIGH']} high, "
        f"{summary['MEDIUM']} medium priority."
    )
    return text
