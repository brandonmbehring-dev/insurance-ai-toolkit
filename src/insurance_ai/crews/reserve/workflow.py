"""LangGraph workflow for ReserveCrew.

Defines the multi-agent orchestration for regulatory reserve calculations:
1. Scenario Generation: Create 100-10000 economic scenarios
2. Cash Flow Projection: Project liabilities via mortality/lapse/discounting
3. CTE Calculation: Calculate percentiles, risk margin
4. Sensitivity Analysis: Shock rates, vol, lapse
5. Convergence Validation: Check accuracy and regulatory compliance

Convergence Loop:
- If convergence_error > 2%: Loop back to scenario generation with more scenarios
- Otherwise: Output final reserve
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import ReserveState
from .agents.scenario_generation import scenario_generation_agent
from .agents.cash_flow_projection import cash_flow_projection_agent
from .agents.cte_calculation import cte_calculation_agent
from .agents.sensitivity_analysis import sensitivity_analysis_agent
from .agents.convergence_validation import convergence_validation_agent


def build_reserve_crew() -> StateGraph:
    """
    Build ReserveCrew as LangGraph workflow.

    Workflow graph:
    ```
    START
      ↓
    SCENARIO_GENERATION (Create economic scenarios)
      ↓
    CASH_FLOW_PROJECTION (Project liabilities)
      ↓
    CTE_CALCULATION (Calculate percentiles, risk margin)
      ↓
    SENSITIVITY_ANALYSIS (Rate, vol, lapse shocks)
      ↓
    CONVERGENCE_VALIDATION (Check accuracy)
      ↓
    ROUTE_CONVERGENCE (convergence_error < 2%?)
      ├─ YES → END (output reserve)
      └─ NO → SCENARIO_GENERATION (more scenarios, up to 5000)
    ```

    Returns:
        Compiled LangGraph StateGraph ready for invocation.

    Example:
        >>> crew = build_reserve_crew()
        >>> state = ReserveState(
        ...     policy_id="test_001",
        ...     product_type=ProductType.VA_GLWB,
        ...     issue_age=55,
        ...     policy_month=120,
        ...     account_value=250000,
        ...     benefit_base=350000,
        ...     valuation_date="2025-12-31"
        ... )
        >>> result = crew.invoke(state)
        >>> print(f"CTE70 Reserve: ${result.cte70_reserve:,.2f}")
    """

    workflow = StateGraph(ReserveState)

    # ===== Add Nodes =====
    # Actual agent implementations from agents/ module

    workflow.add_node("scenario_generation", scenario_generation_agent)
    workflow.add_node("cash_flow_projection", cash_flow_projection_agent)
    workflow.add_node("cte_calculation", cte_calculation_agent)
    workflow.add_node("sensitivity_analysis", sensitivity_analysis_agent)
    workflow.add_node("convergence_validation", convergence_validation_agent)

    # ===== Add Edges =====

    # START → Scenario Generation
    workflow.add_edge(START, "scenario_generation")

    # Linear flow through main agents
    workflow.add_edge("scenario_generation", "cash_flow_projection")
    workflow.add_edge("cash_flow_projection", "cte_calculation")
    workflow.add_edge("cte_calculation", "sensitivity_analysis")
    workflow.add_edge("sensitivity_analysis", "convergence_validation")

    # Conditional routing based on convergence
    def route_on_convergence(state: ReserveState) -> Literal["scenario_generation", "END"]:
        """
        Route based on convergence check.

        If convergence error > 2% and scenarios < 5000, loop back with more scenarios.
        Otherwise, output final reserve.
        """
        if (
            not state.converged
            and state.convergence_error_percent > 0.02
            and state.num_scenarios < 5000
        ):
            # Double scenarios but cap at 5000
            state.num_scenarios = min(state.num_scenarios * 2, 5000)
            return "scenario_generation"
        return "END"

    workflow.add_conditional_edges(
        "convergence_validation",
        route_on_convergence,
        {"scenario_generation": "scenario_generation", "END": END},
    )

    # ===== Compile =====
    return workflow.compile()


def run_reserve_crew(state: ReserveState) -> ReserveState:
    """
    Execute ReserveCrew workflow.

    Args:
        state: Initial ReserveState with policy metadata

    Returns:
        Final ReserveState with CTE70 reserve and validation metrics.

    Example:
        >>> from insurance_ai.crews.reserve import ProductType
        >>> state = ReserveState(
        ...     policy_id="VA_001",
        ...     product_type=ProductType.VA_GLWB,
        ...     issue_age=55,
        ...     policy_month=120,
        ...     account_value=250000,
        ...     benefit_base=350000,
        ...     valuation_date="2025-12-31"
        ... )
        >>> result = run_reserve_crew(state)
        >>> print(result.to_dict())
    """
    crew = build_reserve_crew()
    # Increase recursion limit for convergence loop (allows up to 5 iterations)
    result_dict = crew.invoke(state, config={"recursion_limit": 100})

    # Convert dict result back to ReserveState
    # (LangGraph's invoke() returns a dict, not the state object)
    if isinstance(result_dict, dict):
        state.economic_scenarios = result_dict.get(
            "economic_scenarios", state.economic_scenarios
        )
        state.projected_cash_flows = result_dict.get(
            "projected_cash_flows", state.projected_cash_flows
        )
        state.reserve_paths = result_dict.get("reserve_paths", state.reserve_paths)
        state.mean_reserve = result_dict.get("mean_reserve", state.mean_reserve)
        state.median_reserve = result_dict.get("median_reserve", state.median_reserve)
        state.percentile_reserves = result_dict.get(
            "percentile_reserves", state.percentile_reserves
        )
        state.cte70_reserve = result_dict.get("cte70_reserve", state.cte70_reserve)
        state.cte90_reserve = result_dict.get("cte90_reserve", state.cte90_reserve)
        state.risk_margin = result_dict.get("risk_margin", state.risk_margin)
        state.vm21_reserve = result_dict.get("vm21_reserve", state.vm21_reserve)
        state.vm22_reserve = result_dict.get("vm22_reserve", state.vm22_reserve)
        state.sensitivity_results = result_dict.get(
            "sensitivity_results", state.sensitivity_results
        )
        state.sensitivity_monotonicity = result_dict.get(
            "sensitivity_monotonicity", state.sensitivity_monotonicity
        )
        state.convergence_error_percent = result_dict.get(
            "convergence_error_percent", state.convergence_error_percent
        )
        state.converged = result_dict.get("converged", state.converged)
        state.validation_metrics = result_dict.get(
            "validation_metrics", state.validation_metrics
        )
        state.regulatory_reporting = result_dict.get(
            "regulatory_reporting", state.regulatory_reporting
        )
        state.processing_method = result_dict.get(
            "processing_method", state.processing_method
        )

    return state
