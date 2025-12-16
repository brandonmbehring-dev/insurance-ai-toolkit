"""Tools for BehaviorCrew agents.

Helper functions for:
- Dynamic lapse rate calculations
- Optimal withdrawal strategy determination
- Monte Carlo path simulation with behavioral assumptions
- Rate sensitivity analysis for policyholder behavior
"""

import math
import random
from typing import List, Tuple


# ===== LAPSE RATE CALCULATIONS =====


def calculate_moneyness(account_value: float, benefit_base: float) -> float:
    """
    Calculate moneyness ratio.

    Moneyness = Account Value / Benefit Base
    - Moneyness < 1.0: OTM (account below guarantee) - high lapse
    - Moneyness = 1.0: ATM (at guarantee) - base lapse
    - Moneyness > 1.0: ITM (account above guarantee) - low lapse

    Returns:
        Moneyness ratio
    """
    if benefit_base <= 0:
        return 1.0
    return account_value / benefit_base


def calculate_dynamic_lapse_rate(
    base_rate: float,
    moneyness: float,
    risk_free_rate: float,
    market_volatility: float,
    moneyness_elasticity: float = 0.05,
    rate_elasticity: float = 0.02,
    vol_elasticity: float = 0.01,
) -> float:
    """
    Calculate dynamic lapse rate based on economic conditions.

    Factors:
    1. Moneyness: OTM (ITM = low lapse, OTM = high lapse)
    2. Interest Rates: Higher rates → higher lapse (less valuable guarantee)
    3. Volatility: Higher vol → lower lapse (more valuable guarantee)

    Args:
        base_rate: Base lapse rate (ATM)
        moneyness: Account value / Benefit base ratio
        risk_free_rate: Risk-free interest rate
        market_volatility: Market volatility (annual)
        moneyness_elasticity: Sensitivity to moneyness changes
        rate_elasticity: Sensitivity to rate changes
        vol_elasticity: Sensitivity to volatility changes

    Returns:
        Adjusted lapse rate (bounded 0.01 to 0.50)
    """
    # 1. Moneyness adjustment
    # ITM (moneyness > 1) reduces lapse (benefit valuable)
    # OTM (moneyness < 1) increases lapse (account poor)
    moneyness_adjustment = moneyness_elasticity * (1.0 - moneyness)

    # 2. Rate adjustment
    # Higher rates reduce guarantee value → higher lapse
    base_rate_assumption = 0.03  # 3% base
    rate_adjustment = rate_elasticity * (risk_free_rate - base_rate_assumption)

    # 3. Volatility adjustment
    # Higher volatility increases guarantee value → lower lapse
    base_vol_assumption = 0.18  # 18% base
    vol_adjustment = -vol_elasticity * (market_volatility - base_vol_assumption)

    # Combined adjustment
    adjusted_rate = base_rate + moneyness_adjustment + rate_adjustment + vol_adjustment

    # Bounds: 1% minimum, 50% maximum
    return max(0.01, min(adjusted_rate, 0.50))


def calculate_withdrawal_rate(
    account_value: float, benefit_base: float, remaining_years: float
) -> float:
    """
    Calculate optimal withdrawal rate for GLWB.

    Strategy: Withdrawal amount that:
    1. Provides annual income (4% rule)
    2. Preserves benefit base for downside protection
    3. Adjusts for time to maturity

    Returns:
        Optimal withdrawal rate (% of account value per year)
    """
    if account_value <= 0:
        return 0.0

    moneyness = account_value / benefit_base if benefit_base > 0 else 1.0

    # If ITM: Can withdraw more (account above guarantee)
    if moneyness > 1.0:
        base_rate = 0.05  # 5% for ITM
        buffer = (moneyness - 1.0) * 0.02  # Extra 2% per 100% moneyness
        withdrawal_rate = min(base_rate + buffer, 0.08)  # Cap at 8%
    else:
        # If OTM: Conservative withdrawal
        base_rate = 0.03  # 3% for OTM
        withdrawal_rate = base_rate

    # Adjust for time to maturity (higher withdrawal near end)
    if remaining_years < 5:
        withdrawal_rate *= 1.5

    return min(withdrawal_rate, 0.10)  # Cap at 10%


# ===== MONTE CARLO PATH SIMULATION =====


def simulate_lapse_path(
    base_lapse: float,
    moneyness: float,
    risk_free_rate: float,
    market_vol: float,
    num_years: int,
) -> List[float]:
    """
    Simulate annual lapse rates for a single path.

    Lapse rates vary annually based on:
    - Initial moneyness
    - Interest rate path (simplified: constant)
    - Market vol (simplified: constant)

    Returns:
        List of lapse rates by year
    """
    lapse_rates = []

    # Start with dynamic lapse
    current_lapse = calculate_dynamic_lapse_rate(
        base_lapse, moneyness, risk_free_rate, market_vol
    )

    for year in range(num_years):
        # Gradually revert to base rate over time
        reversion_factor = min(year / 5.0, 1.0)  # Full reversion by year 5
        reverted_lapse = base_lapse * (1.0 - reversion_factor) + current_lapse * (
            1.0 - reversion_factor
        )

        # Add random variation (±20% of current)
        random_shock = random.gauss(1.0, 0.20)
        year_lapse = reverted_lapse * random_shock

        # Bounds
        year_lapse = max(0.01, min(year_lapse, 0.50))
        lapse_rates.append(year_lapse)

    return lapse_rates


def simulate_withdrawal_path(
    initial_account_value: float,
    annual_withdrawal: float,
    num_years: int,
    return_rate: float,
) -> Tuple[List[float], int]:
    """
    Simulate account value path with withdrawals.

    Assumes:
    - Fixed annual withdrawal
    - Constant return (simplified)
    - Account surrendered if depleted

    Returns:
        (account_value_path, surrender_year)
        surrender_year = None if account survives
    """
    account_values = [initial_account_value]
    current_av = initial_account_value
    surrender_year = None

    for year in range(1, num_years):
        # Apply return
        current_av = current_av * (1.0 + return_rate)

        # Apply withdrawal
        current_av = current_av - annual_withdrawal

        # Check for depletion
        if current_av <= 0:
            surrender_year = year
            account_values.append(0.0)
            break

        account_values.append(current_av)

    return (account_values, surrender_year)


def simulate_behavioral_paths(
    initial_account_value: float,
    benefit_base: float,
    annual_withdrawal: float,
    base_lapse: float,
    num_years: int,
    num_scenarios: int,
    risk_free_rate: float,
    market_vol: float,
    seed: int,
) -> Tuple[List[List[float]], List[bool]]:
    """
    Simulate account value paths with lapse and withdrawal behavior.

    For each scenario:
    1. Simulate lapse rates (vary with conditions)
    2. Check surrender each year based on lapse
    3. Simulate account value path
    4. Track whether account survives to maturity

    Returns:
        (account_value_paths, in_force_flags)
    """
    random.seed(seed)

    account_paths = []
    in_force_flags = []

    initial_moneyness = calculate_moneyness(initial_account_value, benefit_base)

    for scenario_idx in range(num_scenarios):
        # Scenario-specific random seed
        scenario_seed = seed + scenario_idx * 1000
        random.seed(scenario_seed)

        # Lapse path
        lapse_path = simulate_lapse_path(
            base_lapse, initial_moneyness, risk_free_rate, market_vol, num_years
        )

        # Account path with lapse behavior
        account_vals = [initial_account_value]
        current_av = initial_account_value
        in_force = True

        for year in range(num_years):
            # Lapse check (surrender decision)
            if random.random() < lapse_path[year]:
                # Surrendered
                in_force = False
                break

            # Otherwise, continue and apply returns (simplified: 5% annual)
            current_av = current_av * 1.05 - annual_withdrawal
            if current_av < 0:
                in_force = False
                break

            account_vals.append(current_av)

        # Pad path if surrendered early
        while len(account_vals) < num_years + 1:
            account_vals.append(0.0)

        account_paths.append(account_vals)
        in_force_flags.append(in_force)

    return (account_paths, in_force_flags)


# ===== SENSITIVITY CALCULATIONS =====


def calculate_rate_sensitivity(
    base_rate: float,
    moneyness: float,
    base_rf_rate: float,
    rate_elasticity: float = 0.02,
) -> Tuple[float, float]:
    """
    Calculate lapse rate sensitivity to interest rate changes.

    Returns:
        (lapse_if_rates_up_100bps, lapse_if_rates_down_100bps)
    """
    # Base dynamic lapse
    base_lapse = calculate_dynamic_lapse_rate(
        base_rate, moneyness, base_rf_rate, 0.18, rate_elasticity=rate_elasticity
    )

    # Rates up 100bps
    lapse_rates_up = calculate_dynamic_lapse_rate(
        base_rate,
        moneyness,
        base_rf_rate + 0.01,
        0.18,
        rate_elasticity=rate_elasticity,
    )

    # Rates down 100bps
    lapse_rates_down = calculate_dynamic_lapse_rate(
        base_rate,
        moneyness,
        base_rf_rate - 0.01,
        0.18,
        rate_elasticity=rate_elasticity,
    )

    return (lapse_rates_up, lapse_rates_down)


# ===== RESERVE IMPACT CALCULATIONS =====


def calculate_behavior_reserve_impact(
    base_reserve: float,
    probability_in_force: float,
    average_av_at_maturity: float,
) -> float:
    """
    Calculate impact of behavioral assumptions on reserve.

    If lapse is lower than assumed:
    - More policies in force → higher reserve (negative impact)

    If lapse is higher than assumed:
    - Fewer policies in force → lower reserve (positive impact)

    Args:
        base_reserve: Reserve assuming static lapse
        probability_in_force: % of scenarios that survive to maturity
        average_av_at_maturity: Average AV if in force

    Returns:
        Reserve adjustment ($ amount)
    """
    # Behavioral reserve = base reserve * probability in force
    # This captures selection (only healthy policies stay)
    behavioral_adjustment = base_reserve * (1.0 - probability_in_force)

    return behavioral_adjustment
