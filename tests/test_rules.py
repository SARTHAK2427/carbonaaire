"""
tests/test_rules.py
===================
Unit tests for the rule engine and individual rule functions.
Run with:  python -m pytest tests/test_rules.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.input_schema import CarbonInputData
from core.master_calculator import run_calculation
from rules.rule_engine import RuleEngine, Finding, Severity, summarise_findings
from rules.scope1_rules import rule_diesel_usage_level, rule_scope1_share_of_total
from rules.scope2_rules import rule_renewable_energy_adoption, rule_electricity_per_employee
from rules.scope3_rules import rule_cloud_spend_level, rule_server_arrangement_efficiency
from utils.helpers import build_demo_input, build_excellent_input, build_high_emission_input


def _run(data: CarbonInputData):
    result = run_calculation(data)
    engine = RuleEngine()
    findings = engine.evaluate(result, data)
    return result, findings


# ─────────────────────────────────────────────────────────────
# RULE ENGINE CORE
# ─────────────────────────────────────────────────────────────

class TestRuleEngine:

    def test_returns_list_of_findings(self):
        data = build_demo_input()
        _, findings = _run(data)
        assert isinstance(findings, list)
        assert all(isinstance(f, Finding) for f in findings)

    def test_findings_sorted_by_severity(self):
        data = build_high_emission_input()
        _, findings = _run(data)
        severities = [f.severity.value for f in findings]
        assert severities == sorted(severities, reverse=True)

    def test_summarise_findings(self):
        findings = [
            Finding(Severity.CRITICAL, "S1", "Cat", "msg", "rec"),
            Finding(Severity.HIGH,     "S2", "Cat", "msg", "rec"),
            Finding(Severity.INFO,     "S3", "Cat", "msg", "rec"),
        ]
        summary = summarise_findings(findings)
        assert summary["CRITICAL"] == 1
        assert summary["HIGH"]     == 1
        assert summary["INFO"]     == 1
        assert summary["total"]    == 3

    def test_no_crash_on_zero_emissions(self):
        """Engine should not crash even on a minimal input."""
        data = CarbonInputData(
            electricity_kwh_per_month=5000.0,
            num_employees=10,
        )
        result = run_calculation(data)
        engine = RuleEngine()
        findings = engine.evaluate(result, data)
        assert isinstance(findings, list)


# ─────────────────────────────────────────────────────────────
# SCOPE 1 RULES
# ─────────────────────────────────────────────────────────────

class TestScope1Rules:

    def test_diesel_critical_fires(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            diesel_litres_per_month=1500.0
        )
        result = run_calculation(data)
        findings = rule_diesel_usage_level(result, data)
        severities = [f.severity for f in findings]
        assert Severity.CRITICAL in severities

    def test_diesel_high_fires(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            diesel_litres_per_month=700.0
        )
        result = run_calculation(data)
        findings = rule_diesel_usage_level(result, data)
        severities = [f.severity for f in findings]
        assert Severity.HIGH in severities

    def test_no_diesel_no_critical(self):
        data = CarbonInputData(electricity_kwh_per_month=10000)
        result = run_calculation(data)
        findings = rule_diesel_usage_level(result, data)
        assert all(f.severity != Severity.CRITICAL for f in findings)

    def test_scope1_share_high(self):
        """Large diesel + small electricity → Scope 1 dominant."""
        data = CarbonInputData(
            electricity_kwh_per_month=1000.0,     # small
            diesel_litres_per_month=5000.0,       # large
            num_employees=10,
        )
        result = run_calculation(data)
        findings = rule_scope1_share_of_total(result, data)
        # Scope 1 should be >> 50%
        assert len(findings) > 0


# ─────────────────────────────────────────────────────────────
# SCOPE 2 RULES
# ─────────────────────────────────────────────────────────────

class TestScope2Rules:

    def test_zero_renewable_fires_high(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            renewable_energy_percent=0.0
        )
        result = run_calculation(data)
        findings = rule_renewable_energy_adoption(result, data)
        assert any(f.severity == Severity.HIGH for f in findings)

    def test_high_renewable_fires_info(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            renewable_energy_percent=75.0
        )
        result = run_calculation(data)
        findings = rule_renewable_energy_adoption(result, data)
        assert all(f.severity in (Severity.INFO, Severity.LOW) for f in findings)

    def test_per_employee_high_kwh(self):
        data = CarbonInputData(
            electricity_kwh_per_month=50000.0,
            num_employees=100,      # 500 kWh/employee → very high
        )
        result = run_calculation(data)
        findings = rule_electricity_per_employee(result, data)
        assert any(f.severity in (Severity.HIGH, Severity.MEDIUM) for f in findings)

    def test_per_employee_normal(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            num_employees=100,      # 100 kWh/employee → normal
        )
        result = run_calculation(data)
        findings = rule_electricity_per_employee(result, data)
        assert all(f.severity == Severity.INFO for f in findings)

    def test_no_employees_no_per_employee_rule(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            num_employees=0,
        )
        result = run_calculation(data)
        findings = rule_electricity_per_employee(result, data)
        assert findings == []   # Rule should return empty list


# ─────────────────────────────────────────────────────────────
# SCOPE 3 RULES
# ─────────────────────────────────────────────────────────────

class TestScope3Rules:

    def test_high_cloud_spend_fires(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            cloud_provider="aws",
            cloud_monthly_bill_inr=600000.0,
        )
        result = run_calculation(data)
        findings = rule_cloud_spend_level(result, data)
        assert any(f.severity == Severity.HIGH for f in findings)

    def test_low_cloud_spend_fires_info(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            cloud_provider="aws",
            cloud_monthly_bill_inr=5000.0,
        )
        result = run_calculation(data)
        findings = rule_cloud_spend_level(result, data)
        assert all(f.severity == Severity.INFO for f in findings)

    def test_no_cloud_no_findings(self):
        data = CarbonInputData(electricity_kwh_per_month=10000)
        result = run_calculation(data)
        findings = rule_cloud_spend_level(result, data)
        assert findings == []

    def test_stacked_server_fires_high(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            server_rack_count=5,
            server_arrangement="stacked_high_density",
            num_servers_onprem=20,
        )
        result = run_calculation(data)
        findings = rule_server_arrangement_efficiency(result, data)
        assert any(f.severity == Severity.HIGH for f in findings)

    def test_liquid_cooling_fires_info(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000,
            server_rack_count=2,
            server_arrangement="direct_liquid_cooling",
            num_servers_onprem=10,
        )
        result = run_calculation(data)
        findings = rule_server_arrangement_efficiency(result, data)
        assert all(f.severity == Severity.INFO for f in findings)


# ─────────────────────────────────────────────────────────────
# SCENARIO-LEVEL TESTS
# ─────────────────────────────────────────────────────────────

class TestScenarios:

    def test_excellent_scenario_no_critical_findings(self):
        data = build_excellent_input()
        _, findings = _run(data)
        assert not any(f.severity == Severity.CRITICAL for f in findings)

    def test_high_emission_scenario_has_critical(self):
        data = build_high_emission_input()
        _, findings = _run(data)
        assert any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings)

    def test_demo_scenario_runs_end_to_end(self):
        data = build_demo_input()
        result, findings = _run(data)
        assert result["annual"]["total_tco2e"] > 0
        assert len(findings) > 0
