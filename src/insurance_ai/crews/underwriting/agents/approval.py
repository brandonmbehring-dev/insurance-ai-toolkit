"""Approval agent: Apply product-specific approval rules.

This agent makes the final approval decision based on:
- Product type (VA + GLWB has stricter rules than FIA/RILA)
- Applicant age (must be within product range)
- Mortality adjustment (must not exceed product limit)
- Extraction confidence (must be >70%)

Output: risk_class (APPROVED, APPROVED_WITH_FLATEX, PENDING_REVIEW, DECLINED)
"""

from ..state import UnderwritingState, RiskClass
from ..tools import check_approval_rules


def approval_agent(state: UnderwritingState) -> UnderwritingState:
    """
    Apply product-specific approval rules and make final decision.

    Rules by product:
    - VA + GLWB: Stricter (living benefits require longevity)
      - Max mortality adjustment: +50%
      - Age range: 40-85
    - FIA: Standard
      - Max mortality adjustment: +100%
      - Age range: 35-90
    - RILA: Standard
      - Max mortality adjustment: +100%
      - Age range: 35-90

    Approval outcomes:
    - APPROVED: All rules met, standard rates apply
    - APPROVED_WITH_FLATEX: Rules met, but requires flatex rider
    - PENDING_REVIEW: Manual review needed (low confidence, etc.)
    - DECLINED: Does not meet underwriting requirements

    Args:
        state: Current UnderwritingState with classification complete

    Returns:
        Updated state with risk_class, confidence_score, underwriting_notes.

    Example:
        >>> state.age = 55
        >>> state.product_type = ProductType.VA_GLWB
        >>> state.mortality_adjustment_percent = 35
        >>> state.extraction_confidence = 0.95
        >>> state = approval_agent(state)
        >>> state.risk_class
        <RiskClass.APPROVED: 'APPROVED'>
    """

    # Check approval rules using tool
    approval_result = check_approval_rules(
        product_type=state.product_type.value,
        age=state.age,
        mortality_adjustment_percent=state.mortality_adjustment_percent,
        extraction_confidence=state.extraction_confidence,
    )

    # Map result to RiskClass
    class_map = {
        "APPROVED": RiskClass.APPROVED,
        "APPROVED_WITH_FLATEX": RiskClass.APPROVED_WITH_FLATEX,
        "PENDING_REVIEW": RiskClass.PENDING_REVIEW,
        "DECLINED": RiskClass.DECLINED,
    }
    state.risk_class = class_map.get(approval_result["class"], RiskClass.PENDING_REVIEW)

    # Calculate final confidence score
    # Base: extraction confidence
    base_confidence = state.extraction_confidence

    # Penalties for warnings
    warning_penalty = len(state.extraction_warnings) * 0.05
    state.confidence_score = max(0.0, base_confidence - warning_penalty)

    # Penalties for uncertain mortality class
    if state.vbt_mortality_class in ["Standard + Flatex", "Sub-Standard"]:
        state.confidence_score *= 0.9  # 10% reduction

    # Build summary notes
    notes = []
    notes.extend(approval_result["reasons"])

    if state.extraction_warnings:
        notes.append(f"Warnings: {', '.join(state.extraction_warnings[:2])}")

    if state.risk_class == RiskClass.APPROVED:
        notes.append(f"VBT Class: {state.vbt_mortality_class}")
        notes.append("No additional riders or adjustments required.")

    elif state.risk_class == RiskClass.APPROVED_WITH_FLATEX:
        notes.append(f"VBT Class: {state.vbt_mortality_class}")
        notes.append(
            f"Flatex rider required (premium increase: ~{state.mortality_adjustment_percent:.0f}%)"
        )

    elif state.risk_class == RiskClass.PENDING_REVIEW:
        notes.append("Manual underwriting review required.")
        if state.extraction_confidence < 0.7:
            notes.append(
                f"Extraction confidence low: {state.extraction_confidence:.0%} (recommend manual review)"
            )

    elif state.risk_class == RiskClass.DECLINED:
        notes.append("Application does not meet underwriting requirements.")
        notes.append(f"Primary reason: {approval_result['reasons'][0]}")

    state.underwriting_notes = " ".join(notes)

    # Add validation metrics
    state.validation_metrics = {
        "schema_valid": "PASS" if state.schema_valid else "FAIL",
        "extraction_confidence": f"{state.extraction_confidence:.0%}",
        "warnings_count": str(len(state.extraction_warnings)),
        "final_confidence_score": f"{state.confidence_score:.0%}",
        "approval_status": state.risk_class.value,
    }

    return state
