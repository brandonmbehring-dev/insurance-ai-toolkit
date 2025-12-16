"""State definitions for HedgingCrew.

Defines the data structures for dynamic hedging decisions:
- Portfolio state (equity holdings, liability durations)
- Greeks (Delta, Gamma, Vega, Theta)
- Volatility surface (ATM, smile, term structure)
- Hedge recommendations (position changes, costs)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class InstrumentType(str, Enum):
    """Types of hedging instruments."""

    EQUITY_CALL = "equity_call"  # Protective calls on downside
    EQUITY_PUT = "equity_put"  # Puts for downside protection
    INDEX_SWAP = "index_swap"  # Equity index swaps
    VOLATILITY_SWAP = "volatility_swap"  # Variance/vol swaps
    COLLAR = "collar"  # Call spread collar


class HedgeAction(str, Enum):
    """Recommended hedge actions."""

    BUY_CALLS = "buy_calls"  # Buy upside calls
    BUY_PUTS = "buy_puts"  # Buy downside protection
    SELL_CALLS = "sell_calls"  # Reduce hedge costs
    UNWIND = "unwind"  # Close hedge position
    HOLD = "hold"  # Maintain current position
    REBALANCE = "rebalance"  # Adjust notional


@dataclass
class GreeksCalculation:
    """Greeks for a single option/liability."""

    delta: float = 0.0  # Change in value per 1% equity move
    gamma: float = 0.0  # Change in delta per 1% equity move
    vega: float = 0.0  # Change in value per 1% volatility change
    theta: float = 0.0  # Time decay per day
    rho: float = 0.0  # Interest rate sensitivity

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "vega": self.vega,
            "theta": self.theta,
            "rho": self.rho,
        }


@dataclass
class HedgeRecommendation:
    """A single hedge recommendation."""

    action: HedgeAction
    instrument: InstrumentType
    strike_price: float
    notional_amount: float  # $ amount to hedge
    estimated_cost: float  # Premium to pay
    effective_delta: float  # Portfolio delta after hedge
    rationale: str  # Why this hedge


@dataclass
class HedgingState:
    """
    State that flows through HedgingCrew agents.

    Organized in stages:
    - Input: Policy portfolio (liabilities, equity holdings)
    - Greeks Calculation: Compute delta, vega, etc.
    - Volatility Calibration: SABR model for vol surface
    - Hedge Recommendation: Suggest positions
    - Validation: Check delta reduction, cost-benefit
    - Output: Hedge execution plan
    """

    # ===== Input Stage =====
    policy_id: str
    portfolio_name: str
    valuation_date: str  # ISO format: YYYY-MM-DD
    underlying_spot_price: float  # S&P 500 or other index
    liability_value: float  # GLWB/GMWB obligation
    time_to_maturity_years: float  # Years until maturity
    risk_free_rate: float = 0.03  # 3% base rate

    # ===== Greeks Calculation Stage =====
    liability_greeks: GreeksCalculation = field(default_factory=GreeksCalculation)
    hedge_greeks: GreeksCalculation = field(default_factory=GreeksCalculation)
    portfolio_delta: float = 0.0  # Net delta exposure
    portfolio_vega: float = 0.0  # Net vega exposure (vol sensitivity)

    # ===== Volatility Calibration Stage =====
    implied_volatility_atm: float = 0.18  # At-the-money vol (18%)
    volatility_surface: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )  # {term: {strike: vol}}
    sabr_parameters: Dict[str, float] = field(
        default_factory=dict
    )  # {alpha, beta, rho, nu} from calibration
    volatility_skew: float = 0.0  # Smile slope (higher for OTM puts)

    # ===== Hedge Recommendation Stage =====
    hedge_recommendations: List[HedgeRecommendation] = field(default_factory=list)
    recommended_action: HedgeAction = HedgeAction.HOLD
    hedge_cost_bps: float = 0.0  # Cost in basis points of liability

    # ===== Validation Stage =====
    portfolio_delta_after_hedge: float = 0.0  # Delta post-hedge
    delta_reduction_percent: float = 0.0  # % delta reduction achieved
    cost_benefit_ratio: float = 0.0  # Benefit / Cost
    hedge_effective: bool = False  # Cost < Benefit?

    # ===== Output Stage =====
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    hedge_efficiency_score: float = 0.0  # 0-100, higher = better
    processing_method: str = "OFFLINE_FIXTURE"  # "OFFLINE_FIXTURE" or "MARKET_DATA"

    # ===== Validation Metrics =====
    validation_metrics: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON output."""
        return {
            "policy_id": self.policy_id,
            "portfolio_name": self.portfolio_name,
            "valuation_date": self.valuation_date,
            "underlying_spot_price": self.underlying_spot_price,
            "liability_value": self.liability_value,
            "time_to_maturity_years": self.time_to_maturity_years,
            "liability_greeks": self.liability_greeks.to_dict(),
            "portfolio_delta": self.portfolio_delta,
            "portfolio_vega": self.portfolio_vega,
            "implied_volatility_atm": self.implied_volatility_atm,
            "hedge_recommendations": [
                {
                    "action": r.action.value,
                    "instrument": r.instrument.value,
                    "strike_price": r.strike_price,
                    "notional_amount": r.notional_amount,
                    "estimated_cost": r.estimated_cost,
                    "effective_delta": r.effective_delta,
                    "rationale": r.rationale,
                }
                for r in self.hedge_recommendations
            ],
            "recommended_action": self.recommended_action.value,
            "hedge_cost_bps": self.hedge_cost_bps,
            "portfolio_delta_after_hedge": self.portfolio_delta_after_hedge,
            "delta_reduction_percent": self.delta_reduction_percent,
            "cost_benefit_ratio": self.cost_benefit_ratio,
            "hedge_effective": self.hedge_effective,
            "hedge_efficiency_score": self.hedge_efficiency_score,
            "processing_method": self.processing_method,
            "validation_metrics": self.validation_metrics,
        }
