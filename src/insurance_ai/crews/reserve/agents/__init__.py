"""Agents for ReserveCrew.

Each agent is a node in the LangGraph workflow:
- scenario_generation_agent: Create 100-10000 economic scenarios
- cash_flow_projection_agent: Project liabilities via mortality/lapse
- cte_calculation_agent: Calculate percentiles and risk margin
- sensitivity_analysis_agent: Shock rates, vol, lapse; validate direction
- convergence_validation_agent: Check accuracy and regulatory compliance

Implementation Status: All agents implemented with full calculations.
"""

from .scenario_generation import scenario_generation_agent
from .cash_flow_projection import cash_flow_projection_agent
from .cte_calculation import cte_calculation_agent
from .sensitivity_analysis import sensitivity_analysis_agent
from .convergence_validation import convergence_validation_agent

__all__ = [
    "scenario_generation_agent",
    "cash_flow_projection_agent",
    "cte_calculation_agent",
    "sensitivity_analysis_agent",
    "convergence_validation_agent",
]
