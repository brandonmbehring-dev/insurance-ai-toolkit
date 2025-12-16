"""UnderwritingCrew: Medical data extraction & risk classification.

Processes medical records to extract health metrics and assign mortality risk classes
for VA, FIA, and RILA products with guaranteed living benefits.

Workflow:
1. Extract health metrics from PDF or structured data
2. Validate extracted metrics for consistency
3. Classify mortality risk using SOA 2012 IAM tables
4. Apply product-specific approval rules (VA/FIA/RILA)

Output: Risk classification with confidence score and approval status.
"""

from .workflow import build_underwriting_crew, run_underwriting_crew
from .state import UnderwritingState, RiskClass, ProductType

__all__ = [
    "build_underwriting_crew",
    "run_underwriting_crew",
    "UnderwritingState",
    "RiskClass",
    "ProductType",
]
