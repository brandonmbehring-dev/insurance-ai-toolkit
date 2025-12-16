"""Agents for HedgingCrew.

Each agent is a node in the LangGraph workflow:
- greeks_calculation_agent: Compute Delta, Gamma, Vega, Theta
- volatility_calibration_agent: Build vol surface with SABR model
- hedge_recommendation_agent: Suggest optimal hedge positions
- validation_agent: Verify Greeks accuracy and cost-benefit

All agents are implemented in the workflow module.
Implementation Status: Complete with full Greeks calculations.
"""

__all__ = []
