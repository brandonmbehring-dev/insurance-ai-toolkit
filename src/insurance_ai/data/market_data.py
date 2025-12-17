"""
Market Data Service for InsuranceAI Toolkit.

High-level service that combines FRED data into structured formats
for display in the web UI.

Usage:
    from insurance_ai.data.market_data import get_market_snapshot

    snapshot = get_market_snapshot()
    print(f"10Y Treasury: {snapshot.treasury_10y}%")
    print(f"S&P 500: {snapshot.sp500:,.0f}")
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

from .fred_client import (
    fetch_fed_funds_rate,
    fetch_market_indices,
    fetch_treasury_yields,
    get_all_market_data,
)


@dataclass
class MarketData:
    """Structured market data snapshot."""

    # Treasury yields
    treasury_1y: float
    treasury_2y: float
    treasury_5y: float
    treasury_10y: float
    treasury_30y: float

    # Fed Funds
    fed_funds: float

    # Market indices
    sp500: float
    vix: float

    # Metadata
    is_live: bool
    timestamp: datetime

    @property
    def yield_curve(self) -> List[Tuple[str, float]]:
        """Return yield curve as ordered list of (tenor, yield) tuples."""
        return [
            ("1Y", self.treasury_1y),
            ("2Y", self.treasury_2y),
            ("5Y", self.treasury_5y),
            ("10Y", self.treasury_10y),
            ("30Y", self.treasury_30y),
        ]

    @property
    def curve_slope_2_10(self) -> float:
        """10Y - 2Y spread (classic curve slope indicator)."""
        return self.treasury_10y - self.treasury_2y

    @property
    def is_inverted(self) -> bool:
        """True if 2Y-10Y spread is negative (inverted yield curve)."""
        return self.curve_slope_2_10 < 0

    @property
    def vix_level(self) -> str:
        """Interpret VIX level."""
        if self.vix < 12:
            return "Very Low"
        elif self.vix < 20:
            return "Low"
        elif self.vix < 30:
            return "Elevated"
        else:
            return "High"

    @property
    def source_badge(self) -> str:
        """Return badge text for data source."""
        if self.is_live:
            return f"🟢 Live {self.timestamp.strftime('%H:%M')}"
        else:
            return f"📊 Cached {self.timestamp.strftime('%Y-%m-%d')}"


def get_market_snapshot() -> MarketData:
    """
    Get a complete market data snapshot.

    Returns:
        MarketData object with all current market values
    """
    data = get_all_market_data()
    yields = data["treasury_yields"]
    indices = data["indices"]

    return MarketData(
        treasury_1y=yields.get("1Y", 0.0),
        treasury_2y=yields.get("2Y", 0.0),
        treasury_5y=yields.get("5Y", 0.0),
        treasury_10y=yields.get("10Y", 0.0),
        treasury_30y=yields.get("30Y", 0.0),
        fed_funds=data["fed_funds"],
        sp500=indices.get("SP500", 0.0),
        vix=indices.get("VIX", 0.0),
        is_live=data["is_live"],
        timestamp=data["timestamp"],
    )


def get_treasury_curve_data() -> List[Tuple[str, float]]:
    """
    Get treasury yield curve data for charting.

    Returns:
        List of (tenor_label, yield) tuples ordered by maturity
    """
    yields = fetch_treasury_yields()
    return [
        ("1Y", yields.get("1Y", 0.0)),
        ("2Y", yields.get("2Y", 0.0)),
        ("5Y", yields.get("5Y", 0.0)),
        ("10Y", yields.get("10Y", 0.0)),
        ("30Y", yields.get("30Y", 0.0)),
    ]


def format_rate(rate: float) -> str:
    """Format rate for display (e.g., 4.25 -> '4.25%')."""
    return f"{rate:.2f}%"


def format_index(value: float) -> str:
    """Format index value for display (e.g., 5950.5 -> '5,950.50')."""
    return f"{value:,.2f}"
