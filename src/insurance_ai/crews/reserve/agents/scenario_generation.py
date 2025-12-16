"""Scenario Generation Agent for ReserveCrew.

Generates economic scenarios (equity paths, interest rate paths) for reserve calculations.
Uses GBM for equity indices and Vasicek for interest rates.
"""

from typing import Any, Dict, List
from insurance_ai.crews.reserve.state import ReserveState
from insurance_ai.crews.reserve import tools


def scenario_generation_agent(state: ReserveState) -> ReserveState:
    """
    Generate economic scenarios for reserve calculations.

    Creates equity index paths (GBM) and interest rate paths (Vasicek).
    Respects the num_scenarios and scenario_seed from state.

    Args:
        state: ReserveState with num_scenarios, scenario_seed, num_years

    Returns:
        ReserveState with populated economic_scenarios list

    Validation:
        - economic_scenarios is non-empty list
        - All scenarios have consistent length
        - Equity paths are positive (GBM property)
    """
    num_scenarios = state.num_scenarios
    num_years = state.num_years
    seed = state.scenario_seed

    # GBM parameters for equity index
    S0 = 100.0  # Initial equity index
    mu = 0.075  # 7.5% drift (long-term equity return)
    sigma = 0.18  # 18% volatility (historical S&P 500)
    dt = 1.0  # Annual time step

    # Vasicek parameters for interest rates
    r0 = 0.03  # Initial 3% short rate
    kappa = 0.15  # Mean reversion speed
    theta = 0.04  # Long-term mean 4%
    sigma_rate = 0.01  # 1% volatility

    scenarios = []

    for scenario_idx in range(num_scenarios):
        # Generate distinct seed for each scenario
        scenario_seed = seed + scenario_idx

        # Generate equity path
        equity_path = tools.generate_gbm_path(
            S0=S0,
            mu=mu,
            sigma=sigma,
            dt=dt,
            T=float(num_years),
            seed=scenario_seed,
            num_steps=num_years,
        )

        # Generate rate path
        rate_path = tools.generate_vasicek_rates(
            r0=r0,
            kappa=kappa,
            theta=theta,
            sigma=sigma_rate,
            T=float(num_years),
            seed=scenario_seed + 10000,  # Different seed stream
            num_steps=num_years,
        )

        # Validate paths
        if not equity_path or not rate_path:
            continue

        # Clip rates to minimum (Vasicek can go negative, but practically useful floor)
        rate_path = [max(r, 0.001) for r in rate_path]

        scenario = {
            "scenario_id": f"scenario_{scenario_idx:04d}",
            "equity_path": equity_path,  # [S0, S1, ..., S_T]
            "rate_path": rate_path,  # [r0, r1, ..., r_T]
            "final_equity_level": equity_path[-1] if equity_path else S0,
            "final_rate": rate_path[-1] if rate_path else r0,
        }
        scenarios.append(scenario)

    state.economic_scenarios = scenarios
    state.num_scenarios = len(scenarios)  # Update in case some failed

    return state
