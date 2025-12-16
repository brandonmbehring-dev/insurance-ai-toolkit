"""ReserveCrew: Regulatory reserve calculations (VM-21/VM-22, CTE70).

Calculates Principle-Based Reserves for Variable Annuities (VM-21), Fixed Annuities (VM-22),
and other products, including CTE70 tail risk calculations.

Workflow:
1. Scenario Generation: Create 100-10000 economic scenarios (equity + rates)
2. Cash Flow Projection: Project liabilities across scenarios with mortality/lapse
3. CTE Calculation: Calculate percentiles, mean reserve, risk margin
4. Sensitivity Analysis: Shock rates/vol/lapse, validate monotonicity
5. Convergence Validation: Check accuracy and regulatory compliance

Output: Regulatory reserve with CTE70, risk margin, sensitivity analysis.
"""

from .workflow import build_reserve_crew, run_reserve_crew
from .state import ReserveState, ProductType, CalculationMethod

__all__ = [
    "build_reserve_crew",
    "run_reserve_crew",
    "ReserveState",
    "ProductType",
    "CalculationMethod",
]
