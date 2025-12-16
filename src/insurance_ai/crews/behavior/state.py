"""State definitions for BehaviorCrew.

Defines data structures for policyholder behavior modeling:
- Dynamic lapse rates (surrender rates under different economic conditions)
- Withdrawal behavior (optimal withdrawal strategies for GLWB/GMWB)
- Monte Carlo path simulation
- Rate sensitivity analysis
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class WithdrawalStrategy(str, Enum):
    """Types of withdrawal strategies."""

    CONSERVATIVE = "conservative"  # Min withdrawal to preserve base
    AGGRESSIVE = "aggressive"  # Max withdrawal (exhaust early)
    OPTIMAL = "optimal"  # Balanced for longevity + returns
    STATIC = "static"  # Fixed withdrawal rate


@dataclass
class LapseAssumption:
    """Dynamic lapse rate assumptions."""

    base_lapse_rate: float = 0.06  # 6% at-the-money
    moneyness_elasticity: float = 0.05  # Sensitivity to moneyness
    rate_elasticity: float = 0.02  # Sensitivity to interest rates
    volatility_elasticity: float = 0.01  # Sensitivity to market vol


@dataclass
class WithdrawalPath:
    """Withdrawal path for a single scenario."""

    scenario_id: str
    annual_withdrawals: List[float] = field(default_factory=list)  # By year
    total_withdrawn: float = 0.0
    account_value_at_surrender: float = 0.0  # If surrendered early
    surrender_year: Optional[int] = None  # Year of surrender (if any)
    strategy_used: WithdrawalStrategy = WithdrawalStrategy.OPTIMAL


@dataclass
class BehaviorState:
    """
    State that flows through BehaviorCrew agents.

    Organized in stages:
    - Input: Policy & economic data (account value, rates, vol, moneyness)
    - Lapse Modeling: Calculate dynamic surrender rates
    - Withdrawal Planning: Determine optimal withdrawal strategy
    - Path Simulation: Monte Carlo paths with lapse/withdrawal behavior
    - Sensitivity Analysis: Impact of rate shocks on behavior
    - Output: Behavioral impact on reserves
    """

    # ===== Input Stage =====
    policy_id: str
    portfolio_name: str
    valuation_date: str  # ISO format: YYYY-MM-DD
    account_value: float  # Current AV
    benefit_base: float  # GLWB/GMWB base
    annual_withdrawal_amount: float  # $ withdrawal per year
    time_to_maturity_years: float
    risk_free_rate: float = 0.03
    market_volatility: float = 0.18

    # ===== Lapse Modeling Stage =====
    base_lapse_rate: float = 0.06  # Base 6%
    moneyness: float = 0.0  # Account value / Benefit base ratio
    dynamic_lapse_rate: float = 0.0  # Adjusted for rates/vol
    lapse_rate_by_year: List[float] = field(default_factory=list)

    # ===== Withdrawal Planning Stage =====
    recommended_strategy: WithdrawalStrategy = WithdrawalStrategy.OPTIMAL
    optimal_withdrawal_rate: float = 0.0  # % of account value
    withdrawal_paths: List[WithdrawalPath] = field(default_factory=list)

    # ===== Path Simulation Stage =====
    num_scenarios: int = 1000
    scenario_seed: int = 42
    simulated_account_values: List[List[float]] = field(default_factory=list)  # [scenario][year]
    simulated_surrenders: List[int] = field(default_factory=list)  # [scenario] → surrender_year
    average_account_value_at_maturity: float = 0.0
    probability_in_force_at_maturity: float = 1.0  # % not surrendered

    # ===== Sensitivity Analysis Stage =====
    lapse_rate_if_rates_up: float = 0.0  # Lapse if +100bps
    lapse_rate_if_rates_down: float = 0.0  # Lapse if -100bps
    lapse_rate_if_vol_up: float = 0.0  # Lapse if vol +25%
    reserve_impact_from_behavior: float = 0.0  # $ impact on reserve

    # ===== Output Stage =====
    behavioral_adjustment_to_reserve: float = 0.0  # % adjustment to base reserve
    validation_metrics: Dict[str, str] = field(default_factory=dict)
    processing_method: str = "OFFLINE_FIXTURE"

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON output."""
        return {
            "policy_id": self.policy_id,
            "portfolio_name": self.portfolio_name,
            "valuation_date": self.valuation_date,
            "account_value": self.account_value,
            "benefit_base": self.benefit_base,
            "annual_withdrawal_amount": self.annual_withdrawal_amount,
            "time_to_maturity_years": self.time_to_maturity_years,
            "moneyness": self.moneyness,
            "base_lapse_rate": self.base_lapse_rate,
            "dynamic_lapse_rate": self.dynamic_lapse_rate,
            "recommended_strategy": self.recommended_strategy.value,
            "optimal_withdrawal_rate": self.optimal_withdrawal_rate,
            "num_scenarios": self.num_scenarios,
            "average_account_value_at_maturity": self.average_account_value_at_maturity,
            "probability_in_force_at_maturity": self.probability_in_force_at_maturity,
            "lapse_rate_if_rates_up": self.lapse_rate_if_rates_up,
            "lapse_rate_if_rates_down": self.lapse_rate_if_rates_down,
            "lapse_rate_if_vol_up": self.lapse_rate_if_vol_up,
            "reserve_impact_from_behavior": self.reserve_impact_from_behavior,
            "behavioral_adjustment_to_reserve": self.behavioral_adjustment_to_reserve,
            "processing_method": self.processing_method,
            "validation_metrics": self.validation_metrics,
        }
