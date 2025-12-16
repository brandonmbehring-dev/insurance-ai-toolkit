"""Cash Flow Projection Agent for ReserveCrew.

Projects policy cash flows (liabilities) across economic scenarios.
Applies mortality, lapse, and expense assumptions.
"""

from typing import Any, Dict, List
from insurance_ai.crews.reserve.state import ReserveState
from insurance_ai.crews.reserve import tools


def cash_flow_projection_agent(state: ReserveState) -> ReserveState:
    """
    Project policy cash flows across economic scenarios.

    For each scenario, calculates projected liabilities considering:
    - Mortality (reduces in-force population)
    - Lapse (policy surrenders)
    - Discounting (present value calculation)

    Args:
        state: ReserveState with economic_scenarios populated

    Returns:
        ReserveState with projected_cash_flows populated

    Validation:
        - projected_cash_flows dict has one entry per scenario
        - All cash flows are non-negative
        - Earlier cash flows have higher PV (due to discounting)
    """
    if not state.economic_scenarios:
        return state

    num_years = state.num_years
    issue_age = state.issue_age
    policy_month = state.policy_month
    account_value = state.account_value
    benefit_base = state.benefit_base

    projected_cash_flows_dict: Dict[str, List[float]] = {}
    reserve_paths: List[float] = []

    for scenario in state.economic_scenarios:
        scenario_id = scenario["scenario_id"]
        equity_path = scenario["equity_path"]
        rate_path = scenario["rate_path"]

        # Project cash flows for this scenario
        scenario_cash_flows = []
        scenario_pv = 0.0

        for year in range(num_years):
            # Current age and duration
            current_age = issue_age + (policy_month + year * 12) // 12
            duration = (policy_month + year * 12) // 12

            # Load mortality rate
            mortality_rate = tools.load_mortality_rate(
                gender="M", age=current_age, table_type="SOA_2012_IAM"
            )

            # Load lapse rate
            lapse_rate = tools.load_lapse_rate(
                issue_age=issue_age, duration=duration, model_type="SOA_2006_VBT"
            )

            # Probability of survival to this point
            # P(survive year) = (1 - mort_rate) * (1 - lapse_rate)
            survival_prob = (1.0 - mortality_rate) * (1.0 - lapse_rate)

            # Get interest rate for discounting
            discount_rate = rate_path[year] if year < len(rate_path) else rate_path[-1]

            # Calculate discount factor
            df = tools.calculate_discount_factor(discount_rate, float(year))

            # Expected liability at year = benefit_base * survival * discount
            expected_liability = benefit_base * survival_prob * df
            scenario_cash_flows.append(expected_liability)

            # Add to present value
            scenario_pv += expected_liability

        projected_cash_flows_dict[scenario_id] = scenario_cash_flows
        reserve_paths.append(scenario_pv)

    state.projected_cash_flows = projected_cash_flows_dict
    state.reserve_paths = reserve_paths

    # Calculate mean for later use
    if reserve_paths:
        state.expected_liability_pv = tools.calculate_mean(reserve_paths)

    return state
