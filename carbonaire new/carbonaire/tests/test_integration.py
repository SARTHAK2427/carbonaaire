"""
tests/test_integration.py
=========================
End-to-end integration tests for the full Carbonaire pipeline:
  Input → Validation → Scope 1/2/3 Calc → Rule Engine → Report

Run with:  python -m pytest tests/test_integration.py -v
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.input_schema import CarbonInputData, inputs_from_dict, validate_inputs
from core.master_calculator import run_calculation
from rules.rule_engine import RuleEngine, summarise_findings
from utils.report_generator import to_json, to_summary_text
from utils.helpers import build_demo_input, build_excellent_input, build_high_emission_input
from benchmarks.industry_benchmark import get_performance_band, get_benchmark_summary


# ─────────────────────────────────────────────────────────────
# PIPELINE TESTS
# ─────────────────────────────────────────────────────────────

def _full_pipeline(data: CarbonInputData):
    """Runs the complete pipeline and returns (result, findings, json_out)."""
    result   = run_calculation(data)
    engine   = RuleEngine()
    findings = engine.evaluate(result, data)
    json_out = to_json(result, findings, data)
    return result, findings, json_out


class TestFullPipeline:

    def test_demo_pipeline_runs(self):
        data = build_demo_input()
        result, findings, json_out = _full_pipeline(data)

        # Basic output checks
        assert result["annual"]["total_tco2e"] > 0
        assert len(findings) > 0
        assert isinstance(json_out, str)
        parsed = json.loads(json_out)
        assert "emissions" in parsed
        assert "findings" in parsed

    def test_excellent_company_benchmark_band(self):
        """GreenTech with 80% renewables should be Excellent or Good."""
        data = build_excellent_input()
        result, findings, _ = _full_pipeline(data)
        ri = result["intensity"]["revenue_intensity_tco2e_per_cr"]
        band = get_performance_band(ri)
        assert band in ("Excellent", "Good"), f"Expected Excellent/Good, got {band} ({ri:.2f})"

    def test_high_emission_company_benchmark_band(self):
        """Old-school company should land in High band."""
        data = build_high_emission_input()
        result, findings, _ = _full_pipeline(data)
        ri = result["intensity"]["revenue_intensity_tco2e_per_cr"]
        band = get_performance_band(ri)
        assert band in ("High", "Industry Normal"), f"Expected High/Normal, got {band} ({ri:.2f})"

    def test_json_output_is_valid_json(self):
        data = build_demo_input()
        result = run_calculation(data)
        engine = RuleEngine()
        findings = engine.evaluate(result, data)
        json_str = to_json(result, findings)
        parsed = json.loads(json_str)  # must not throw
        assert "metadata" in parsed
        assert "emissions" in parsed
        assert "benchmark" in parsed

    def test_summary_text_generated(self):
        data = build_demo_input()
        result = run_calculation(data)
        engine = RuleEngine()
        findings = engine.evaluate(result, data)
        text = to_summary_text(result, findings)
        assert "tCO2e/year" in text
        assert len(text) > 50

    def test_inputs_from_dict(self):
        """Build input from a flat dict (simulating API payload)."""
        payload = {
            "company_name":              "Dict Test Co",
            "electricity_kwh_per_month": 8000.0,
            "diesel_litres_per_month":   300.0,
            "location_state":            "maharashtra",
            "num_employees":             60,
            "annual_revenue_inr_cr":     15.0,
            "renewable_energy_percent":  20.0,
            "num_laptops":               55,
            "cloud_provider":            "azure",
            "cloud_monthly_bill_inr":    40000.0,
        }
        data = inputs_from_dict(payload)
        result, findings, json_out = _full_pipeline(data)
        assert result["annual"]["total_tco2e"] > 0


# ─────────────────────────────────────────────────────────────
# BOUNDARY / EDGE CASES
# ─────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_only_electricity_provided(self):
        data = CarbonInputData(
            electricity_kwh_per_month=5000.0,
            num_employees=10,
            annual_revenue_inr_cr=2.0,
        )
        result, findings, json_out = _full_pipeline(data)
        assert result["scope1"]["total_tco2e"] == 0.0
        assert result["scope2"]["total_tco2e"] > 0.0

    def test_no_revenue_no_benchmark(self):
        data = CarbonInputData(
            electricity_kwh_per_month=5000.0,
            annual_revenue_inr_cr=0.0,
        )
        result = run_calculation(data)
        assert result["intensity"]["revenue_intensity_tco2e_per_cr"] is None

    def test_validation_catches_bad_renewable_pct(self):
        data = CarbonInputData(
            electricity_kwh_per_month=5000.0,
            renewable_energy_percent=150.0
        )
        val = validate_inputs(data)
        assert len(val["errors"]) > 0

    def test_very_large_input(self):
        """System should handle large enterprise-scale numbers without error."""
        data = CarbonInputData(
            electricity_kwh_per_month=500_000.0,
            diesel_litres_per_month=50_000.0,
            petrol_litres_per_month=10_000.0,
            num_employees=5000,
            annual_revenue_inr_cr=2000.0,
            num_laptops=4500,
            num_servers_onprem=500,
            cloud_monthly_bill_inr=10_000_000.0,
        )
        result, findings, _ = _full_pipeline(data)
        assert result["annual"]["total_tco2e"] > 0
        assert result["annual"]["total_tco2e"] < 1_000_000   # sanity upper bound

    def test_all_scope3_zero_when_no_data(self):
        """With no Scope 3 inputs and no electricity, Scope 3 T&D = 0."""
        data = CarbonInputData(electricity_kwh_per_month=5000.0)
        result = run_calculation(data)
        s3 = result["scope3"]
        assert s3["cloud"]["tco2e"]  == 0.0
        assert s3["services"]["tco2e"] == 0.0


# ─────────────────────────────────────────────────────────────
# BENCHMARK MODULE TESTS
# ─────────────────────────────────────────────────────────────

class TestBenchmarkModule:

    def test_excellent_band(self):
        assert get_performance_band(1.5)  == "Excellent"
        assert get_performance_band(2.39) == "Excellent"

    def test_good_band(self):
        assert get_performance_band(2.4)  == "Good"
        assert get_performance_band(2.99) == "Good"

    def test_normal_band(self):
        assert get_performance_band(3.0)  == "Industry Normal"
        assert get_performance_band(3.59) == "Industry Normal"

    def test_high_band(self):
        assert get_performance_band(3.6)  == "High"
        assert get_performance_band(10.0) == "High"

    def test_benchmark_summary_structure(self):
        bm = get_benchmark_summary(3.5)
        assert "performance_band"      in bm
        assert "gap_to_median"         in bm
        assert "gap_to_ideal"          in bm
        assert "industry_median"       in bm
        assert bm["industry_median"]   == 3.1
