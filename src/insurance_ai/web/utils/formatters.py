"""
Data Formatting Utilities for Streamlit UI.

Provides consistent formatting for currency, percentages, dates, and insurance-specific metrics.
Used across all pages to ensure consistent display conventions.

Usage:
    formatted_amount = format_currency(450000)  # "$450,000"
    formatted_pct = format_percentage(0.0732)   # "7.3%"
    formatted_date = format_date(datetime.now()) # "2025-12-15"
    formatted_moneyness = format_moneyness(1.286) # "1.29x ITM"
"""

from datetime import datetime
from typing import Union, Optional
import math


def format_currency(
    value: Union[int, float],
    symbol: str = "$",
    decimals: int = 0,
) -> str:
    """
    Format number as US currency with thousands separator.

    Args:
        value: Numeric value to format
        symbol: Currency symbol (default: "$")
        decimals: Number of decimal places (default: 0 for whole dollars)

    Returns:
        Formatted currency string (e.g., "$1,234,567" or "$123.45")

    Examples:
        >>> format_currency(450000)
        '$450,000'
        >>> format_currency(58234.5, decimals=2)
        '$58,234.50'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return f"{symbol}N/A"

    format_spec = f":,.{decimals}f"
    formatted = f"{value{format_spec}}"
    return f"{symbol}{formatted}"


def format_percentage(
    value: float,
    decimals: int = 1,
    as_decimal: bool = False,
) -> str:
    """
    Format number as percentage.

    Args:
        value: Decimal value (0.0-1.0) or already-percentage (0-100)
        decimals: Number of decimal places (default: 1)
        as_decimal: If True, interpret input as decimal (0.5 = 50%). If False, assume percentage (50 = 50%)

    Returns:
        Formatted percentage string (e.g., "7.3%" or "73.2%")

    Examples:
        >>> format_percentage(0.0732)  # as_decimal=True by default
        '7.3%'
        >>> format_percentage(73.2, as_decimal=False)
        '73.2%'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return "N/A%"

    # Convert decimal to percentage if needed
    pct_value = value * 100 if as_decimal else value

    format_spec = f":.{decimals}f"
    return f"{pct_value{format_spec}}%"


def format_basis_points(value: float, decimals: int = 0) -> str:
    """
    Format number as basis points (1 bps = 0.01%).

    Args:
        value: Value in basis points (e.g., 50 = 0.5%)
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "50 bps")

    Examples:
        >>> format_basis_points(50)
        '50 bps'
        >>> format_basis_points(125.5)
        '125.5 bps'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return "N/A bps"

    format_spec = f":.{decimals}f"
    return f"{value{format_spec}} bps"


def format_date(
    date_obj: datetime,
    format_str: str = "%Y-%m-%d",
) -> str:
    """
    Format datetime object as string.

    Args:
        date_obj: datetime object to format
        format_str: strftime format string (default: YYYY-MM-DD)

    Returns:
        Formatted date string

    Examples:
        >>> from datetime import datetime
        >>> format_date(datetime(2025, 12, 15))
        '2025-12-15'
        >>> format_date(datetime(2025, 12, 15), "%B %d, %Y")
        'December 15, 2025'
    """
    if not isinstance(date_obj, datetime):
        raise TypeError(f"Expected datetime, got {type(date_obj).__name__}")

    return date_obj.strftime(format_str)


def format_moneyness(
    value: float,
    decimals: int = 2,
) -> str:
    """
    Format moneyness ratio (account value / benefit base).

    Moneyness interpretation:
    - > 1.0: In-The-Money (ITM) - account above benefit base
    - = 1.0: At-The-Money (ATM)
    - < 1.0: Out-Of-The-Money (OTM) - account below benefit base

    Args:
        value: Moneyness ratio (e.g., 1.286, 0.800)
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "1.29x ITM", "0.80x OTM", "1.00x ATM")

    Examples:
        >>> format_moneyness(1.286)
        '1.29x ITM'
        >>> format_moneyness(0.800)
        '0.80x OTM'
        >>> format_moneyness(1.0)
        '1.00x ATM'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return "N/A"

    format_spec = f":.{decimals}f"
    formatted_value = f"{value{format_spec}}"

    # Classify moneyness
    threshold = 0.02  # Allow ±2% for ATM
    if abs(value - 1.0) <= threshold:
        status = "ATM"
    elif value > 1.0:
        status = "ITM"
    else:
        status = "OTM"

    return f"{formatted_value}x {status}"


def format_greek(
    value: float,
    greek_name: str,
    decimals: int = 3,
) -> str:
    """
    Format Greeks values (Delta, Gamma, Vega, Theta, Rho).

    Args:
        value: Greek value
        greek_name: Name of Greek (Delta, Gamma, Vega, Theta, Rho)
        decimals: Number of decimal places

    Returns:
        Formatted Greek string with description

    Examples:
        >>> format_greek(0.73, "Delta")
        'Δ = 0.730 (73.0% price sensitivity)'
        >>> format_greek(0.285, "Vega")
        'ν = 0.285 (per 1% volatility change)'
        >>> format_greek(-1.20, "Theta")
        'Θ = -1.200 per day ($-1.20/day)'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return f"{greek_name} = N/A"

    format_spec = f":.{decimals}f"
    formatted_value = f"{value{format_spec}}"

    # Greek symbols and descriptions
    greek_info = {
        "Delta": ("Δ", "price sensitivity"),
        "Gamma": ("Γ", "delta sensitivity to price changes"),
        "Vega": ("ν", "per 1% volatility change"),
        "Theta": ("Θ", "per day (time decay)"),
        "Rho": ("ρ", "interest rate sensitivity"),
    }

    if greek_name in greek_info:
        symbol, description = greek_info[greek_name]
        return f"{symbol} = {formatted_value} ({description})"
    else:
        return f"{greek_name} = {formatted_value}"


def format_cte_metric(
    cte_value: float,
    mean_value: float,
    decimals: int = 0,
) -> str:
    """
    Format CTE70 reserve metric with comparison to mean.

    CTE70 = Conditional Tail Expectation at 70th percentile.
    Always >= mean by definition.

    Args:
        cte_value: CTE70 reserve amount
        mean_value: Mean reserve amount
        decimals: Number of decimal places for currency

    Returns:
        Formatted string showing both CTE70 and difference from mean

    Examples:
        >>> format_cte_metric(65000, 60000)
        'CTE70: $65,000 (8.3% above mean of $60,000)'
    """
    if not all(isinstance(v, (int, float)) for v in [cte_value, mean_value]):
        raise TypeError("Expected numeric values")

    if mean_value <= 0:
        return "CTE70: N/A (invalid mean)"

    cte_formatted = format_currency(cte_value, decimals=decimals)
    mean_formatted = format_currency(mean_value, decimals=decimals)
    pct_above = ((cte_value - mean_value) / mean_value) * 100

    return f"CTE70: {cte_formatted} ({pct_above:+.1f}% vs mean of {mean_formatted})"


def format_duration(
    years: float,
    decimals: int = 1,
) -> str:
    """
    Format duration in years with friendly description.

    Args:
        years: Duration in years
        decimals: Number of decimal places

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(25.3)
        '25.3 years'
        >>> format_duration(0.5)
        '6 months'
    """
    if not isinstance(years, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(years).__name__}")

    if years < 1:
        months = int(years * 12)
        return f"{months} months"

    format_spec = f":.{decimals}f"
    return f"{years{format_spec}} years"


def format_with_unit(
    value: float,
    unit: str,
    decimals: int = 2,
) -> str:
    """
    Format numeric value with arbitrary unit suffix.

    Args:
        value: Numeric value
        unit: Unit string (e.g., "years", "basis points", "%", "bp")
        decimals: Number of decimal places

    Returns:
        Formatted string with unit

    Examples:
        >>> format_with_unit(3.7, "years")
        '3.70 years'
        >>> format_with_unit(50, "bps")
        '50.00 bps'
        >>> format_with_unit(0.18, "%")
        '0.18%'
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(value).__name__}")

    if math.isnan(value) or math.isinf(value):
        return f"N/A {unit}"

    format_spec = f":.{decimals}f"
    formatted = f"{value{format_spec}}"

    # No space before % or bps suffix
    if unit in ["%", "bps"]:
        return f"{formatted}{unit}"
    else:
        return f"{formatted} {unit}"


def format_approval_decision(decision: str) -> str:
    """
    Format approval decision with emoji and styling hint.

    Args:
        decision: Decision code ("approve", "decline", "rate", "pending")

    Returns:
        Formatted decision string with emoji

    Examples:
        >>> format_approval_decision("approve")
        '✅ APPROVE'
        >>> format_approval_decision("decline")
        '❌ DECLINE'
    """
    decision_map = {
        "approve": "✅ APPROVE",
        "decline": "❌ DECLINE",
        "rate": "⚠️ RATE",
        "pending": "⏳ PENDING",
    }

    return decision_map.get(decision.lower(), f"❓ {decision.upper()}")


def format_risk_class(risk_class: str) -> str:
    """
    Format NAIC Model #908 risk classification.

    Args:
        risk_class: Risk class (Preferred, Standard, Rated, Decline)

    Returns:
        Formatted risk class with optional styling hint

    Examples:
        >>> format_risk_class("Preferred")
        '🟢 Preferred'
        >>> format_risk_class("Rated")
        '🟠 Rated'
    """
    risk_emoji = {
        "preferred": "🟢",
        "standard": "🟡",
        "rated": "🟠",
        "decline": "🔴",
    }

    class_name = risk_class.title()
    emoji = risk_emoji.get(risk_class.lower(), "⚪")
    return f"{emoji} {class_name}"


def format_confidence_score(
    confidence: float,
    decimals: int = 1,
    threshold_low: float = 0.70,
    threshold_high: float = 0.95,
) -> str:
    """
    Format confidence score (0-1) with interpretation.

    Args:
        confidence: Confidence value (0.0-1.0)
        decimals: Decimal places
        threshold_low: Threshold for "low confidence" flagging (default 0.70)
        threshold_high: Threshold for "high confidence" (default 0.95)

    Returns:
        Formatted confidence string with flag (e.g., "94.0% ✅ High")

    Examples:
        >>> format_confidence_score(0.94)
        '94.0% ✅ High'
        >>> format_confidence_score(0.65)
        '65.0% ⚠️ Low (manual review recommended)'
        >>> format_confidence_score(0.82)
        '82.0% ✓ Adequate'
    """
    if not isinstance(confidence, (int, float)):
        raise TypeError(f"Expected numeric value, got {type(confidence).__name__}")

    if not (0 <= confidence <= 1):
        raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")

    pct = confidence * 100
    format_spec = f":.{decimals}f"
    formatted = f"{pct{format_spec}}%"

    if confidence >= threshold_high:
        return f"{formatted} ✅ High"
    elif confidence >= threshold_low:
        return f"{formatted} ✓ Adequate"
    else:
        return f"{formatted} ⚠️ Low (manual review recommended)"


# Export public API
__all__ = [
    "format_currency",
    "format_percentage",
    "format_basis_points",
    "format_date",
    "format_moneyness",
    "format_greek",
    "format_cte_metric",
    "format_duration",
    "format_with_unit",
    "format_approval_decision",
    "format_risk_class",
    "format_confidence_score",
]
