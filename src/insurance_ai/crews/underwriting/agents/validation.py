"""Validation agent: Check consistency of extracted health metrics.

This agent validates that extracted metrics are reasonable and consistent:
- BMI consistency (height, weight)
- Blood pressure reasonableness
- Cholesterol/triglycerides ratio
- Age-condition consistency
"""

from ..state import UnderwritingState
from ..tools import validate_health_metrics


def validation_agent(state: UnderwritingState) -> UnderwritingState:
    """
    Validate extracted metrics for consistency and outliers.

    Uses tool: validate_health_metrics()

    Args:
        state: Current UnderwritingState with extracted_health_metrics

    Returns:
        Updated state with extraction_warnings and schema_valid flag.

    Example:
        >>> state = UnderwritingState(...)
        >>> state.extracted_health_metrics = {
        ...     "height_cm": 175,
        ...     "weight_kg": 150,
        ...     "blood_pressure_systolic": 180,
        ...     "smoking_status": "current"
        ... }
        >>> state = validation_agent(state)
        >>> len(state.extraction_warnings) > 0
        True
    """

    # Validate metrics
    result = validate_health_metrics(state.extracted_health_metrics)

    # Store warnings
    state.extraction_warnings = result["warnings"]

    # If there are critical issues, mark schema as invalid
    if result["issues"]:
        state.schema_valid = False
        state.extraction_warnings.extend(result["issues"])

    # Additional age-specific checks
    age = state.extracted_health_metrics.get("age", 0)
    conditions = state.extracted_health_metrics.get("health_conditions", [])

    # Early-onset conditions
    if age < 50 and "Diabetes" in conditions:
        state.extraction_warnings.append(
            "Early-onset diabetes: Potential genetic component, recommend detailed underwriting"
        )

    if age < 45 and "Hypertension" in conditions:
        state.extraction_warnings.append(
            "Early-onset hypertension: Consider primary vs secondary hypertension"
        )

    # Smoking consistency
    smoking = state.extracted_health_metrics.get("smoking_status", "never")
    if smoking == "current" and age > 75:
        state.extraction_warnings.append("Advanced age with current smoking: High risk")

    return state
