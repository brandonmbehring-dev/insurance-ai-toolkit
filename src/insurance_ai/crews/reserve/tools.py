"""Tools for ReserveCrew agents.

Helper functions for:
- Scenario generation (GBM, Vasicek, AG43 scenarios)
- Cash flow projections (mortality, lapse, discounting)
- CTE and percentile calculations
- Sensitivity analysis and shock calculations
- Convergence and validation checks
"""

from typing import Dict, List, Any
import math


# ===== MORTALITY & LAPSE LOADING =====

def load_mortality_rate(gender: str, age: int, table_type: str = "SOA_2012_IAM") -> float:
    """
    Load mortality rate from SOA tables.

    Args:
        gender: "M" (male) or "F" (female)
        age: Age in years
        table_type: "SOA_2012_IAM" or "SOA_2006_VBT"

    Returns:
        Mortality rate (probability of death in year) as decimal (e.g., 0.005 = 0.5%)

    Example:
        >>> rate_male_60 = load_mortality_rate("M", 60)
        >>> rate_female_60 = load_mortality_rate("F", 60)
        >>> rate_male_60 > rate_female_60  # Males have higher mortality
        True
    """
    # Mock implementation - would load from annuity-pricing loaders module
    # This uses simplified SOA 2012 IAM male rates scaled by gender

    base_rates = {
        40: 0.00082,
        50: 0.00204,
        60: 0.00611,
        70: 0.01875,
        80: 0.05784,
    }

    # Find closest age
    closest_age = min(base_rates.keys(), key=lambda x: abs(x - age))
    rate = base_rates[closest_age]

    # Interpolate if needed (linear)
    if age not in base_rates and closest_age < age:
        # Find next age (if exists)
        ages_above = [k for k in base_rates.keys() if k > closest_age]
        if ages_above:
            next_age = min(ages_above)
            rate_next = base_rates[next_age]
            # Linear interpolation
            rate = rate + (rate_next - rate) * (age - closest_age) / (next_age - closest_age)
        # else: use closest_age rate (for ages > max table age)

    # Adjust for gender (females typically 65-70% of male mortality)
    if gender == "F":
        rate *= 0.67

    return rate


def load_lapse_rate(issue_age: int, duration: int, model_type: str = "SOA_2006_VBT") -> float:
    """
    Load static lapse rate from assumptions.

    Args:
        issue_age: Age at issue
        duration: Policy duration in years
        model_type: "SOA_2006_VBT" (standard), "static", "dynamic"

    Returns:
        Lapse rate as decimal (e.g., 0.06 = 6%)

    Example:
        >>> rate_early = load_lapse_rate(55, 2)  # Year 2 of issue
        >>> rate_late = load_lapse_rate(55, 10)  # Year 10 of issue
        >>> rate_early > rate_late  # Higher lapse in early years (typical)
        True
    """
    # SOA 2006 VBT lapse rates (typical pattern)
    vbt_rates = {
        1: 0.10,   # Year 1: 10% (high surrender)
        2: 0.08,   # Year 2: 8%
        3: 0.07,   # Year 3: 7%
        4: 0.06,   # Year 4-10: 6%
        5: 0.06,
        10: 0.06,  # After 10: steady 3-6%
        15: 0.04,
        20: 0.03,
        25: 0.03,
        30: 0.03,
    }

    # Find closest duration
    closest = min(vbt_rates.keys(), key=lambda x: abs(x - duration))
    return vbt_rates.get(duration, vbt_rates[closest])


# ===== DISCOUNT FACTOR CALCULATIONS =====

def calculate_discount_factor(zero_rate: float, years: float) -> float:
    """
    Calculate discount factor.

    Args:
        zero_rate: Zero-coupon rate (annual, continuous compounding)
        years: Years to discount

    Returns:
        Discount factor = exp(-rate * years)

    Example:
        >>> df_1y = calculate_discount_factor(0.03, 1.0)
        >>> df_1y
        0.9704...
    """
    return math.exp(-zero_rate * years)


def calculate_pv_single_payment(payment: float, discount_rate: float, years: float) -> float:
    """
    Calculate present value of single payment.

    Args:
        payment: Payment amount
        discount_rate: Discount rate (annual)
        years: Years to discount

    Returns:
        Present value = payment * exp(-rate * years)

    Example:
        >>> pv = calculate_pv_single_payment(1000, 0.04, 5)
        >>> pv < 1000  # PV is less than face amount
        True
    """
    df = calculate_discount_factor(discount_rate, years)
    return payment * df


# ===== SCENARIO HELPERS =====

def generate_gbm_path(
    S0: float, mu: float, sigma: float, dt: float, T: float, seed: int, num_steps: int = None
) -> List[float]:
    """
    Generate Geometric Brownian Motion (GBM) path for equity index.

    Used for: Stock prices, equity index levels (e.g., S&P 500)

    Args:
        S0: Initial stock price
        mu: Annual drift (e.g., 0.075 = 7.5% per year)
        sigma: Annual volatility (e.g., 0.18 = 18%)
        dt: Time step (e.g., 1/12 for monthly, 1 for yearly)
        T: Total time horizon in years
        seed: Random seed for reproducibility
        num_steps: Number of time steps (default: T/dt)

    Returns:
        Path: List of [S0, S1, S2, ..., ST]

    Example:
        >>> path = generate_gbm_path(S0=100, mu=0.075, sigma=0.18, dt=1, T=30, seed=42)
        >>> len(path)
        31  # T/dt + 1
        >>> path[0]
        100.0  # Starts at S0
        >>> path[-1] > 0  # All positive (GBM property)
        True
    """
    # Mock implementation - in production would use numpy with seed control
    # For now, return deterministic path for demo
    if num_steps is None:
        num_steps = int(T / dt)

    path = [S0]
    import random

    random.seed(seed)

    for _ in range(num_steps):
        dW = random.gauss(0, math.sqrt(dt))  # Brownian increment
        S_next = path[-1] * math.exp((mu - 0.5 * sigma**2) * dt + sigma * dW)
        path.append(S_next)

    return path


def generate_vasicek_rates(
    r0: float, kappa: float, theta: float, sigma: float, T: float, seed: int, num_steps: int = None
) -> List[float]:
    """
    Generate interest rate path using Vasicek model.

    Used for: Short-term interest rate paths (for discounting)

    Args:
        r0: Initial rate
        kappa: Mean reversion speed (>0)
        theta: Long-term mean rate
        sigma: Rate volatility
        T: Time horizon in years
        seed: Random seed
        num_steps: Number of steps

    Returns:
        Path: List of [r0, r1, r2, ..., rT]

    Example:
        >>> rates = generate_vasicek_rates(r0=0.03, kappa=0.15, theta=0.04, sigma=0.01, T=30, seed=42)
        >>> len(rates)
        31
        >>> all(r > -0.1 for r in rates)  # Vasicek can go negative (feature, not bug)
        True
    """
    # Mock implementation
    if num_steps is None:
        num_steps = int(T)

    path = [r0]
    import random

    random.seed(seed)

    for _ in range(num_steps):
        dW = random.gauss(0, 1.0)
        dr = kappa * (theta - path[-1]) + sigma * dW
        r_next = path[-1] + dr
        path.append(r_next)

    return path


# ===== CTE & PERCENTILE CALCULATIONS =====

def calculate_percentile(values: List[float], percentile: int) -> float:
    """
    Calculate percentile of a list of values.

    Args:
        values: List of reserve values
        percentile: Percentile level (0-100)

    Returns:
        Percentile value

    Example:
        >>> reserves = [90, 95, 100, 105, 110]
        >>> p50 = calculate_percentile(reserves, 50)
        >>> p50
        100  # Median
    """
    sorted_values = sorted(values)
    idx = int(len(sorted_values) * percentile / 100)
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


def calculate_cte_percentile(values: List[float], percentile: int) -> float:
    """
    Calculate Conditional Tail Expectation (CTE) at percentile level.

    CTE = Expected value given the worst (100-percentile)% of outcomes

    Args:
        values: List of reserve values
        percentile: Percentile level (e.g., 70 for CTE70)

    Returns:
        CTE value

    Example:
        >>> reserves = list(range(1, 1001))  # 1 to 1000
        >>> cte70 = calculate_cte_percentile(reserves, 70)
        >>> cte70 > 700  # Top 30% of reserves
        True
        >>> cte70 < 1000
        True
    """
    sorted_values = sorted(values)
    cutoff_idx = int(len(sorted_values) * percentile / 100)
    tail_values = sorted_values[cutoff_idx:]
    return sum(tail_values) / len(tail_values) if tail_values else 0.0


def calculate_mean(values: List[float]) -> float:
    """Calculate mean of values."""
    return sum(values) / len(values) if values else 0.0


def calculate_std_dev(values: List[float]) -> float:
    """Calculate standard deviation of values."""
    if not values:
        return 0.0
    mean = calculate_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


# ===== CONVERGENCE CHECKS =====

def calculate_convergence_error(cte70_n1000: float, cte70_n100: float) -> float:
    """
    Calculate convergence error between two scenario counts.

    Args:
        cte70_n1000: CTE70 calculated with 1000 scenarios
        cte70_n100: CTE70 calculated with 100 scenarios

    Returns:
        Error as percentage (e.g., 0.015 = 1.5%)

    Example:
        >>> error = calculate_convergence_error(95000, 94500)
        >>> error < 0.02  # <2% error = PASS
        True
    """
    if cte70_n1000 == 0:
        return 0.0
    return abs(cte70_n1000 - cte70_n100) / cte70_n1000


# ===== VALIDATION CHECKS =====

def validate_cte_invariant(mean_reserve: float, cte70_reserve: float) -> bool:
    """
    Validate mathematical invariant: CTE70 ≥ Mean.

    Args:
        mean_reserve: Mean of all scenario reserves
        cte70_reserve: CTE70 (top 30% mean)

    Returns:
        True if CTE70 ≥ Mean, False otherwise

    Example:
        >>> is_valid = validate_cte_invariant(100, 110)
        >>> is_valid
        True
    """
    return cte70_reserve >= mean_reserve - 0.01  # Small tolerance for rounding


def validate_sensitivity_direction(
    base_reserve: float, shocked_reserve: float, shock_direction: str
) -> bool:
    """
    Validate direction of sensitivity shock.

    Args:
        base_reserve: Reserve under base assumptions
        shocked_reserve: Reserve under shocked assumptions
        shock_direction: "rates_up", "vol_up", "lapse_up", etc.

    Returns:
        True if shock direction is economically reasonable

    Example:
        >>> # Rates up should decrease reserve (less discounting value)
        >>> is_valid = validate_sensitivity_direction(100, 95, "rates_up")
        >>> is_valid
        True
    """
    expected_directions = {
        "rates_up": shocked_reserve < base_reserve,  # Less present value
        "rates_down": shocked_reserve > base_reserve,  # More present value
        "vol_up": shocked_reserve > base_reserve,  # More tail risk
        "vol_down": shocked_reserve < base_reserve,  # Less tail risk
        "lapse_up": shocked_reserve < base_reserve,  # Shorter duration
    }

    return expected_directions.get(shock_direction, True)


# ===== REPORTING =====

def format_reserve_output(
    mean_reserve: float, cte70_reserve: float, percentiles: Dict[int, float]
) -> Dict[str, Any]:
    """
    Format reserve output for regulatory reporting.

    Args:
        mean_reserve: Expected value
        cte70_reserve: Risk-adjusted reserve
        percentiles: {10: X, 25: Y, 50: Z, ...}

    Returns:
        Formatted output dict

    Example:
        >>> output = format_reserve_output(100, 115, {50: 100, 75: 110})
        >>> output["mean_reserve"]
        100
    """
    return {
        "mean_reserve": mean_reserve,
        "cte70_reserve": cte70_reserve,
        "risk_margin": cte70_reserve - mean_reserve,
        "percentile_reserves": percentiles,
    }
