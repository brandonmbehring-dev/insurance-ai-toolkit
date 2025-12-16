"""BehaviorCrew: Policyholder behavior modeling and lapse analysis.

Coordinates agents for:
1. Dynamic lapse rate calculations (surrender behavior under economic conditions)
2. Optimal withdrawal strategy determination (GLWB/GMWB)
3. Monte Carlo path simulation with behavioral assumptions
4. Rate/volatility sensitivity analysis
"""

from .state import BehaviorState, WithdrawalStrategy, LapseAssumption, WithdrawalPath
from .workflow import (
    build_behavior_crew,
    run_behavior_crew,
    lapse_modeling_agent,
    withdrawal_planning_agent,
    path_simulation_agent,
    sensitivity_analysis_agent,
)

__all__ = [
    "BehaviorState",
    "WithdrawalStrategy",
    "LapseAssumption",
    "WithdrawalPath",
    "build_behavior_crew",
    "run_behavior_crew",
    "lapse_modeling_agent",
    "withdrawal_planning_agent",
    "path_simulation_agent",
    "sensitivity_analysis_agent",
]
