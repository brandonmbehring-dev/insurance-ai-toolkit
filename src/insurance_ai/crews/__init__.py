"""InsuranceAI Toolkit crews - specialized agentic agents for annuity workflows.

Crews:
- UnderwritingCrew: Medical data extraction & risk classification
- ReserveCrew: Regulatory reserve calculations (VM-21/VM-22)
- HedgingCrew: Volatility calibration & Greeks calculation
- BehaviorCrew: Dynamic lapse & policyholder behavior modeling
"""

from .underwriting import build_underwriting_crew

__all__ = ["build_underwriting_crew"]
