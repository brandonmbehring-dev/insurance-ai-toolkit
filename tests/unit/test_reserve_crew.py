"""Unit tests for ReserveCrew.

Tests validate:
1. Scenario generation (GBM paths, Vasicek rates)
2. Cash flow projection (mortality/lapse/discounting)
3. CTE calculation (percentiles, risk margin)
4. Sensitivity analysis (rate/vol/lapse shocks)
5. Convergence validation (regulatory compliance)

Validation criteria (outcome-based, not coverage metrics):
- CTE70 >= Mean (mathematical invariant)
- Convergence error < 2%
- All scenarios non-empty
- All fields populated correctly
"""

import json
import unittest
from pathlib import Path

from insurance_ai.crews.reserve import (
    ReserveState,
    ProductType,
    CalculationMethod,
    run_reserve_crew,
    build_reserve_crew,
)


class TestReserveCrewBasic(unittest.TestCase):
    """Test basic ReserveCrew functionality."""

    def test_build_reserve_crew_compiles(self) -> None:
        """ReserveCrew should compile without errors."""
        crew = build_reserve_crew()
        self.assertIsNotNone(crew)
        # Verify it's a compiled graph
        self.assertTrue(hasattr(crew, "invoke"))

    def test_va_glwb_basic(self) -> None:
        """VA with GLWB should execute and produce valid reserves."""
        state = ReserveState(
            policy_id="test_va_basic",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # Verify output fields populated
        self.assertEqual(result.policy_id, "test_va_basic")
        self.assertEqual(result.product_type, ProductType.VA_GLWB)
        self.assertGreater(len(result.economic_scenarios), 0)
        self.assertGreater(len(result.reserve_paths), 0)
        self.assertGreater(result.cte70_reserve, 0)
        self.assertGreater(result.mean_reserve, 0)

    def test_fia_basic(self) -> None:
        """FIA should execute and produce valid reserves."""
        state = ReserveState(
            policy_id="test_fia_basic",
            product_type=ProductType.FIA,
            issue_age=60,
            policy_month=60,
            account_value=500000,
            benefit_base=500000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=20,
            scenario_seed=99,
        )

        result = run_reserve_crew(state)

        # Verify FIA output
        self.assertEqual(result.product_type, ProductType.FIA)
        self.assertGreater(result.vm22_reserve, 0)
        self.assertEqual(result.vm22_reserve, result.cte70_reserve)

    def test_rila_basic(self) -> None:
        """RILA should execute and produce valid reserves."""
        state = ReserveState(
            policy_id="test_rila_basic",
            product_type=ProductType.RILA,
            issue_age=50,
            policy_month=24,
            account_value=400000,
            benefit_base=420000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=25,
            scenario_seed=77,
        )

        result = run_reserve_crew(state)

        self.assertEqual(result.product_type, ProductType.RILA)
        self.assertGreater(result.vm22_reserve, 0)


class TestScenarioGeneration(unittest.TestCase):
    """Test scenario generation agent."""

    def test_scenarios_generated(self) -> None:
        """Scenarios should be generated and populated."""
        state = ReserveState(
            policy_id="test_scenario_gen",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # Verify scenarios structure
        self.assertEqual(len(result.economic_scenarios), 100)
        for scenario in result.economic_scenarios:
            self.assertIn("scenario_id", scenario)
            self.assertIn("equity_path", scenario)
            self.assertIn("rate_path", scenario)
            self.assertIn("final_equity_level", scenario)
            self.assertIn("final_rate", scenario)
            # Paths should be non-empty and positive
            self.assertGreater(len(scenario["equity_path"]), 0)
            self.assertGreater(len(scenario["rate_path"]), 0)
            self.assertGreater(scenario["final_equity_level"], 0)

    def test_scenario_equity_paths_positive(self) -> None:
        """GBM paths should always be positive (GBM property)."""
        state = ReserveState(
            policy_id="test_gbm_positive",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=50,
            num_years=10,
            scenario_seed=123,
        )

        result = run_reserve_crew(state)

        for scenario in result.economic_scenarios:
            for equity_level in scenario["equity_path"]:
                self.assertGreater(
                    equity_level, 0, "GBM path values must be positive"
                )

    def test_scenario_seed_reproducibility(self) -> None:
        """Same seed should produce identical scenarios."""
        state1 = ReserveState(
            policy_id="test_seed_1",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=50,
            num_years=10,
            scenario_seed=42,
        )
        state2 = ReserveState(
            policy_id="test_seed_2",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=50,
            num_years=10,
            scenario_seed=42,
        )

        result1 = run_reserve_crew(state1)
        result2 = run_reserve_crew(state2)

        # Same seed → same cte70
        self.assertAlmostEqual(
            result1.cte70_reserve, result2.cte70_reserve, places=2
        )


class TestCTECalculation(unittest.TestCase):
    """Test CTE calculation and percentile validation."""

    def test_cte_gte_mean_invariant(self) -> None:
        """CTE70 must always be >= Mean (mathematical property)."""
        state = ReserveState(
            policy_id="test_cte_invariant",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # CTE70 >= Mean (within rounding tolerance)
        self.assertGreaterEqual(
            result.cte70_reserve, result.mean_reserve - 1.0  # 1.0 tolerance for rounding
        )

    def test_percentiles_monotonic(self) -> None:
        """Percentiles should be monotonically increasing."""
        state = ReserveState(
            policy_id="test_percentile_mono",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # Percentiles should increase
        p10 = result.percentile_reserves[10]
        p25 = result.percentile_reserves[25]
        p50 = result.percentile_reserves[50]
        p75 = result.percentile_reserves[75]
        p90 = result.percentile_reserves[90]

        self.assertLess(p10, p25)
        self.assertLess(p25, p50)
        self.assertLess(p50, p75)
        self.assertLess(p75, p90)

    def test_cte70_cte90_relationship(self) -> None:
        """CTE90 should be >= CTE70 (more extreme tail)."""
        state = ReserveState(
            policy_id="test_cte90_gte_cte70",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # CTE90 is more extreme than CTE70
        self.assertGreaterEqual(result.cte90_reserve, result.cte70_reserve - 1.0)

    def test_risk_margin_positive(self) -> None:
        """Risk margin (CTE70 - Mean) should be positive."""
        state = ReserveState(
            policy_id="test_risk_margin",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        self.assertGreaterEqual(result.risk_margin, 0.0)
        self.assertLess(result.risk_margin, result.cte70_reserve)  # Margin < total


class TestSensitivityAnalysis(unittest.TestCase):
    """Test sensitivity to assumption shocks."""

    def test_rate_shock_up_decreases_reserve(self) -> None:
        """Higher rates should decrease reserve (less PV)."""
        state = ReserveState(
            policy_id="test_rate_up",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        rates_up_results = result.sensitivity_results.get("rates_up", {})
        rates_up_valid = result.sensitivity_monotonicity.get("rates_up", False)

        # Direction validation should pass
        self.assertTrue(rates_up_valid)
        # Reserve should decrease
        change = rates_up_results.get("change_percent", 0)
        self.assertLess(change, 0)

    def test_vol_shock_up_increases_reserve(self) -> None:
        """Higher volatility should increase reserve (more tail risk)."""
        state = ReserveState(
            policy_id="test_vol_up",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        vol_up_results = result.sensitivity_results.get("vol_up", {})
        vol_up_valid = result.sensitivity_monotonicity.get("vol_up", False)

        self.assertTrue(vol_up_valid)
        change = vol_up_results.get("change_percent", 0)
        self.assertGreater(change, 0)

    def test_lapse_shock_up_decreases_reserve(self) -> None:
        """Higher lapse should decrease reserve (shorter duration)."""
        state = ReserveState(
            policy_id="test_lapse_up",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        lapse_up_results = result.sensitivity_results.get("lapse_up", {})
        lapse_up_valid = result.sensitivity_monotonicity.get("lapse_up", False)

        self.assertTrue(lapse_up_valid)
        change = lapse_up_results.get("change_percent", 0)
        self.assertLess(change, 0)

    def test_all_sensitivity_shocks_populated(self) -> None:
        """All sensitivity shocks should be calculated."""
        state = ReserveState(
            policy_id="test_all_shocks",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        expected_shocks = ["rates_up", "rates_down", "vol_up", "vol_down", "lapse_up"]
        for shock in expected_shocks:
            self.assertIn(shock, result.sensitivity_results)
            self.assertIn(shock, result.sensitivity_monotonicity)


class TestConvergenceValidation(unittest.TestCase):
    """Test convergence and regulatory compliance."""

    def test_convergence_validated(self) -> None:
        """Convergence should be checked."""
        state = ReserveState(
            policy_id="test_convergence",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        # Convergence metrics should exist
        self.assertGreaterEqual(result.convergence_error_percent, 0.0)
        self.assertLessEqual(result.convergence_error_percent, 1.0)  # Should be <2%
        self.assertIsInstance(result.converged, bool)

    def test_vm21_compliance_for_va(self) -> None:
        """VA reserves should be classified as VM-21."""
        state = ReserveState(
            policy_id="test_vm21",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        self.assertIn("regulatory_standard", result.validation_metrics)
        self.assertEqual(
            result.validation_metrics["regulatory_standard"], "VM-21 (Variable Annuity)"
        )
        self.assertGreater(result.vm21_reserve, 0)

    def test_vm22_compliance_for_fia(self) -> None:
        """FIA reserves should be classified as VM-22."""
        state = ReserveState(
            policy_id="test_vm22_fia",
            product_type=ProductType.FIA,
            issue_age=60,
            policy_month=60,
            account_value=500000,
            benefit_base=500000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=20,
            scenario_seed=99,
        )

        result = run_reserve_crew(state)

        self.assertIn("regulatory_standard", result.validation_metrics)
        self.assertEqual(
            result.validation_metrics["regulatory_standard"], "VM-22 (Fixed Annuity)"
        )
        self.assertGreater(result.vm22_reserve, 0)

    def test_validation_metrics_populated(self) -> None:
        """Validation metrics should include key statistics."""
        state = ReserveState(
            policy_id="test_validation_metrics",
            product_type=ProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        required_metrics = [
            "cte_mean_ratio",
            "std_dev",
            "coefficient_of_variation",
            "cte_gte_mean",
            "convergence_error",
            "num_scenarios",
            "regulatory_standard",
        ]
        for metric in required_metrics:
            self.assertIn(metric, result.validation_metrics)


class TestFixtures(unittest.TestCase):
    """Test loading and validating fixtures."""

    def _load_fixture(self, fixture_name: str) -> dict:
        """Load fixture JSON file."""
        fixture_path = (
            Path(__file__).parent.parent
            / "fixtures"
            / "reserve"
            / f"{fixture_name}.json"
        )
        if not fixture_path.exists():
            self.skipTest(f"Fixture {fixture_name} not found")
        with open(fixture_path) as f:
            return json.load(f)

    def test_va_standard_fixture(self) -> None:
        """VA standard fixture should be valid."""
        fixture = self._load_fixture("va_001_standard")
        self.assertEqual(fixture["product_type"], "VA_with_GLWB")
        self.assertGreater(fixture["cte70_reserve"], 0)
        self.assertGreaterEqual(fixture["cte70_reserve"], fixture["mean_reserve"] - 1)

    def test_fia_standard_fixture(self) -> None:
        """FIA standard fixture should be valid."""
        fixture = self._load_fixture("fia_001_standard")
        self.assertEqual(fixture["product_type"], "FIA")
        self.assertGreater(fixture["cte70_reserve"], 0)
        self.assertGreater(fixture["vm22_reserve"], 0)

    def test_rila_standard_fixture(self) -> None:
        """RILA standard fixture should be valid."""
        fixture = self._load_fixture("rila_001_standard")
        self.assertEqual(fixture["product_type"], "RILA")
        self.assertGreater(fixture["cte70_reserve"], 0)

    def test_all_fixtures_have_key_fields(self) -> None:
        """All fixtures should have required fields."""
        fixture_names = [
            "va_001_standard",
            "va_002_highrisk",
            "fia_001_standard",
            "fia_002_young",
            "rila_001_standard",
            "rila_002_large",
        ]

        for fixture_name in fixture_names:
            fixture = self._load_fixture(fixture_name)
            required_fields = [
                "policy_id",
                "product_type",
                "cte70_reserve",
                "mean_reserve",
                "vm21_reserve",
                "vm22_reserve",
            ]
            for field in required_fields:
                self.assertIn(field, fixture, f"Missing {field} in {fixture_name}")


if __name__ == "__main__":
    unittest.main()
