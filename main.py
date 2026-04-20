"""
main.py
=======
Carbonaire Expert System — CLI Entry Point

Usage:
  python main.py              # Interactive mode — enter company data manually
  python main.py --demo       # Run pre-built demo scenario (no input required)
  python main.py --all-demos  # Run all 3 built-in scenarios (excellent, demo, high)
  python main.py --json       # Demo + output raw JSON
  python main.py --test       # Quick smoke test (same as pytest but inline)

"""

import sys
import os
import argparse

# Make sure local modules are found regardless of where the script is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.input_schema import CarbonInputData, inputs_from_dict, validate_inputs
from core.master_calculator import run_calculation
from rules.rule_engine import RuleEngine, summarise_findings
from utils.report_generator import print_report, to_json, to_summary_text
from utils.helpers import (
    build_demo_input,
    build_excellent_input,
    build_high_emission_input,
    build_minimal_input,
    load_inputs_from_excel,
    extract_from_electricity_document,
)


# ─────────────────────────────────────────────────────────────
# CORE RUNNER
# ─────────────────────────────────────────────────────────────

def run_pipeline(data: CarbonInputData, output_json: bool = False):
    """Run the full pipeline on a CarbonInputData object."""
    try:
        result   = run_calculation(data)
    except ValueError as e:
        print(f"\n❌ Validation Error:\n{e}")
        return

    engine   = RuleEngine()
    findings = engine.evaluate(result, data)

    if output_json:
        print(to_json(result, findings, data))
    else:
        print_report(result, findings, data)

    return result, findings


# ─────────────────────────────────────────────────────────────
# INTERACTIVE INPUT MODE
# ─────────────────────────────────────────────────────────────

def _ask(prompt: str, default, cast=str):
    """Ask user for input with a default fallback."""
    val = input(f"  {prompt} [{default}]: ").strip()
    if val == "":
        return default
    try:
        return cast(val)
    except (ValueError, TypeError):
        print(f"  ⚠️  Invalid input, using default: {default}")
        return default


def interactive_mode():
    """Walk the user through input collection, with Excel + document options."""
    print("\n🌿  CARBONAIRE — Carbon Footprint Calculator")
    print("    Press Enter to accept the default value shown in [ ]\n")

    print("If you have the official Carbonaire Excel Input Template filled in,")
    print("you can upload it now to auto-load all required fields.")
    print("Otherwise, press Enter to skip and enter data manually.\n")

    excel_path = input("  Path to filled Excel template (or press Enter to skip): ").strip()
    data_from_excel = None
    if excel_path:
        try:
            data_from_excel = load_inputs_from_excel(excel_path)
            print("\n  ✅ Excel template loaded successfully. Using these values for the run.\n")
        except Exception as e:
            print(f"\n❌ Could not read or validate Excel template:")
            print(f"   {e}")
            print("\n   Please ensure it follows the Carbonaire template format and has all")
            print("   required columns filled (e.g. company_name, industry_type,")
            print("   location_state, num_employees, annual_revenue_inr_cr,")
            print("   electricity_kwh_per_month, etc.).")
            print("   Falling back to manual data entry.\n")
            data_from_excel = None

    if data_from_excel is not None:
        run_pipeline(data_from_excel)
        return

    # Manual entry, with optional electricity bill upload and supporting documents
    bill_info = {}
    use_bill = input(
        "  Do you want to upload an electricity bill (PDF/Excel) to auto-fill "
        "location and electricity consumption? [y/N]: "
    ).strip().lower()

    if use_bill.startswith("y"):
        bill_path = input("  Path to electricity bill file: ").strip()
        try:
            bill_info = extract_from_electricity_document(bill_path)
            print("\n  Parsed from bill (you can still override below):")
            if "location_state" in bill_info:
                print(f"    Location/state: {bill_info['location_state']}")
            if "electricity_kwh_per_month" in bill_info:
                print(f"    Electricity/month (kWh): {bill_info['electricity_kwh_per_month']}")
            print()
        except Exception as e:
            print(f"\n  ⚠️  Could not parse electricity bill automatically: {e}")
            print("      Falling back to manual inputs.\n")
            bill_info = {}

    uploaded_docs = bill_info.get("uploaded_docs", [])

    # Ask for additional supporting documents to store for audit / accuracy
    print("Optional: you can attach supporting documents to improve traceability.")
    print("These are not strictly required but are recommended:")
    print("  - Hardware acquisition invoices (IT equipment, servers, etc.)")
    print("  - Cloud services bills (AWS/Azure/GCP)")
    print("  - Fuel purchase records (diesel/petrol/LPG, etc.)\n")

    hw_doc = input("  Path to hardware acquisition invoice (or press Enter to skip): ").strip()
    if hw_doc:
        uploaded_docs.append(os.path.basename(hw_doc))

    cloud_doc = input("  Path to cloud services bill (or press Enter to skip): ").strip()
    if cloud_doc:
        uploaded_docs.append(os.path.basename(cloud_doc))

    fuel_doc = input("  Path to fuel purchase record (or press Enter to skip): ").strip()
    if fuel_doc:
        uploaded_docs.append(os.path.basename(fuel_doc))

    data = CarbonInputData(
        company_name  = _ask("Company name",        "My Company"),
        industry_type = _ask("Industry type",       "IT"),
        location_state= _ask(
            "State (e.g. karnataka, maharashtra, delhi)",
            bill_info.get("location_state", "default"),
        ).lower().replace(" ","_"),
        num_employees = _ask("Number of employees", 50,    int),
        annual_revenue_inr_cr = _ask("Annual revenue (₹ Crore)", 10.0, float),
        working_hours_per_day = _ask("Working hours per day",     8.0,  float),

        # Scope 1
        diesel_litres_per_month    = _ask("Diesel consumed/month (litres)",      0.0, float),
        petrol_litres_per_month    = _ask("Petrol consumed/month (litres)",      0.0, float),
        natural_gas_m3_per_month   = _ask("Natural gas consumed/month (m³)",     0.0, float),
        lpg_litres_per_month       = _ask("LPG consumed/month (litres)",         0.0, float),
        power_backup_runtime_hours = _ask("Generator runtime/month (hours)",     0.0, float),

        # Scope 2
        electricity_kwh_per_month  = _ask(
            "Electricity consumed/month (kWh)",
            bill_info.get("electricity_kwh_per_month", 5000.0),
            float,
        ),
        renewable_energy_percent   = _ask("Renewable energy used (%)",           0.0,    float),

        # Servers
        server_rack_count          = _ask("Server rack count",                   0,   int),
        server_operating_hours_per_day = _ask("Server operating hours/day",      24.0, float),
        server_arrangement         = _ask(
            "Server arrangement [hot_aisle_cold_aisle / stacked_high_density / direct_liquid_cooling / custom]",
            "hot_aisle_cold_aisle"
        ).lower().replace(" ","_"),
        server_area_sqft           = _ask("Server room area (sq ft)",            0.0, float),

        # Devices
        num_laptops                = _ask("Number of laptops",                   0,   int),
        num_desktops               = _ask("Number of desktops",                  0,   int),
        num_servers_onprem         = _ask("Number of on-premise servers",        0,   int),
        num_monitors               = _ask("Number of monitors",                  0,   int),

        # Cloud
        cloud_provider             = _ask("Cloud provider [aws/azure/gcp/none]", "none").lower(),
        cloud_monthly_bill_inr     = _ask("Monthly cloud bill (₹, 0 if none)",  0.0, float),
        cloud_compute_hours_per_month = _ask("Cloud compute hours/month (0 if using bill)", 0.0, float),
        cloud_kwh_per_month        = _ask("Cloud kWh/month (0 if unknown)",      0.0, float),

        # Purchased services
        purchased_services_spend_inr_per_month = _ask(
            "Purchased services spend/month (₹, e.g. SaaS, outsourcing)", 0.0, float
        ),

        # Documents (if any) used during input collection
        uploaded_docs = uploaded_docs,
    )

    run_pipeline(data)


# ─────────────────────────────────────────────────────────────
# QUICK SMOKE TEST
# ─────────────────────────────────────────────────────────────

def quick_smoke_test():
    """Run inline smoke tests — used when pytest is not available."""
    print("\nRunning quick smoke tests...\n")
    scenarios = [
        ("Demo (mid-sized IT SME)",     build_demo_input()),
        ("Excellent (green company)",   build_excellent_input()),
        ("High emission (old-school)",  build_high_emission_input()),
        ("Minimal (electricity only)",  build_minimal_input()),
    ]

    passed = 0
    failed = 0

    for name, data in scenarios:
        try:
            result   = run_calculation(data)
            engine   = RuleEngine()
            findings = engine.evaluate(result, data)
            summary  = summarise_findings(findings)
            annual   = result["annual"]["total_tco2e"]
            assert annual >= 0, "Negative emissions!"
            assert len(findings) >= 0
            print(f"  PASS  {name:40} -> {annual:.2f} tCO2e/yr | {summary['total']} findings")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name:40} -> FAILED: {e}")
            failed += 1

    print(f"\n  Result: {passed} passed, {failed} failed")
    return failed == 0


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Carbonaire — Carbon Footprint Expert System"
    )
    parser.add_argument("--demo",      action="store_true", help="Run demo scenario")
    parser.add_argument("--all-demos", action="store_true", help="Run all 3 built-in scenarios")
    parser.add_argument("--json",      action="store_true", help="Output JSON instead of formatted report")
    parser.add_argument("--test",      action="store_true", help="Run quick smoke tests")
    args = parser.parse_args()

    if args.test:
        success = quick_smoke_test()
        sys.exit(0 if success else 1)

    elif args.all_demos:
        scenarios = [
            ("🟢 Excellent — GreenTech India",     build_excellent_input()),
            ("🟡 Typical  — TechNova Solutions",   build_demo_input()),
            ("🔴 High     — OldSchool IT",          build_high_emission_input()),
        ]
        for title, data in scenarios:
            print(f"\n{'='*70}")
            print(f"  SCENARIO: {title}")
            print(f"{'='*70}")
            run_pipeline(data, output_json=args.json)

    elif args.demo:
        data = build_demo_input()
        run_pipeline(data, output_json=args.json)

    else:
        interactive_mode()


if __name__ == "__main__":
    main()
