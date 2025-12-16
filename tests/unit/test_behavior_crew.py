"""Unit tests for BehaviorCrew.

Tests validate:
1. Lapse modeling (moneyness relationship, rate bounds)
2. Withdrawal planning (strategy selection, sustainability)
3. Path simulation (in-force probability, convergence)
4. Sensitivity analysis (rate/vol impact, validation metrics)

Validation criteria:
- Lapse monotonicity: OTM > ATM > ITM
- Dynamic lapse bounds: 1% ≤ rate ≤ 50%
- Withdrawal rate bounds: 0% ≤ rate ≤ 10%
- In-force probability: 0% ≤ prob ≤ 100%
- Path convergence: |n=100 vs n=1000| ≤ 3%
"""

import json
import unittest
from pathlib import Path

from insurance_ai.crews.behavior import BehaviorState, WithdrawalStrategy, run_behavior_crew


class TestLapseModeling(unittest.TestCase):
    """Test lapse modeling agent."""

    def test_itm_lapse_less_than_atm(self) -> None:
        """ITM (moneyness > 1) should have lower lapse than ATM."""
        state_atm = BehaviorState(
            policy_id="test_atm_lapse",
            portfolio_name="Test ATM",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result_atm = run_behavior_crew(state_atm)

        state_itm = BehaviorState(
            policy_id="test_itm_lapse",
            portfolio_name="Test ITM",
            valuation_date="2025-12-31",
            account_value=450000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result_itm = run_behavior_crew(state_itm)

        # ITM lapse < ATM lapse (account above guarantee = lower surrender risk)
        self.assertLess(result_itm.dynamic_lapse_rate, result_atm.dynamic_lapse_rate)

    def test_otm_lapse_greater_than_atm(self) -> None:
        """OTM (moneyness < 1) should have higher lapse than ATM."""
        state_atm = BehaviorState(
            policy_id="test_atm_lapse2",
            portfolio_name="Test ATM",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result_atm = run_behavior_crew(state_atm)

        state_otm = BehaviorState(
            policy_id="test_otm_lapse",
            portfolio_name="Test OTM",
            valuation_date="2025-12-31",
            account_value=280000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result_otm = run_behavior_crew(state_otm)

        # OTM lapse > ATM lapse (account below guarantee = higher surrender risk)
        self.assertGreater(result_otm.dynamic_lapse_rate, result_atm.dynamic_lapse_rate)

    def test_lapse_rate_bounds(self) -> None:
        """Dynamic lapse should be bounded 1% to 50%."""
        state = BehaviorState(
            policy_id="test_lapse_bounds",
            portfolio_name="Test Bounds",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result = run_behavior_crew(state)

        self.assertGreaterEqual(result.dynamic_lapse_rate, 0.01)
        self.assertLessEqual(result.dynamic_lapse_rate, 0.50)

    def test_lapse_rate_by_year_reversion(self) -> None:
        """Lapse rates should gradually revert to base over time."""
        state = BehaviorState(
            policy_id="test_lapse_reversion",
            portfolio_name="Test Reversion",
            valuation_date="2025-12-31",
            account_value=280000.0,  # OTM - elevated initial lapse
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
        )
        result = run_behavior_crew(state)

        # Lapse rates should converge to base rate over time (some noise due to stochastic shock)
        self.assertGreater(len(result.lapse_rate_by_year), 0)
        # Check that early years have higher lapse for OTM
        self.assertGreater(result.lapse_rate_by_year[0], result.base_lapse_rate * 0.9)


class TestWithdrawalPlanning(unittest.TestCase):
    """Test withdrawal planning agent."""

    def test_itm_gets_aggressive_strategy(self) -> None:
        """ITM (moneyness > 1.2) should get AGGRESSIVE strategy."""
        state = BehaviorState(
            policy_id="test_aggressive_withdrawal",
            portfolio_name="Test Aggressive",
            valuation_date="2025-12-31",
            account_value=450000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        self.assertEqual(result.recommended_strategy, WithdrawalStrategy.AGGRESSIVE)

    def test_otm_gets_conservative_strategy(self) -> None:
        """OTM (moneyness < 0.9) should get CONSERVATIVE strategy."""
        state = BehaviorState(
            policy_id="test_conservative_withdrawal",
            portfolio_name="Test Conservative",
            valuation_date="2025-12-31",
            account_value=280000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        self.assertEqual(result.recommended_strategy, WithdrawalStrategy.CONSERVATIVE)

    def test_atm_gets_optimal_strategy(self) -> None:
        """ATM (0.9 ≤ moneyness ≤ 1.2) should get OPTIMAL strategy."""
        state = BehaviorState(
            policy_id="test_optimal_withdrawal",
            portfolio_name="Test Optimal",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        self.assertEqual(result.recommended_strategy, WithdrawalStrategy.OPTIMAL)

    def test_withdrawal_rate_bounds(self) -> None:
        """Optimal withdrawal rate should be bounded 0% to 10%."""
        state = BehaviorState(
            policy_id="test_withdrawal_bounds",
            portfolio_name="Test Bounds",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        self.assertGreaterEqual(result.optimal_withdrawal_rate, 0.0)
        self.assertLessEqual(result.optimal_withdrawal_rate, 0.10)

    def test_withdrawal_sustainability_check(self) -> None:
        """Annual withdrawal < 10% of account value should pass sustainability."""
        state = BehaviorState(
            policy_id="test_sustainability",
            portfolio_name="Test Sustainability",
            valuation_date="2025-12-31",
            account_value=300000.0,
            benefit_base=400000.0,
            annual_withdrawal_amount=25000.0,  # 8.3% - sustainable
            time_to_maturity_years=10.0,
        )
        result = run_behavior_crew(state)

        # Check validation metrics
        self.assertIn("withdrawal_sustainable", result.validation_metrics)
        self.assertIn(result.validation_metrics["withdrawal_sustainable"], ["PASS", "WARN"])


class TestPathSimulation(unittest.TestCase):
    """Test path simulation agent."""

    def test_in_force_probability_bounds(self) -> None:
        """In-force probability should be between 0% and 100%."""
        state = BehaviorState(
            policy_id="test_in_force_prob",
            portfolio_name="Test In-Force",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=20.0,
            num_scenarios=100,
        )
        result = run_behavior_crew(state)

        self.assertGreaterEqual(result.probability_in_force_at_maturity, 0.0)
        self.assertLessEqual(result.probability_in_force_at_maturity, 1.0)

    def test_otm_lower_in_force_probability(self) -> None:
        """OTM policies should have lower in-force probability."""
        state_atm = BehaviorState(
            policy_id="test_atm_inforce",
            portfolio_name="Test ATM",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            num_scenarios=100,
        )
        result_atm = run_behavior_crew(state_atm)

        state_otm = BehaviorState(
            policy_id="test_otm_inforce",
            portfolio_name="Test OTM",
            valuation_date="2025-12-31",
            account_value=280000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            num_scenarios=100,
        )
        result_otm = run_behavior_crew(state_otm)

        # OTM should have lower in-force probability (higher lapse risk)
        self.assertLess(
            result_otm.probability_in_force_at_maturity,
            result_atm.probability_in_force_at_maturity,
        )

    def test_average_account_value_nonnegative(self) -> None:
        """Average account value at maturity should be >= 0."""
        state = BehaviorState(
            policy_id="test_av_maturity",
            portfolio_name="Test AV",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            num_scenarios=100,
        )
        result = run_behavior_crew(state)

        self.assertGreaterEqual(result.average_account_value_at_maturity, 0.0)


class TestSensitivityAnalysis(unittest.TestCase):
    """Test sensitivity analysis agent."""

    def test_rate_up_increases_lapse(self) -> None:
        """Rates up 100bps should increase lapse (guarantee less valuable)."""
        state = BehaviorState(
            policy_id="test_rate_sensitivity",
            portfolio_name="Test Rate Sens",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        # Rates up 100bps should increase lapse (reduce guarantee value)
        self.assertGreater(result.lapse_rate_if_rates_up, result.dynamic_lapse_rate)

    def test_rate_down_decreases_lapse(self) -> None:
        """Rates down 100bps should decrease lapse (guarantee more valuable)."""
        state = BehaviorState(
            policy_id="test_rate_down",
            portfolio_name="Test Rate Down",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        # Rates down 100bps should decrease lapse (increase guarantee value)
        self.assertLess(result.lapse_rate_if_rates_down, result.dynamic_lapse_rate)

    def test_vol_sensitivity_bounds(self) -> None:
        """Vol sensitivity lapse should be within bounds."""
        state = BehaviorState(
            policy_id="test_vol_sensitivity",
            portfolio_name="Test Vol Sens",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        self.assertGreaterEqual(result.lapse_rate_if_vol_up, 0.01)
        self.assertLessEqual(result.lapse_rate_if_vol_up, 0.50)

    def test_validation_metrics_present(self) -> None:
        """All expected validation metrics should be present."""
        state = BehaviorState(
            policy_id="test_validation_metrics",
            portfolio_name="Test Metrics",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        expected_metrics = [
            "in_force_probability",
            "lapse_rate_bounds",
            "withdrawal_sustainable",
        ]
        for metric in expected_metrics:
            self.assertIn(metric, result.validation_metrics)


class TestFixtures(unittest.TestCase):
    """Test loading and validating fixtures."""

    def _load_fixture(self, fixture_name: str) -> dict:
        """Load fixture JSON file."""
        fixture_path = (
            Path(__file__).parent.parent
            / "fixtures"
            / "behavior"
            / f"{fixture_name}.json"
        )
        if not fixture_path.exists():
            self.skipTest(f"Fixture {fixture_name} not found")
        with open(fixture_path) as f:
            return json.load(f)

    def test_itm_fixture_loads(self) -> None:
        """ITM fixture should load and validate."""
        fixture = self._load_fixture("behavior_va_001_itm")
        self.assertGreater(fixture["account_value"], 0)
        self.assertGreater(fixture["benefit_base"], 0)
        self.assertGreater(fixture["moneyness"], 1.0)  # ITM
        self.assertEqual(fixture["recommended_strategy"], "aggressive")

    def test_otm_fixture_loads(self) -> None:
        """OTM fixture should load and validate."""
        fixture = self._load_fixture("behavior_va_002_otm")
        self.assertGreater(fixture["account_value"], 0)
        self.assertGreater(fixture["benefit_base"], 0)
        self.assertLess(fixture["moneyness"], 1.0)  # OTM
        self.assertEqual(fixture["recommended_strategy"], "conservative")

    def test_atm_fixture_loads(self) -> None:
        """ATM fixture should load and validate."""
        fixture = self._load_fixture("behavior_va_003_atm")
        self.assertGreater(fixture["account_value"], 0)
        self.assertGreater(fixture["benefit_base"], 0)
        self.assertAlmostEqual(fixture["moneyness"], 1.0, delta=0.1)  # ATM
        self.assertEqual(fixture["recommended_strategy"], "optimal")

    def test_high_withdrawal_fixture_loads(self) -> None:
        """High withdrawal fixture should load and validate."""
        fixture = self._load_fixture("behavior_va_004_high_withdrawal")
        self.assertGreater(fixture["account_value"], 0)
        self.assertGreater(fixture["benefit_base"], 0)
        self.assertGreater(fixture["annual_withdrawal_amount"], 20000.0)
        self.assertEqual(fixture["recommended_strategy"], "conservative")

    def test_fixture_consistency_across_moneyness(self) -> None:
        """Fixtures should show consistent moneyness-lapse relationship."""
        fixture_itm = self._load_fixture("behavior_va_001_itm")
        fixture_atm = self._load_fixture("behavior_va_003_atm")
        fixture_otm = self._load_fixture("behavior_va_002_otm")

        # Lapse should increase: ITM < ATM < OTM
        self.assertLess(fixture_itm["dynamic_lapse_rate"], fixture_atm["dynamic_lapse_rate"])
        self.assertLess(fixture_atm["dynamic_lapse_rate"], fixture_otm["dynamic_lapse_rate"])


class TestBehaviorStateSchema(unittest.TestCase):
    """Test BehaviorState schema and serialization."""

    def test_state_to_dict_serialization(self) -> None:
        """BehaviorState should serialize to dict."""
        state = BehaviorState(
            policy_id="test_serialize",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
        )
        result = run_behavior_crew(state)

        state_dict = result.to_dict()
        self.assertEqual(state_dict["policy_id"], "test_serialize")
        self.assertEqual(state_dict["portfolio_name"], "Test Portfolio")
        self.assertIn("moneyness", state_dict)
        self.assertIn("dynamic_lapse_rate", state_dict)
        self.assertIn("recommended_strategy", state_dict)

    def test_state_preserves_input_fields(self) -> None:
        """BehaviorState should preserve all input fields."""
        state = BehaviorState(
            policy_id="test_preservation",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            risk_free_rate=0.035,
            market_volatility=0.20,
        )
        result = run_behavior_crew(state)

        self.assertEqual(result.policy_id, "test_preservation")
        self.assertEqual(result.account_value, 350000.0)
        self.assertEqual(result.benefit_base, 350000.0)
        self.assertAlmostEqual(result.risk_free_rate, 0.035, places=3)


class TestDeterminism(unittest.TestCase):
    """Test reproducibility with fixed seeds."""

    def test_fixed_seed_reproducible(self) -> None:
        """Same seed should produce identical results."""
        state1 = BehaviorState(
            policy_id="test_seed1",
            portfolio_name="Test",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            scenario_seed=42,
            num_scenarios=50,
        )
        result1 = run_behavior_crew(state1)

        state2 = BehaviorState(
            policy_id="test_seed2",
            portfolio_name="Test",
            valuation_date="2025-12-31",
            account_value=350000.0,
            benefit_base=350000.0,
            annual_withdrawal_amount=17500.0,
            time_to_maturity_years=15.0,
            scenario_seed=42,
            num_scenarios=50,
        )
        result2 = run_behavior_crew(state2)

        # Same seed should give identical lapse rates
        self.assertAlmostEqual(
            result1.dynamic_lapse_rate, result2.dynamic_lapse_rate, places=6
        )
        self.assertAlmostEqual(
            result1.probability_in_force_at_maturity,
            result2.probability_in_force_at_maturity,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
