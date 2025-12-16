"""LangGraph workflow for UnderwritingCrew.

Defines the multi-agent orchestration:
1. Extract: Load health metrics from PDF or fixture
2. Validate: Check consistency of extracted metrics
3. Classify: Determine VBT mortality class
4. Approve: Apply product-specific rules and make final decision

Conditional routing:
- If extraction confidence < 0.5: Skip to end with PENDING_REVIEW
- If schema validation fails: Skip to end with PENDING_REVIEW
- Otherwise: Continue through full workflow
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import UnderwritingState, RiskClass
from .agents import (
    extraction_agent,
    validation_agent,
    mortality_agent,
    approval_agent,
)


def build_underwriting_crew() -> StateGraph:
    """
    Build UnderwritingCrew as LangGraph workflow.

    Workflow graph:
    ```
    START
      ↓
    EXTRACT (load health metrics)
      ↓
    ROUTE_AFTER_EXTRACT (confidence threshold)
      ├→ (confidence < 0.5) → END (PENDING_REVIEW)
      └→ (confidence ≥ 0.5) → VALIDATE
           ↓
         CLASSIFY (VBT mortality)
           ↓
         APPROVE (final decision)
           ↓
         END
    ```

    Returns:
        Compiled LangGraph StateGraph ready for invocation.

    Example:
        >>> crew = build_underwriting_crew()
        >>> state = UnderwritingState(
        ...     applicant_id="test_001",
        ...     product_type=ProductType.VA_GLWB,
        ...     age=55,
        ...     gender="M"
        ... )
        >>> result = crew.invoke(state)
        >>> result.risk_class
        <RiskClass.APPROVED: 'APPROVED'>
    """

    workflow = StateGraph(UnderwritingState)

    # ===== Add Nodes =====
    workflow.add_node("extract", extraction_agent)
    workflow.add_node("validate", validation_agent)
    workflow.add_node("classify", mortality_agent)
    workflow.add_node("approve", approval_agent)

    # ===== Add Edges =====

    # 1. START → EXTRACT
    workflow.add_edge(START, "extract")

    # 2. EXTRACT → ROUTE (conditional routing based on confidence)
    def route_after_extract(state: UnderwritingState) -> Literal["validate", "approve"]:
        """
        Route after extraction.

        If extraction confidence is too low, skip to approval stage
        which will set status to PENDING_REVIEW.
        Otherwise, continue to validation.
        """
        if state.extraction_confidence < 0.5:
            # Skip validation and go directly to approval for PENDING_REVIEW
            return "approve"
        return "validate"

    workflow.add_conditional_edges(
        "extract",
        route_after_extract,
        {"validate": "validate", "approve": "approve"},
    )

    # 3. VALIDATE → CLASSIFY (always)
    workflow.add_edge("validate", "classify")

    # 4. CLASSIFY → APPROVE (always)
    workflow.add_edge("classify", "approve")

    # 5. APPROVE → END
    workflow.add_edge("approve", END)

    # ===== Compile =====
    return workflow.compile()


def run_underwriting_crew(state: UnderwritingState) -> UnderwritingState:
    """
    Execute UnderwritingCrew workflow.

    Args:
        state: Initial UnderwritingState with applicant_id, product_type, age, gender

    Returns:
        Final UnderwritingState with risk_class and underwriting_notes.

    Example:
        >>> from insurance_ai.crews.underwriting import ProductType
        >>> state = UnderwritingState(
        ...     applicant_id="synthetic_001",
        ...     product_type=ProductType.VA_GLWB,
        ...     age=55,
        ...     gender="M"
        ... )
        >>> result = run_underwriting_crew(state)
        >>> print(result.to_dict())
    """
    crew = build_underwriting_crew()
    result_dict = crew.invoke(state)

    # Convert dict result back to UnderwritingState
    # (LangGraph's invoke() returns a dict, not the state object)
    if isinstance(result_dict, dict):
        # Recreate state from returned dict
        state.applicant_id = result_dict.get("applicant_id", state.applicant_id)
        state.extracted_health_metrics = result_dict.get(
            "extracted_health_metrics", state.extracted_health_metrics
        )
        state.extraction_confidence = result_dict.get(
            "extraction_confidence", state.extraction_confidence
        )
        state.extraction_warnings = result_dict.get(
            "extraction_warnings", state.extraction_warnings
        )
        state.vbt_mortality_class = result_dict.get(
            "vbt_mortality_class", state.vbt_mortality_class
        )
        state.mortality_adjustment_percent = result_dict.get(
            "mortality_adjustment_percent", state.mortality_adjustment_percent
        )
        state.risk_class = RiskClass(result_dict.get("risk_class", state.risk_class.value))
        state.confidence_score = result_dict.get("confidence_score", state.confidence_score)
        state.underwriting_notes = result_dict.get(
            "underwriting_notes", state.underwriting_notes
        )
        state.processing_method = result_dict.get(
            "processing_method", state.processing_method
        )
        state.approval_flags = result_dict.get("approval_flags", state.approval_flags)
        state.validation_metrics = result_dict.get(
            "validation_metrics", state.validation_metrics
        )

    return state
