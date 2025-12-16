"""LangGraph workflow for BehaviorCrew.

Defines multi-agent orchestration for policyholder behavior modeling:
1. Lapse Modeling: Calculate dynamic lapse rates
2. Withdrawal Planning: Determine optimal withdrawal strategy
3. Path Simulation: Monte Carlo paths with behavioral assumptions
4. Sensitivity Analysis: Impact of rate/vol shocks on behavior

Validates against:
- Moneyness-lapse relationship (OTM = high lapse, ITM = low lapse)
- In-force probability (% not surrendered by maturity)
- Withdrawal sustainability (account doesn't deplete)
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END

from .state import BehaviorState, WithdrawalStrategy
from . import tools


def lapse_modeling_agent(state: BehaviorState) -> BehaviorState:
    """
    Calculate dynamic lapse rates based on economic conditions.

    Factors:
    - Moneyness (account value vs guarantee)
    - Interest rates (lower rates = more valuable guarantee)
    - Market volatility (higher vol = more valuable guarantee)
    """
    # Calculate moneyness
    state.moneyness = tools.calculate_moneyness(
        state.account_value, state.benefit_base
    )

    # Calculate dynamic lapse rate
    state.dynamic_lapse_rate = tools.calculate_dynamic_lapse_rate(
        base_rate=state.base_lapse_rate,
        moneyness=state.moneyness,
        risk_free_rate=state.risk_free_rate,
        market_volatility=state.market_volatility,
    )

    # Calculate lapse by year (gradually revert to base)
    state.lapse_rate_by_year = []
    current_lapse = state.dynamic_lapse_rate
    for year in range(int(state.time_to_maturity_years)):
        # Revert towards base over time
        reversion = min(year / 5.0, 1.0)
        year_lapse = (
            state.base_lapse_rate * reversion + current_lapse * (1.0 - reversion)
        )
        state.lapse_rate_by_year.append(year_lapse)

    return state


def withdrawal_planning_agent(state: BehaviorState) -> BehaviorState:
    """
    Determine optimal withdrawal strategy for GLWB/GMWB.

    Strategy selection:
    - Conservative: Minimize withdrawals to preserve capital
    - Aggressive: Maximize early withdrawals
    - Optimal: Balance income and preservation
    - Static: Fixed withdrawal amount
    """
    # Calculate optimal withdrawal rate
    state.optimal_withdrawal_rate = tools.calculate_withdrawal_rate(
        account_value=state.account_value,
        benefit_base=state.benefit_base,
        remaining_years=state.time_to_maturity_years,
    )

    # Determine strategy
    if state.moneyness < 0.9:
        # Out-of-the-money: conservative
        state.recommended_strategy = WithdrawalStrategy.CONSERVATIVE
    elif state.moneyness > 1.2:
        # Well in-the-money: aggressive
        state.recommended_strategy = WithdrawalStrategy.AGGRESSIVE
    else:
        # Near-the-money: optimal (balanced)
        state.recommended_strategy = WithdrawalStrategy.OPTIMAL

    return state


def path_simulation_agent(state: BehaviorState) -> BehaviorState:
    """
    Simulate account value paths with lapse and withdrawal behavior.

    For each scenario:
    1. Calculate year-by-year lapse rates
    2. Simulate surrender decisions (Bernoulli with year-specific rate)
    3. Calculate account value evolution
    4. Track whether account is in-force at maturity
    """
    # Run Monte Carlo simulation
    account_paths, in_force_flags = tools.simulate_behavioral_paths(
        initial_account_value=state.account_value,
        benefit_base=state.benefit_base,
        annual_withdrawal=state.annual_withdrawal_amount,
        base_lapse=state.base_lapse_rate,
        num_years=int(state.time_to_maturity_years),
        num_scenarios=state.num_scenarios,
        risk_free_rate=state.risk_free_rate,
        market_vol=state.market_volatility,
        seed=state.scenario_seed,
    )

    state.simulated_account_values = account_paths
    state.simulated_surrenders = [
        i if not in_force else None
        for i, in_force in enumerate([not flag for flag in in_force_flags])
    ]

    # Calculate probability in-force at maturity
    num_in_force = sum(in_force_flags)
    state.probability_in_force_at_maturity = (
        num_in_force / state.num_scenarios if state.num_scenarios > 0 else 0.0
    )

    # Calculate average account value at maturity (among survivors)
    if num_in_force > 0:
        final_values = [
            path[-1]
            for path, in_force in zip(account_paths, in_force_flags)
            if in_force
        ]
        state.average_account_value_at_maturity = sum(final_values) / len(final_values)
    else:
        state.average_account_value_at_maturity = 0.0

    return state


def sensitivity_analysis_agent(state: BehaviorState) -> BehaviorState:
    """
    Analyze sensitivity of lapse rates to rate and volatility shocks.

    Shocks:
    - Rates +100bps: Higher rates reduce guarantee value → higher lapse
    - Rates -100bps: Lower rates increase guarantee value → lower lapse
    - Vol +25%: Higher vol increases guarantee value → lower lapse
    """
    # Rate sensitivity
    lapse_rates_up, lapse_rates_down = tools.calculate_rate_sensitivity(
        base_rate=state.base_lapse_rate,
        moneyness=state.moneyness,
        base_rf_rate=state.risk_free_rate,
    )
    state.lapse_rate_if_rates_up = lapse_rates_up
    state.lapse_rate_if_rates_down = lapse_rates_down

    # Vol sensitivity (simplified: lower vol increases lapse)
    low_vol = state.market_volatility * 0.75  # 25% vol down
    state.lapse_rate_if_vol_up = tools.calculate_dynamic_lapse_rate(
        state.base_lapse_rate,
        state.moneyness,
        state.risk_free_rate,
        low_vol,
    )

    # Calculate reserve impact
    # Behavioral impact = (reserve) * (probability not in force)
    # This represents selection/adverse lapse risk
    base_reserve = state.account_value * 0.10  # Rough estimate
    state.reserve_impact_from_behavior = tools.calculate_behavior_reserve_impact(
        base_reserve=base_reserve,
        probability_in_force=state.probability_in_force_at_maturity,
        average_av_at_maturity=state.average_account_value_at_maturity,
    )

    # Behavioral adjustment to reserve
    state.behavioral_adjustment_to_reserve = (
        state.reserve_impact_from_behavior / base_reserve
        if base_reserve > 0
        else 0.0
    )

    # Validation metrics
    validation_metrics = {}

    # Check moneyness-lapse relationship
    if state.moneyness < 0.8:
        if state.dynamic_lapse_rate > state.base_lapse_rate:
            validation_metrics["otm_lapse_increase"] = "PASS"
        else:
            validation_metrics["otm_lapse_increase"] = "WARN"
    else:
        validation_metrics["moneyness_standard"] = "OK"

    # Check in-force probability
    if 0.0 <= state.probability_in_force_at_maturity <= 1.0:
        validation_metrics["in_force_probability"] = (
            f"{state.probability_in_force_at_maturity * 100:.1f}%"
        )
    else:
        validation_metrics["in_force_probability"] = "ERROR"

    # Check lapse rate bounds
    if 0.01 <= state.dynamic_lapse_rate <= 0.50:
        validation_metrics["lapse_rate_bounds"] = "PASS"
    else:
        validation_metrics["lapse_rate_bounds"] = "FAIL"

    # Withdrawal sustainability
    if state.annual_withdrawal_amount < state.account_value * 0.10:
        validation_metrics["withdrawal_sustainable"] = "PASS"
    else:
        validation_metrics["withdrawal_sustainable"] = "WARN"

    state.validation_metrics = validation_metrics

    return state


def build_behavior_crew() -> StateGraph:
    """
    Build BehaviorCrew as LangGraph workflow.

    Workflow:
    ```
    START
      ↓
    LAPSE_MODELING (Dynamic lapse rates)
      ↓
    WITHDRAWAL_PLANNING (Optimal strategy)
      ↓
    PATH_SIMULATION (Monte Carlo with behavior)
      ↓
    SENSITIVITY_ANALYSIS (Rate/vol shocks)
      ↓
    END (Output behavioral impact)
    ```

    Returns:
        Compiled LangGraph StateGraph ready for invocation
    """
    workflow = StateGraph(BehaviorState)

    # Add nodes
    workflow.add_node("lapse_modeling", lapse_modeling_agent)
    workflow.add_node("withdrawal_planning", withdrawal_planning_agent)
    workflow.add_node("path_simulation", path_simulation_agent)
    workflow.add_node("sensitivity_analysis", sensitivity_analysis_agent)

    # Linear flow
    workflow.add_edge(START, "lapse_modeling")
    workflow.add_edge("lapse_modeling", "withdrawal_planning")
    workflow.add_edge("withdrawal_planning", "path_simulation")
    workflow.add_edge("path_simulation", "sensitivity_analysis")
    workflow.add_edge("sensitivity_analysis", END)

    return workflow.compile()


def run_behavior_crew(state: BehaviorState) -> BehaviorState:
    """
    Execute BehaviorCrew workflow.

    Args:
        state: Initial BehaviorState with policy data

    Returns:
        Final BehaviorState with behavioral analysis and reserve impact

    Example:
        >>> from insurance_ai.crews.behavior import BehaviorState, run_behavior_crew
        >>> state = BehaviorState(
        ...     policy_id="VA_001",
        ...     portfolio_name="Test Portfolio",
        ...     valuation_date="2025-12-31",
        ...     account_value=250000.0,
        ...     benefit_base=350000.0,
        ...     annual_withdrawal_amount=15000.0,
        ...     time_to_maturity_years=20.0,
        ... )
        >>> result = run_behavior_crew(state)
        >>> print(f"Lapse Rate: {result.dynamic_lapse_rate * 100:.1f}%")
        >>> print(f"In-Force Probability: {result.probability_in_force_at_maturity * 100:.1f}%")
    """
    crew = build_behavior_crew()
    result_dict = crew.invoke(state, config={"recursion_limit": 50})

    # Convert dict result back to BehaviorState
    if isinstance(result_dict, dict):
        for key, value in result_dict.items():
            if hasattr(state, key):
                setattr(state, key, value)

    return state
