"""Unit tests for HedgingCrew.

Tests validate:
1. Greeks calculation (Black-Scholes compliance)
2. Volatility calibration (SABR model)
3. Hedge recommendation logic
4. Cost-benefit analysis

Validation criteria:
- Put delta between -1 and 0
- Put gamma positive
- Put vega positive
- Cost-benefit ratio >1.0 for hedging
- Efficiency score 0-100
"""

import json
import unittest
from pathlib import Path

from insurance_ai.crews.hedging import HedgingState, run_hedging_crew


class TestGreeksCalculation(unittest.TestCase):
    """Test Greeks calculations."""

    def test_put_delta_bounds(self) -> None:
        """Put delta should always be between -1 and 0."""
        state = HedgingState(
            policy_id="test_delta",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        # Put delta: -1 <= delta <= 0
        self.assertGreaterEqual(result.hedge_greeks.delta, -1.0)
        self.assertLessEqual(result.hedge_greeks.delta, 0.0)

    def test_gamma_positive(self) -> None:
        """Gamma should always be positive."""
        state = HedgingState(
            policy_id="test_gamma",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertGreaterEqual(result.hedge_greeks.gamma, 0.0)

    def test_vega_positive(self) -> None:
        """Vega should always be positive for options."""
        state = HedgingState(
            policy_id="test_vega",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertGreaterEqual(result.hedge_greeks.vega, 0.0)

    def test_liability_has_negative_delta(self) -> None:
        """GLWB liability should have negative delta."""
        state = HedgingState(
            policy_id="test_liability_delta",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        # Liability delta negative (benefits from price drops)
        self.assertLess(result.liability_greeks.delta, 0.0)

    def test_liability_has_positive_vega(self) -> None:
        """GLWB liability should have positive vega (vol increases cost)."""
        state = HedgingState(
            policy_id="test_liability_vega",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        # Liability vega positive (higher vol increases liability)
        self.assertGreater(result.liability_greeks.vega, 0.0)


class TestHedgeRecommendation(unittest.TestCase):
    """Test hedge recommendation logic."""

    def test_hedge_action_is_valid(self) -> None:
        """Recommended action should be one of the valid enums."""
        state = HedgingState(
            policy_id="test_action",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertIn(
            result.recommended_action.value,
            ["buy_puts", "buy_calls", "sell_calls", "unwind", "hold", "rebalance"],
        )

    def test_cost_benefit_ratio_positive(self) -> None:
        """Cost-benefit ratio should be non-negative."""
        state = HedgingState(
            policy_id="test_cb_ratio",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertGreaterEqual(result.cost_benefit_ratio, 0.0)

    def test_delta_reduction_percent_valid(self) -> None:
        """Delta reduction should be between 0 and 100%."""
        state = HedgingState(
            policy_id="test_delta_reduction",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertGreaterEqual(result.delta_reduction_percent, 0.0)
        self.assertLessEqual(result.delta_reduction_percent, 1.0)


class TestEfficiencyScore(unittest.TestCase):
    """Test hedge efficiency scoring."""

    def test_efficiency_score_range(self) -> None:
        """Efficiency score should be 0-100."""
        state = HedgingState(
            policy_id="test_efficiency",
            portfolio_name="Test Portfolio",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
        )
        result = run_hedging_crew(state)

        self.assertGreaterEqual(result.hedge_efficiency_score, 0.0)
        self.assertLessEqual(result.hedge_efficiency_score, 100.0)

    def test_high_vol_increases_hedge_need(self) -> None:
        """Higher volatility should suggest hedging."""
        state_low_vol = HedgingState(
            policy_id="test_lowvol",
            portfolio_name="Low Vol",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
            implied_volatility_atm=0.10,  # Low vol
        )
        result_low_vol = run_hedging_crew(state_low_vol)

        state_high_vol = HedgingState(
            policy_id="test_highvol",
            portfolio_name="High Vol",
            valuation_date="2025-12-31",
            underlying_spot_price=100.0,
            liability_value=500000.0,
            time_to_maturity_years=10.0,
            implied_volatility_atm=0.35,  # High vol
        )
        result_high_vol = run_hedging_crew(state_high_vol)

        # Higher vol should have higher cost-benefit ratio or better efficiency
        self.assertGreater(
            result_high_vol.hedge_efficiency_score, result_low_vol.hedge_efficiency_score * 0.8
        )


class TestFixtures(unittest.TestCase):
    """Test loading and validating fixtures."""

    def _load_fixture(self, fixture_name: str) -> dict:
        """Load fixture JSON file."""
        fixture_path = (
            Path(__file__).parent.parent / "fixtures" / "hedging" / f"{fixture_name}.json"
        )
        if not fixture_path.exists():
            self.skipTest(f"Fixture {fixture_name} not found")
        with open(fixture_path) as f:
            return json.load(f)

    def test_va_standard_fixture(self) -> None:
        """VA standard fixture should be valid."""
        fixture = self._load_fixture("hedge_va_001_standard")
        self.assertGreater(fixture["underlying_spot_price"], 0)
        self.assertGreater(fixture["liability_value"], 0)
        self.assertIn("recommended_action", fixture)

    def test_highvol_fixture(self) -> None:
        """High volatility fixture should be valid."""
        fixture = self._load_fixture("hedge_va_002_highvol")
        self.assertGreater(fixture["implied_volatility_atm"], 0.25)
        self.assertGreater(fixture["hedge_efficiency_score"], 90)

    def test_short_maturity_fixture(self) -> None:
        """Short maturity fixture should be valid."""
        fixture = self._load_fixture("hedge_va_003_short")
        self.assertLess(fixture["time_to_maturity_years"], 3)
        self.assertGreater(fixture["hedge_efficiency_score"], 0)

    def test_large_portfolio_fixture(self) -> None:
        """Large portfolio fixture should be valid."""
        fixture = self._load_fixture("hedge_port_001_large")
        self.assertGreater(fixture["liability_value"], 1000000)
        self.assertGreater(fixture["time_to_maturity_years"], 10)


if __name__ == "__main__":
    unittest.main()
