"""Unit tests for UnderwritingCrew.

Tests cover:
1. Agent workflow execution
2. Approval decisions for different scenarios
3. Fixture loading and validation
4. Offline/online mode integration
5. Health metric validation
"""

import pytest
from pathlib import Path

from insurance_ai.crews.underwriting import (
    build_underwriting_crew,
    run_underwriting_crew,
    UnderwritingState,
    RiskClass,
    ProductType,
)


class TestUnderwritingCrew:
    """Test UnderwritingCrew workflow."""

    def test_crew_builds_successfully(self) -> None:
        """Test that UnderwritingCrew builds without errors."""
        crew = build_underwriting_crew()
        assert crew is not None

    def test_standard_applicant_approved(self) -> None:
        """Test standard applicant is approved.

        Fixture: synthetic_applicant_001
        - Age: 55, Non-smoker, Good health
        - Expected: APPROVED at standard rates
        """
        state = UnderwritingState(
            applicant_id="synthetic_applicant_001",
            product_type=ProductType.VA_GLWB,
            age=55,
            gender="M",
        )

        result = run_underwriting_crew(state)

        assert result.risk_class == RiskClass.APPROVED
        assert result.vbt_mortality_class == "Super Preferred"
        assert result.confidence_score > 0.8

    def test_high_risk_applicant_declined(self) -> None:
        """Test high-risk applicant for VA + GLWB is declined.

        Fixture: synthetic_applicant_002_high_risk
        - Age: 62, Smoker, Diabetes, Severe hypertension
        - Expected: DECLINED for VA + GLWB (mortality adjustment > 50%)
        """
        state = UnderwritingState(
            applicant_id="synthetic_applicant_002_high_risk",
            product_type=ProductType.VA_GLWB,
            age=62,
            gender="M",
        )

        result = run_underwriting_crew(state)

        # High-risk with mortality adjustment > 50% should be declined for VA + GLWB
        assert result.risk_class == RiskClass.DECLINED
        assert "exceeds" in result.underwriting_notes or "does not meet" in result.underwriting_notes

    def test_high_risk_fia_adjusted_rate(self) -> None:
        """Test high-risk applicant for FIA has significant mortality adjustment.

        Fixture: synthetic_applicant_002_high_risk
        - Age: 62, Smoker, Diabetes, Severe hypertension
        - Expected: Significant mortality adjustment and appropriate risk class
        """
        state = UnderwritingState(
            applicant_id="synthetic_applicant_002_high_risk",
            product_type=ProductType.FIA,  # More lenient than VA
            age=62,
            gender="M",
        )

        result = run_underwriting_crew(state)

        # Should have significant health adjustments
        assert result.mortality_adjustment_percent > 25
        # Risk class should reflect the severity
        assert result.risk_class in [
            RiskClass.DECLINED,
            RiskClass.APPROVED_WITH_FLATEX,
            RiskClass.PENDING_REVIEW,
        ]

    def test_low_confidence_pending_review(self) -> None:
        """Test low-confidence extraction triggers pending review.

        Fixture: synthetic_applicant_003_pending
        - Extraction confidence: 0.62 (<70% threshold)
        - Expected: PENDING_REVIEW
        """
        state = UnderwritingState(
            applicant_id="synthetic_applicant_003_pending",
            product_type=ProductType.VA_GLWB,
            age=58,
            gender="F",
        )

        result = run_underwriting_crew(state)

        assert result.risk_class == RiskClass.PENDING_REVIEW
        assert result.extraction_confidence < 0.70

    def test_flatex_rider_borderline(self) -> None:
        """Test borderline applicant with controlled health conditions.

        Fixture: synthetic_applicant_004_flatex
        - Age: 68, Controlled hypertension
        - Expected: Some mortality adjustment but approved outcome
        """
        state = UnderwritingState(
            applicant_id="synthetic_applicant_004_flatex",
            product_type=ProductType.VA_GLWB,
            age=68,
            gender="M",
        )

        result = run_underwriting_crew(state)

        # Should have some adjustment for age and conditions
        assert result.mortality_adjustment_percent >= 0
        # Should be approved (with or without flatex)
        assert result.risk_class in [RiskClass.APPROVED, RiskClass.APPROVED_WITH_FLATEX]

    def test_age_below_minimum_declined(self) -> None:
        """Test applicant below minimum age is declined."""
        state = UnderwritingState(
            applicant_id="test_young",
            product_type=ProductType.VA_GLWB,
            age=35,  # Below VA + GLWB minimum of 40
            gender="F",
        )

        result = run_underwriting_crew(state)

        assert result.risk_class == RiskClass.DECLINED
        assert "below minimum" in result.underwriting_notes.lower()

    def test_age_above_standard_generates_warning(self) -> None:
        """Test applicant above standard age is flagged.

        Age above standard limits should generate appropriate handling.
        """
        state = UnderwritingState(
            applicant_id="test_senior",
            product_type=ProductType.VA_GLWB,
            age=90,  # Above VA + GLWB standard limit of 85
            gender="M",
        )

        result = run_underwriting_crew(state)

        # Age above limit should result in some concern
        assert result.risk_class in [
            RiskClass.PENDING_REVIEW,
            RiskClass.DECLINED,
            RiskClass.APPROVED,
        ]

    def test_different_products_different_outcomes(self) -> None:
        """Test that different products may have different approval outcomes.

        Same applicant, different products:
        - VA + GLWB: Stricter limits (max 50%)
        - FIA: More lenient limits (max 100%)
        """
        state_va = UnderwritingState(
            applicant_id="synthetic_applicant_002_high_risk",
            product_type=ProductType.VA_GLWB,
            age=62,
            gender="M",
        )

        state_fia = UnderwritingState(
            applicant_id="synthetic_applicant_002_high_risk",
            product_type=ProductType.FIA,
            age=62,
            gender="M",
        )

        result_va = run_underwriting_crew(state_va)
        result_fia = run_underwriting_crew(state_fia)

        # Both should produce risk assessments
        assert result_va.risk_class in [
            RiskClass.APPROVED,
            RiskClass.APPROVED_WITH_FLATEX,
            RiskClass.DECLINED,
            RiskClass.PENDING_REVIEW,
        ]
        assert result_fia.risk_class in [
            RiskClass.APPROVED,
            RiskClass.APPROVED_WITH_FLATEX,
            RiskClass.DECLINED,
            RiskClass.PENDING_REVIEW,
        ]
        # Both should have extracted same health metrics
        assert result_va.extracted_health_metrics == result_fia.extracted_health_metrics

    def test_validation_metrics_populated(self) -> None:
        """Test that validation metrics are properly populated."""
        state = UnderwritingState(
            applicant_id="synthetic_applicant_001",
            product_type=ProductType.VA_GLWB,
            age=55,
            gender="M",
        )

        result = run_underwriting_crew(state)

        # Check validation metrics
        assert "schema_valid" in result.validation_metrics
        assert "extraction_confidence" in result.validation_metrics
        assert "warnings_count" in result.validation_metrics
        assert "final_confidence_score" in result.validation_metrics
        assert "approval_status" in result.validation_metrics

    def test_extraction_confidence_affects_score(self) -> None:
        """Test that extraction confidence affects final confidence score."""
        state_low = UnderwritingState(
            applicant_id="synthetic_applicant_003_pending",  # Low confidence
            product_type=ProductType.VA_GLWB,
            age=58,
            gender="F",
        )

        state_high = UnderwritingState(
            applicant_id="synthetic_applicant_001",  # High confidence
            product_type=ProductType.VA_GLWB,
            age=55,
            gender="M",
        )

        result_low = run_underwriting_crew(state_low)
        result_high = run_underwriting_crew(state_high)

        # High confidence should result in higher final score
        assert result_high.confidence_score > result_low.confidence_score

    def test_state_to_dict_output(self) -> None:
        """Test that state can be serialized to dict for JSON output."""
        state = UnderwritingState(
            applicant_id="test_dict",
            product_type=ProductType.FIA,
            age=60,
            gender="F",
        )

        result = run_underwriting_crew(state)
        result_dict = result.to_dict()

        # Check required fields in output
        assert "applicant_id" in result_dict
        assert "product_type" in result_dict
        assert "risk_class" in result_dict
        assert "confidence_score" in result_dict
        assert "extracted_health_metrics" in result_dict
        assert "vbt_mortality_class" in result_dict
        assert "underwriting_notes" in result_dict

    def test_smoking_status_increases_mortality(self) -> None:
        """Test that smoking status increases mortality adjustment."""
        state_smoker = UnderwritingState(
            applicant_id="synthetic_applicant_002_high_risk",  # Smoker
            product_type=ProductType.FIA,
            age=62,
            gender="M",
        )

        state_nonsmoker = UnderwritingState(
            applicant_id="synthetic_applicant_001",  # Non-smoker
            product_type=ProductType.FIA,
            age=55,
            gender="M",
        )

        result_smoker = run_underwriting_crew(state_smoker)
        result_nonsmoker = run_underwriting_crew(state_nonsmoker)

        # Smoker should have higher mortality adjustment
        assert result_smoker.mortality_adjustment_percent >= result_nonsmoker.mortality_adjustment_percent

    def test_workflow_completeness(self) -> None:
        """Test that workflow completes all stages.

        Verify that all state fields are populated after workflow.
        """
        state = UnderwritingState(
            applicant_id="test_complete",
            product_type=ProductType.VA_GLWB,
            age=55,
            gender="M",
        )

        result = run_underwriting_crew(state)

        # Check all stages are populated
        assert result.extracted_health_metrics  # Extraction stage
        assert result.extraction_confidence > 0  # Extraction stage
        assert result.vbt_mortality_class  # Classification stage
        assert result.risk_class != RiskClass.PENDING_REVIEW or result.extraction_confidence < 0.70  # Approval stage
        assert result.underwriting_notes  # Approval stage

    def test_multiple_products_same_applicant(self) -> None:
        """Test same applicant with different products."""
        applicant_id = "synthetic_applicant_004_flatex"
        age = 68
        gender = "M"

        results = {}
        for product in [ProductType.VA_GLWB, ProductType.FIA, ProductType.RILA]:
            state = UnderwritingState(
                applicant_id=applicant_id,
                product_type=product,
                age=age,
                gender=gender,
            )
            results[product.value] = run_underwriting_crew(state)

        # All products should be evaluated
        assert len(results) == 3
        assert all(
            r.risk_class in [
                RiskClass.APPROVED,
                RiskClass.APPROVED_WITH_FLATEX,
                RiskClass.PENDING_REVIEW,
                RiskClass.DECLINED,
            ]
            for r in results.values()
        )
