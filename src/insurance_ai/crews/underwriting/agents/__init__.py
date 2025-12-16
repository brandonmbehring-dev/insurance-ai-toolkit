"""Agents for UnderwritingCrew.

Each agent is a node in the LangGraph workflow:
- extraction_agent: Extract health metrics from PDF or fixture
- validation_agent: Validate consistency of extracted metrics
- mortality_agent: Classify mortality risk using SOA 2012 IAM
- approval_agent: Apply product-specific approval rules
"""

from .extraction import extraction_agent
from .validation import validation_agent
from .mortality import mortality_agent
from .approval import approval_agent

__all__ = [
    "extraction_agent",
    "validation_agent",
    "mortality_agent",
    "approval_agent",
]
