"""Mortality agent: Classify mortality risk using SOA 2012 IAM tables.

This agent:
1. Loads base mortality table for gender
2. Calculates adjusted mortality from health metrics
3. Maps to VBT mortality class
4. Stores adjustment factors for approval rules
"""

from ..state import UnderwritingState
from ..tools import load_mortality_table, calculate_health_adjustment


def mortality_agent(state: UnderwritingState) -> UnderwritingState:
    """
    Classify mortality risk using SOA 2012 IAM tables and health adjustments.

    Workflow:
    1. Load base mortality table for gender
    2. Calculate health adjustment factors (smoking, BMI, conditions)
    3. Apply adjustments to get adjusted mortality
    4. Map to VBT class (Super Preferred → Sub-Standard)

    Args:
        state: Current UnderwritingState with extracted_health_metrics

    Returns:
        Updated state with vbt_mortality_class and mortality_adjustment_percent.

    Example:
        >>> state.age = 55
        >>> state.gender = "M"
        >>> state.extracted_health_metrics = {"smoking_status": "current", ...}
        >>> state = mortality_agent(state)
        >>> state.vbt_mortality_class
        'Standard + Flatex'
        >>> state.mortality_adjustment_percent
        75.0
    """

    # Step 1: Load base mortality table
    mortality_table = load_mortality_table(state.gender)

    # Store for reference
    state.mortality_table_age = state.age

    # Step 2: Calculate health adjustment
    adjustment_result = calculate_health_adjustment(state.extracted_health_metrics)
    adjustment_factor = adjustment_result["adjustment_factor"]
    components = adjustment_result["components"]

    # Store adjustment details
    state.approval_flags = components
    state.mortality_adjustment_percent = adjustment_result["percent_increase"]

    # Step 3: Map adjustment factor to VBT class
    state.vbt_mortality_class = _map_to_vbt_class(adjustment_factor)

    return state


def _map_to_vbt_class(adjustment_factor: float) -> str:
    """
    Map adjustment factor to VBT (Valuation Basic Tables) mortality class.

    VBT Classes (in order of risk):
    - Super Preferred (0.0-1.0x): Excellent health, low mortality
    - Preferred (1.0-1.1x): Very good health
    - Standard (1.1-1.25x): Average health
    - Standard + Flatex (1.25-1.5x): Below average health, requires rider
    - Sub-Standard (1.5x+): Poor health, may decline

    Args:
        adjustment_factor: Mortality multiplier (1.0 = standard)

    Returns:
        VBT class name as string.

    Example:
        >>> _map_to_vbt_class(0.95)
        'Super Preferred'
        >>> _map_to_vbt_class(1.35)
        'Standard + Flatex'
    """
    if adjustment_factor <= 1.0:
        return "Super Preferred"
    elif adjustment_factor <= 1.1:
        return "Preferred"
    elif adjustment_factor <= 1.25:
        return "Standard"
    elif adjustment_factor <= 1.5:
        return "Standard + Flatex"
    else:
        return "Sub-Standard"
