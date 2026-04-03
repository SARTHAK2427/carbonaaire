"""
tests/test_calculators.py
=========================
Unit tests for Scope 1, 2, 3, and Master calculators.
Run with:  python -m pytest tests/test_calculators.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.input_schema import CarbonInputData
from core.scope1_calculator import calculate_scope1
from core.scope2_calculator import calculate_scope2
from core.scope3_calculator import calculate_scope3
from core.master_calculator import run_calculation


# ─────────────────────────────────────────────────────────────
# SCOPE 1 TESTS
# ─────────────────────────────────────────────────────────────

class TestScope1Calculator:

    def test_diesel_only(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            diesel_litres_per_month=1000.0
        )
        result = calculate_scope1(data)
        # 1000 L × 2.68 kg/L ÷ 1000 = 2.68 tCO2e
        assert abs(result["diesel_tco2e"] - 2.68) < 0.001
        assert result["petrol_tco2e"] == 0.0
        assert result["total_tco2e"] == result["diesel_tco2e"]

    def test_petrol_only(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            petrol_litres_per_month=500.0
        )
        result = calculate_scope1(data)
        # 500 × 2.31 ÷ 1000 = 1.155
        assert abs(result["petrol_tco2e"] - 1.155) < 0.001

    def test_natural_gas(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            natural_gas_m3_per_month=100.0
        )
        result = calculate_scope1(data)
        # 100 × 1.9 ÷ 1000 = 0.19
        assert abs(result["natural_gas_tco2e"] - 0.19) < 0.001

    def test_all_fuels(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            diesel_litres_per_month=100.0,
            petrol_litres_per_month=100.0,
            natural_gas_m3_per_month=100.0,
            lpg_litres_per_month=100.0
        )
        result = calculate_scope1(data)
        assert result["total_tco2e"] > 0
        expected_diesel  = (100 * 2.68) / 1000
        expected_petrol  = (100 * 2.31) / 1000
        expected_gas     = (100 * 1.90) / 1000
        expected_lpg     = (100 * 2.98) / 1000
        expected_total   = expected_diesel + expected_petrol + expected_gas + expected_lpg
        assert abs(result["total_tco2e"] - expected_total) < 0.001

    def test_zero_fuel(self):
        data = CarbonInputData(electricity_kwh_per_month=1000)
        result = calculate_scope1(data)
        assert result["total_tco2e"] == 0.0

    def test_breakdown_keys_present(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            diesel_litres_per_month=500
        )
        result = calculate_scope1(data)
        assert "breakdown" in result
        assert "diesel" in result["breakdown"]
        assert "ef_kg_per_unit" in result["breakdown"]["diesel"]


# ─────────────────────────────────────────────────────────────
# SCOPE 2 TESTS
# ─────────────────────────────────────────────────────────────

class TestScope2Calculator:

    def test_basic_calculation(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            location_state="default",
            renewable_energy_percent=0.0
        )
        result = calculate_scope2(data)
        # 10000 × 0.82 ÷ 1000 = 8.2 tCO2e
        assert abs(result["total_tco2e"] - 8.2) < 0.01

    def test_renewable_offset(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            location_state="default",
            renewable_energy_percent=50.0
        )
        result = calculate_scope2(data)
        # 10000 × 0.5 × 0.82 ÷ 1000 = 4.1
        assert abs(result["total_tco2e"] - 4.1) < 0.01
        assert result["renewable_fraction"] == 0.5

    def test_100_percent_renewable(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            renewable_energy_percent=100.0
        )
        result = calculate_scope2(data)
        assert result["total_tco2e"] == 0.0

    def test_state_grid_ef_karnataka(self):
        """Karnataka has lower EF (0.60) due to high renewables."""
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            location_state="karnataka",
            renewable_energy_percent=0.0
        )
        result = calculate_scope2(data)
        assert abs(result["grid_ef_used"] - 0.60) < 0.001
        # 10000 × 0.60 ÷ 1000 = 6.0
        assert abs(result["total_tco2e"] - 6.0) < 0.01

    def test_state_grid_ef_rajasthan(self):
        """Rajasthan has higher EF (0.90)."""
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            location_state="rajasthan",
            renewable_energy_percent=0.0
        )
        result = calculate_scope2(data)
        assert abs(result["grid_ef_used"] - 0.90) < 0.001

    def test_unknown_state_falls_back_to_default(self):
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            location_state="unknown_state"
        )
        result = calculate_scope2(data)
        assert result["grid_ef_used"] == 0.82   # default

    def test_renewable_clamped_to_100(self):
        """Renewable % > 100 should be clamped."""
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            renewable_energy_percent=150.0
        )
        result = calculate_scope2(data)
        assert result["total_tco2e"] == 0.0


# ─────────────────────────────────────────────────────────────
# SCOPE 3 TESTS
# ─────────────────────────────────────────────────────────────

class TestScope3Calculator:

    def test_cloud_spend_based(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            cloud_provider="aws",
            cloud_monthly_bill_inr=100000.0
        )
        result = calculate_scope3(data, scope2_total_tco2e=5.0)
        # 100000 INR × 0.001 kg/INR = 100 kg = 0.1 tCO2e
        assert result["cloud"]["method"] == "spend_based_eeio"
        assert result["cloud"]["tco2e"] > 0

    def test_cloud_kwh_based_priority(self):
        """kWh-based should be chosen over spend-based when both provided."""
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            cloud_kwh_per_month=1000.0,
            cloud_monthly_bill_inr=100000.0
        )
        result = calculate_scope3(data, scope2_total_tco2e=5.0)
        assert result["cloud"]["method"] == "kwh_based"
        # 1000 × 0.40 ÷ 1000 = 0.4
        assert abs(result["cloud"]["tco2e"] - 0.4) < 0.001

    def test_device_lifecycle(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            num_laptops=10,
            num_desktops=5,
        )
        result = calculate_scope3(data, scope2_total_tco2e=5.0)
        # Laptops: (10 × 300) / 3.5 = 857.14 kg/year → 71.4 kg/month → 0.0714 tCO2e/month
        # Desktops:(5 × 400) / 4.0  = 500 kg/year    → 41.7 kg/month → 0.0417 tCO2e/month
        expected = ((10 * 300 / 3.5) + (5 * 400 / 4.0)) / 1000 / 12
        assert abs(result["devices"]["total_monthly_tco2e"] - expected) < 0.0001

    def test_td_losses(self):
        data = CarbonInputData(electricity_kwh_per_month=1000)
        result = calculate_scope3(data, scope2_total_tco2e=10.0)
        # 10.0 × 0.08 = 0.8
        assert abs(result["td_losses"]["tco2e"] - 0.8) < 0.001

    def test_purchased_services(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            purchased_services_spend_inr_per_month=100000.0
        )
        result = calculate_scope3(data, scope2_total_tco2e=5.0)
        # 100000 × 0.001 ÷ 1000 = 0.0001 tCO2e
        assert result["services"]["tco2e"] >= 0

    def test_zero_scope3(self):
        data = CarbonInputData(electricity_kwh_per_month=1000)
        result = calculate_scope3(data, scope2_total_tco2e=0.0)
        assert result["total_tco2e"] == 0.0

    def test_total_is_sum_of_parts(self):
        data = CarbonInputData(
            electricity_kwh_per_month=1000,
            num_laptops=50,
            cloud_monthly_bill_inr=50000,
            purchased_services_spend_inr_per_month=30000,
        )
        result = calculate_scope3(data, scope2_total_tco2e=8.0)
        expected_total = (
            result["cloud"]["tco2e"]
            + result["devices"]["total_monthly_tco2e"]
            + result["td_losses"]["tco2e"]
            + result["services"]["tco2e"]
        )
        assert abs(result["total_tco2e"] - expected_total) < 0.0001


# ─────────────────────────────────────────────────────────────
# MASTER CALCULATOR TESTS
# ─────────────────────────────────────────────────────────────

class TestMasterCalculator:

    def _demo_data(self):
        return CarbonInputData(
            company_name="Test Co",
            electricity_kwh_per_month=10000.0,
            diesel_litres_per_month=200.0,
            num_employees=50,
            annual_revenue_inr_cr=10.0,
            location_state="karnataka",
            num_laptops=40,
        )

    def test_run_returns_all_keys(self):
        data = self._demo_data()
        result = run_calculation(data)
        for key in ("scope1", "scope2", "scope3", "monthly", "annual",
                    "intensity", "scope_percentages", "validation"):
            assert key in result, f"Missing key: {key}"

    def test_total_is_sum_of_scopes(self):
        data = self._demo_data()
        result = run_calculation(data)
        expected = (
            result["monthly"]["scope1_tco2e"]
            + result["monthly"]["scope2_tco2e"]
            + result["monthly"]["scope3_tco2e"]
        )
        assert abs(result["monthly"]["total_tco2e"] - expected) < 0.001

    def test_annual_is_12x_monthly(self):
        data = self._demo_data()
        result = run_calculation(data)
        assert abs(result["annual"]["total_tco2e"] - result["monthly"]["total_tco2e"] * 12) < 0.01

    def test_scope_percentages_sum_to_100(self):
        data = self._demo_data()
        result = run_calculation(data)
        total_pct = sum(result["scope_percentages"].values())
        assert abs(total_pct - 100.0) < 0.1

    def test_per_employee_intensity(self):
        data = self._demo_data()
        result = run_calculation(data)
        assert result["intensity"]["per_employee_tco2e_per_year"] is not None
        assert result["intensity"]["per_employee_tco2e_per_year"] > 0

    def test_revenue_intensity(self):
        data = self._demo_data()
        result = run_calculation(data)
        assert result["intensity"]["revenue_intensity_tco2e_per_cr"] is not None

    def test_validation_error_raised(self):
        """Missing electricity should raise ValueError."""
        data = CarbonInputData(electricity_kwh_per_month=0)
        with pytest.raises(ValueError):
            run_calculation(data)

    def test_zero_emissions_scenario(self):
        """100% renewable, no fuel — Scope 1 and 2 should be ~0."""
        data = CarbonInputData(
            electricity_kwh_per_month=10000.0,
            renewable_energy_percent=100.0,
            num_employees=10,
            annual_revenue_inr_cr=5.0,
        )
        result = run_calculation(data)
        assert result["scope1"]["total_tco2e"] == 0.0
        assert result["scope2"]["total_tco2e"] == 0.0
