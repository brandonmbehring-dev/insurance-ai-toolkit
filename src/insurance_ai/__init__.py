"""InsuranceAI Toolkit: Annuity Product Lifecycle Automation.

Multi-agent system for automating Variable Annuity (VA), Fixed Index Annuity (FIA),
and Registered Index-Linked Annuity (RILA) workflows with guaranteed living benefits.

Crews:
- UnderwritingCrew: Medical data extraction & risk classification
- ReserveCrew: Regulatory reserve calculations (VM-21/VM-22)
- HedgingCrew: Volatility calibration & hedge recommendations
- BehaviorCrew: Dynamic lapse modeling & path simulation

Offline Mode (Default):
Uses pre-recorded JSON fixtures for deterministic testing without API costs.

Online Mode (Opt-In):
Uses Claude Vision API and market data services (requires API keys).
"""

__version__ = "0.1.0"
__author__ = "Brandon Behring"

from insurance_ai.config import ONLINE_MODE, get_config

__all__ = ["ONLINE_MODE", "get_config"]
