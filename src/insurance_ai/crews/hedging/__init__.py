"""HedgingCrew: Dynamic hedging for guaranteed withdrawal benefits.

Calculates hedge recommendations for VA/FIA/RILA guarantees:
- Greeks calculation (Delta, Gamma, Vega, Theta)
- Volatility surface calibration (SABR model)
- Hedge recommendation (puts, collars, swaps)
- Cost-benefit analysis and validation

Workflow:
1. Greeks Calculation: Compute liability and hedge Greeks
2. Volatility Calibration: Build vol surface from market data/assumptions
3. Hedge Recommendation: Suggest optimal hedge positions
4. Validation: Check Greeks accuracy, cost-benefit, efficiency

Output: Hedge execution plan with estimated costs and effectiveness
"""

from .workflow import build_hedging_crew, run_hedging_crew
from .state import HedgingState, InstrumentType, HedgeAction

__all__ = [
    "build_hedging_crew",
    "run_hedging_crew",
    "HedgingState",
    "InstrumentType",
    "HedgeAction",
]
