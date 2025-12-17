"""
InsuranceAI Toolkit - Market Data Module

FRED API integration for live market data: Treasury yields, S&P 500, VIX.
"""

from .fred_client import (
    FREDClient,
    fetch_treasury_yields,
    fetch_market_indices,
    get_all_market_data,
)
from .market_data import (
    MarketData,
    get_market_snapshot,
    get_treasury_curve_data,
)

__all__ = [
    # FRED client
    "FREDClient",
    "fetch_treasury_yields",
    "fetch_market_indices",
    "get_all_market_data",
    # Market data service
    "MarketData",
    "get_market_snapshot",
    "get_treasury_curve_data",
]
