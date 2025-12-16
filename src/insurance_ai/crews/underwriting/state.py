"""State definitions for UnderwritingCrew.

Defines the data structures that flow through the underwriting workflow:
- ProductType: VA, FIA, RILA
- RiskClass: Approval decision (APPROVED, APPROVED_WITH_FLATEX, PENDING_REVIEW, DECLINED)
- UnderwritingState: Complete state during workflow execution
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProductType(str, Enum):
    """Supported annuity products."""

    VA_GLWB = "VA_with_GLWB"
    FIA = "FIA"
    RILA = "RILA"


class RiskClass(str, Enum):
    """Mortality risk classifications and approval decisions."""

    APPROVED = "APPROVED"
    APPROVED_WITH_FLATEX = "APPROVED_WITH_FLATEX"
    PENDING_REVIEW = "PENDING_REVIEW"
    DECLINED = "DECLINED"


@dataclass
class UnderwritingState:
    """
    State that flows through UnderwritingCrew agents.

    Organized in stages:
    - Input: applicant_id, product_type, age, gender
    - Extraction: extracted_health_metrics, extraction_confidence
    - Validation: extraction_warnings, schema_valid
    - Classification: vbt_mortality_class, mortality_adjustment_percent
    - Approval: risk_class, confidence_score, approval_flags
    - Output: underwriting_notes, processing_method, validation_metrics
    """

    # ===== Input Stage =====
    applicant_id: str
    product_type: ProductType
    age: int
    gender: str  # "M" or "F"

    # ===== Extraction Stage =====
    extracted_health_metrics: Dict[str, Any] = field(default_factory=dict)
    extraction_confidence: float = 0.0
    extraction_warnings: List[str] = field(default_factory=list)

    # ===== Validation Stage =====
    all_fields_extracted: bool = False
    schema_valid: bool = False

    # ===== Classification Stage =====
    mortality_table_age: int = 0
    mortality_adjustment_percent: float = 0.0
    vbt_mortality_class: str = ""

    # ===== Approval Stage =====
    risk_class: RiskClass = RiskClass.PENDING_REVIEW
    approval_flags: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0

    # ===== Output Stage =====
    underwriting_notes: str = ""
    processing_method: str = "OFFLINE_FIXTURE"  # "OFFLINE_FIXTURE" or "CLAUDE_VISION"

    # ===== Validation Metrics =====
    validation_metrics: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON output."""
        return {
            "applicant_id": self.applicant_id,
            "product_type": self.product_type.value,
            "age": self.age,
            "gender": self.gender,
            "extracted_health_metrics": self.extracted_health_metrics,
            "extraction_confidence": self.extraction_confidence,
            "extraction_warnings": self.extraction_warnings,
            "vbt_mortality_class": self.vbt_mortality_class,
            "mortality_adjustment_percent": self.mortality_adjustment_percent,
            "risk_class": self.risk_class.value,
            "confidence_score": self.confidence_score,
            "underwriting_notes": self.underwriting_notes,
            "processing_method": self.processing_method,
            "approval_flags": self.approval_flags,
            "validation_metrics": self.validation_metrics,
        }
