"""State definitions for ReserveCrew.

Defines the data structures that flow through the reserve calculation workflow:
- ProductType: VA, FIA, RILA
- CalculationMethod: Monte Carlo, Deterministic, Lattice
- ReserveState: Complete state during workflow execution
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProductType(str, Enum):
    """Supported annuity products."""

    VA_GLWB = "VA_with_GLWB"
    VA_GMWB = "VA_with_GMWB"
    FIA = "FIA"
    RILA = "RILA"


class CalculationMethod(str, Enum):
    """Regulatory reserve calculation methods."""

    MONTE_CARLO = "monte_carlo"
    DETERMINISTIC = "deterministic"
    LATTICE = "lattice"


@dataclass
class ReserveState:
    """
    State that flows through ReserveCrew agents.

    Organized in stages:
    - Input: Policy metadata, valuation parameters
    - Scenario Generation: Economic scenarios (equity paths, rate paths)
    - Cash Flow Projection: Projected liabilities across scenarios
    - CTE Calculation: Percentiles, mean, risk margin
    - Sensitivity Analysis: Shock results and monotonicity checks
    - Convergence Validation: Accuracy assessment and compliance
    - Output: Regulatory reserve (VM-21/VM-22)
    """

    # ===== Input Stage =====
    policy_id: str
    product_type: ProductType
    issue_age: int
    policy_month: int
    account_value: float  # AV for VA; premium for FIA
    benefit_base: float  # GLWB/GMWB benefit base
    valuation_date: str  # ISO format: YYYY-MM-DD
    calculation_method: CalculationMethod = CalculationMethod.MONTE_CARLO

    # ===== Scenario Generation Stage =====
    economic_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    num_scenarios: int = 1000
    num_years: int = 30
    scenario_seed: int = 42
    ag43_scenarios: bool = True  # Use NAIC 43 ESG scenarios

    # ===== Cash Flow Projection Stage =====
    projected_cash_flows: Dict[str, List[float]] = field(default_factory=dict)
    mortality_assumptions: Dict[str, Any] = field(default_factory=dict)
    lapse_assumptions: Dict[str, Any] = field(default_factory=dict)
    expense_assumptions: Dict[str, Any] = field(default_factory=dict)
    expected_liability_pv: float = 0.0

    # ===== CTE Calculation Stage =====
    reserve_paths: List[float] = field(default_factory=list)
    mean_reserve: float = 0.0
    median_reserve: float = 0.0
    percentile_reserves: Dict[int, float] = field(default_factory=dict)
    cte70_reserve: float = 0.0
    cte90_reserve: float = 0.0
    risk_margin: float = 0.0

    # ===== Sensitivity Analysis Stage =====
    sensitivity_results: Dict[str, Dict[str, float]] = field(default_factory=dict)
    sensitivity_monotonicity: Dict[str, bool] = field(default_factory=dict)

    # ===== Convergence Validation Stage =====
    convergence_error_percent: float = 0.0
    converged: bool = False
    required_scenario_count: int = 1000

    # ===== Output Stage =====
    vm21_reserve: float = 0.0  # Final regulatory reserve for VA
    vm22_reserve: float = 0.0  # Final regulatory reserve for FIA/RILA
    regulatory_reporting: Dict[str, Any] = field(default_factory=dict)
    processing_method: str = "OFFLINE_FIXTURE"

    # ===== Validation Metrics =====
    validation_metrics: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON output."""
        return {
            "policy_id": self.policy_id,
            "product_type": self.product_type.value,
            "issue_age": self.issue_age,
            "policy_month": self.policy_month,
            "account_value": self.account_value,
            "benefit_base": self.benefit_base,
            "valuation_date": self.valuation_date,
            "num_scenarios": self.num_scenarios,
            "expected_liability_pv": self.expected_liability_pv,
            "mean_reserve": self.mean_reserve,
            "percentile_reserves": self.percentile_reserves,
            "cte70_reserve": self.cte70_reserve,
            "cte90_reserve": self.cte90_reserve,
            "risk_margin": self.risk_margin,
            "vm21_reserve": self.vm21_reserve,
            "vm22_reserve": self.vm22_reserve,
            "convergence_error_percent": self.convergence_error_percent,
            "converged": self.converged,
            "sensitivity_results": self.sensitivity_results,
            "sensitivity_monotonicity": self.sensitivity_monotonicity,
            "processing_method": self.processing_method,
            "validation_metrics": self.validation_metrics,
            "regulatory_reporting": self.regulatory_reporting,
        }
