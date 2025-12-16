"""Tools for HedgingCrew agents.

Helper functions for:
- Black-Scholes Greeks calculation
- Volatility surface interpolation
- SABR model calibration (simplified)
- Hedge position optimization
"""

import math
from typing import Dict, Tuple


# ===== BLACK-SCHOLES GREEKS =====


def black_scholes_d1_d2(
    S: float, K: float, T: float, r: float, sigma: float
) -> Tuple[float, float]:
    """
    Calculate d1 and d2 for Black-Scholes.

    Args:
        S: Spot price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate
        sigma: Volatility (annualized)

    Returns:
        (d1, d2) tuple
    """
    if T <= 0 or sigma <= 0:
        return (0.0, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return (d1, d2)


def normal_cdf(x: float) -> float:
    """Cumulative normal distribution (approximation)."""
    # Accurate approximation for CDF
    return 0.5 * (1.0 + math.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * x**3)))


def normal_pdf(x: float) -> float:
    """Probability density function for standard normal."""
    return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)


def black_scholes_call(
    S: float, K: float, T: float, r: float, sigma: float
) -> float:
    """
    Black-Scholes European call option price.

    Args:
        S: Spot price
        K: Strike price
        T: Time to maturity
        r: Risk-free rate
        sigma: Volatility

    Returns:
        Call option price
    """
    if T <= 0:
        return max(S - K, 0.0)
    if sigma <= 0:
        return max(S - K * math.exp(-r * T), 0.0)

    d1, d2 = black_scholes_d1_d2(S, K, T, r, sigma)
    call = S * normal_cdf(d1) - K * math.exp(-r * T) * normal_cdf(d2)
    return max(call, 0.0)


def black_scholes_put(
    S: float, K: float, T: float, r: float, sigma: float
) -> float:
    """
    Black-Scholes European put option price.

    Returns:
        Put option price
    """
    if T <= 0:
        return max(K - S, 0.0)
    if sigma <= 0:
        return max(K * math.exp(-r * T) - S, 0.0)

    d1, d2 = black_scholes_d1_d2(S, K, T, r, sigma)
    put = K * math.exp(-r * T) * normal_cdf(-d2) - S * normal_cdf(-d1)
    return max(put, 0.0)


def calculate_delta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """
    Calculate option delta (dPrice/dSpot).

    Args:
        option_type: "call" or "put"

    Returns:
        Delta (-1 to +1)
    """
    if T <= 0:
        return 1.0 if option_type == "call" and S > K else 0.0

    d1, _ = black_scholes_d1_d2(S, K, T, r, sigma)

    if option_type == "call":
        return normal_cdf(d1)
    else:  # put
        return normal_cdf(d1) - 1.0


def calculate_gamma(
    S: float, K: float, T: float, r: float, sigma: float
) -> float:
    """
    Calculate option gamma (d²Price/dSpot²).

    Gamma is always positive (same for calls and puts).

    Returns:
        Gamma (second derivative of option value)
    """
    if T <= 0 or sigma <= 0:
        return 0.0

    d1, _ = black_scholes_d1_d2(S, K, T, r, sigma)
    gamma = normal_pdf(d1) / (S * sigma * math.sqrt(T))
    return gamma


def calculate_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate option vega (dPrice/dVol).

    Vega is always positive (same for calls and puts).
    Returns vega per 1% change in volatility (typically divided by 100).

    Returns:
        Vega (usually expressed per 1% vol change)
    """
    if T <= 0 or sigma <= 0:
        return 0.0

    d1, _ = black_scholes_d1_d2(S, K, T, r, sigma)
    vega = S * normal_pdf(d1) * math.sqrt(T) / 100.0
    return vega


def calculate_theta(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """
    Calculate option theta (dPrice/dTime, per day).

    Args:
        option_type: "call" or "put"

    Returns:
        Theta per day (negative for long options, positive for short)
    """
    if T <= 0:
        return 0.0

    d1, d2 = black_scholes_d1_d2(S, K, T, r, sigma)

    if option_type == "call":
        theta = (
            -S * normal_pdf(d1) * sigma / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * normal_cdf(d2)
        )
    else:  # put
        theta = (
            -S * normal_pdf(d1) * sigma / (2 * math.sqrt(T))
            + r * K * math.exp(-r * T) * normal_cdf(-d2)
        )

    # Convert to per-day (divide by 365)
    return theta / 365.0


def calculate_rho(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """
    Calculate option rho (dPrice/dRate).

    Sensitivity to interest rate changes (per 1% rate change).

    Returns:
        Rho per 1% rate change
    """
    if T <= 0:
        return 0.0

    _, d2 = black_scholes_d1_d2(S, K, T, r, sigma)

    if option_type == "call":
        rho = K * T * math.exp(-r * T) * normal_cdf(d2) / 100.0
    else:  # put
        rho = -K * T * math.exp(-r * T) * normal_cdf(-d2) / 100.0

    return rho


# ===== PORTFOLIO GREEKS =====


def calculate_glwb_liability_delta(
    account_value: float, benefit_base: float, spot_price: float, T: float, r: float
) -> float:
    """
    Calculate delta of GLWB liability.

    GLWB liability has negative delta (benefit increases if equity falls).
    Simplified: delta ≈ -min(account_value / benefit_base, 1.0) * 0.5

    Returns:
        Delta of liability (typically negative)
    """
    # Liability gets worse (higher) if equity falls
    # Rough approximation: 50% of downside impact
    hedge_ratio = min(account_value / benefit_base, 1.0) if benefit_base > 0 else 0.5
    return -hedge_ratio * 0.5


def calculate_glwb_liability_vega(
    account_value: float, time_to_maturity: float
) -> float:
    """
    Calculate vega of GLWB liability.

    GLWB has positive vega (higher volatility increases liability).
    Approximation based on embedded option nature.

    Returns:
        Vega of liability (positive)
    """
    # Rough approximation: vega increases with time and account value
    return account_value * time_to_maturity / 10000.0


# ===== SABR MODEL (Simplified) =====


def sabr_implied_vol(
    F: float, K: float, T: float, alpha: float, beta: float, rho: float, nu: float
) -> float:
    """
    Simplified SABR implied volatility.

    SABR (Stochastic Alpha-Beta-Rho) model for capturing volatility smile.

    Args:
        F: Forward rate/price
        K: Strike price
        T: Time to maturity
        alpha: Volatility scale (ATM)
        beta: CEV exponent (0.5-1.0)
        rho: Correlation between price and vol
        nu: Vol of vol

    Returns:
        Implied volatility from SABR
    """
    if T <= 0 or alpha <= 0:
        return 0.18  # Default to 18% if invalid

    # Simplified SABR (Hagan formula approximation)
    # For beta=1 (lognormal), simplifies to ATM vol with smile adjustment
    FK = (F * K) ** ((1 - beta) / 2)

    # ATM vol
    atm_vol = alpha / (F ** (1 - beta))

    # Smile adjustment (increases vol for OTM strikes)
    moneyness = (K - F) / F if F > 0 else 0
    smile = 1.0 + (rho * nu / (4 * alpha)) * (moneyness**2)

    implied_vol = atm_vol * smile
    return max(implied_vol, 0.05)  # Floor at 5%


def calibrate_sabr_simple(
    spot: float, atm_vol: float, skew_vol: float
) -> Dict[str, float]:
    """
    Simplified SABR calibration.

    Uses ATM vol and skew to estimate SABR parameters.
    In practice, would use optimization; here we use heuristics.

    Args:
        spot: Current spot price
        atm_vol: At-the-money volatility
        skew_vol: Volatility skew (difference between OTM and ATM)

    Returns:
        Dict with {alpha, beta, rho, nu}
    """
    alpha = atm_vol  # Alpha ≈ ATM vol
    beta = 0.8  # Typically between 0.5-1.0, use 0.8 for equity
    nu = max(skew_vol / atm_vol, 0.1) if atm_vol > 0 else 0.2  # Nu from skew
    rho = -0.5 + skew_vol / atm_vol  # Negative correlation for equity puts

    return {"alpha": alpha, "beta": beta, "rho": rho, "nu": nu}


# ===== VOLATILITY SURFACE =====


def build_vol_surface(
    atm_vol: float, skew: float, term_structure: Dict[float, float]
) -> Dict[str, Dict[str, float]]:
    """
    Build simplified volatility surface.

    Args:
        atm_vol: At-the-money volatility
        skew: Smile slope (typically -0.01 to -0.05)
        term_structure: {T: vol_factor} for different maturities

    Returns:
        Surface as {term: {strike: vol}}
    """
    surface = {}

    for T, term_factor in term_structure.items():
        strikes = {}
        for moneyness_pct in [-20, -10, 0, 10, 20]:  # OTM to ITM
            # Smile adjustment: puts more expensive due to skew
            skew_adjustment = skew * (moneyness_pct / 10) if moneyness_pct <= 0 else 0
            vol = (atm_vol + skew_adjustment) * term_factor
            strikes[f"{moneyness_pct:+d}%"] = max(vol, 0.05)

        surface[f"T{T}"] = strikes

    return surface


# ===== HEDGE OPTIMIZATION =====


def calculate_optimal_put_strike(
    spot: float, liability_value: float, time_to_maturity: float
) -> float:
    """
    Calculate optimal put strike for downside protection.

    Strategy: Strike at distance reflecting liability size.
    Larger liability → lower strike (less protection).

    Returns:
        Strike price (in $ terms)
    """
    # Put strike typically 5-10% below spot for VA
    protection_level = min(liability_value / (spot * 10), 0.10)
    strike = spot * (1.0 - protection_level)
    return strike


def calculate_hedge_notional(
    account_value: float, liability_delta: float, put_delta: float
) -> float:
    """
    Calculate notional to hedge using puts.

    Hedge notional = account_value * |liability_delta| / |put_delta|

    Returns:
        Notional amount to buy in puts
    """
    if put_delta >= 0 or liability_delta >= 0:
        return 0.0

    # Negative deltas, so absolute values
    hedge_notional = account_value * abs(liability_delta) / abs(put_delta)
    return hedge_notional


def calculate_hedge_cost(
    hedge_notional: float, put_premium: float
) -> Tuple[float, float]:
    """
    Calculate hedge cost in dollars and basis points.

    Args:
        hedge_notional: Amount being hedged
        put_premium: Put option cost per unit

    Returns:
        (cost_dollars, cost_bps)
    """
    cost_dollars = hedge_notional * put_premium
    cost_bps = (cost_dollars / hedge_notional * 10000) if hedge_notional > 0 else 0
    return (cost_dollars, cost_bps)
