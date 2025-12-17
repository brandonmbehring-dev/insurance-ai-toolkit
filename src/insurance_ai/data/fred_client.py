"""
FRED API Client for InsuranceAI Toolkit.

Fetches market data from Federal Reserve Economic Data (FRED):
- Treasury yields (1Y, 2Y, 5Y, 10Y, 30Y)
- Fed Funds rate
- S&P 500 index
- VIX volatility index

Usage:
    from insurance_ai.data.fred_client import fetch_treasury_yields, fetch_market_indices

    yields = fetch_treasury_yields()  # {'1Y': 4.5, '2Y': 4.2, ...}
    indices = fetch_market_indices()  # {'SP500': 4500.0, 'VIX': 15.2}
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import streamlit as st

# FRED series IDs
TREASURY_SERIES = {
    "1Y": "DGS1",
    "2Y": "DGS2",
    "5Y": "DGS5",
    "10Y": "DGS10",
    "30Y": "DGS30",
}

FED_FUNDS_SERIES = "FEDFUNDS"

MARKET_SERIES = {
    "SP500": "SP500",
    "VIX": "VIXCLS",
}

# Fixture data for fallback (realistic values as of late 2024)
FIXTURE_TREASURY_YIELDS = {
    "1Y": 4.85,
    "2Y": 4.42,
    "5Y": 4.15,
    "10Y": 4.28,
    "30Y": 4.52,
}

FIXTURE_FED_FUNDS = 5.33

FIXTURE_MARKET_INDICES = {
    "SP500": 5950.0,
    "VIX": 14.5,
}


@dataclass
class FREDClient:
    """FRED API client wrapper with caching and fallback."""

    api_key: Optional[str] = None
    _fred: Optional[Any] = None

    def __post_init__(self) -> None:
        """Initialize FRED client if API key is available."""
        self.api_key = self._get_api_key()
        if self.api_key:
            try:
                from fredapi import Fred

                self._fred = Fred(api_key=self.api_key)
            except ImportError:
                self._fred = None
            except Exception:
                self._fred = None

    def _get_api_key(self) -> Optional[str]:
        """Get FRED API key from Streamlit secrets or environment."""
        # Try Streamlit secrets first
        try:
            return st.secrets.get("FRED_API_KEY")
        except Exception:
            pass

        # Fall back to environment variable
        return os.getenv("FRED_API_KEY")

    @property
    def is_available(self) -> bool:
        """Check if FRED client is available."""
        return self._fred is not None

    def fetch_series_latest(self, series_id: str) -> Optional[float]:
        """
        Fetch the latest value for a FRED series.

        Args:
            series_id: FRED series identifier (e.g., 'DGS10')

        Returns:
            Latest value or None if fetch fails
        """
        if not self.is_available:
            return None

        try:
            # Fetch last 30 days to ensure we get a recent value
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            series = self._fred.get_series(
                series_id,
                observation_start=start_date.strftime("%Y-%m-%d"),
                observation_end=end_date.strftime("%Y-%m-%d"),
            )

            if series is not None and len(series) > 0:
                # Get most recent non-NaN value
                valid_values = series.dropna()
                if len(valid_values) > 0:
                    return float(valid_values.iloc[-1])

            return None

        except Exception:
            return None


# Module-level client instance (lazy initialization)
_client: Optional[FREDClient] = None


def _get_client() -> FREDClient:
    """Get or create the FRED client singleton."""
    global _client
    if _client is None:
        _client = FREDClient()
    return _client


@st.cache_data(ttl=86400)  # 24-hour cache for Treasury/Fed Funds
def fetch_treasury_yields() -> Dict[str, float]:
    """
    Fetch current Treasury yields from FRED.

    Returns:
        Dict with keys '1Y', '2Y', '5Y', '10Y', '30Y' and yield values
        Falls back to fixture data if API unavailable
    """
    client = _get_client()

    if not client.is_available:
        return FIXTURE_TREASURY_YIELDS.copy()

    yields = {}
    for label, series_id in TREASURY_SERIES.items():
        value = client.fetch_series_latest(series_id)
        yields[label] = value if value is not None else FIXTURE_TREASURY_YIELDS[label]

    return yields


@st.cache_data(ttl=86400)  # 24-hour cache
def fetch_fed_funds_rate() -> float:
    """
    Fetch current Fed Funds rate from FRED.

    Returns:
        Fed Funds rate as float, falls back to fixture if unavailable
    """
    client = _get_client()

    if not client.is_available:
        return FIXTURE_FED_FUNDS

    value = client.fetch_series_latest(FED_FUNDS_SERIES)
    return value if value is not None else FIXTURE_FED_FUNDS


@st.cache_data(ttl=14400)  # 4-hour cache for indices (more volatile)
def fetch_market_indices() -> Dict[str, float]:
    """
    Fetch S&P 500 and VIX from FRED.

    Returns:
        Dict with 'SP500' and 'VIX' values
        Falls back to fixture data if API unavailable
    """
    client = _get_client()

    if not client.is_available:
        return FIXTURE_MARKET_INDICES.copy()

    indices = {}
    for label, series_id in MARKET_SERIES.items():
        value = client.fetch_series_latest(series_id)
        indices[label] = value if value is not None else FIXTURE_MARKET_INDICES[label]

    return indices


def get_all_market_data() -> Dict[str, Any]:
    """
    Fetch all market data in one call.

    Returns:
        Dict containing:
        - treasury_yields: Dict[str, float]
        - fed_funds: float
        - indices: Dict[str, float]
        - is_live: bool (True if fetched from API, False if using fixtures)
        - timestamp: datetime
    """
    client = _get_client()
    is_live = client.is_available

    return {
        "treasury_yields": fetch_treasury_yields(),
        "fed_funds": fetch_fed_funds_rate(),
        "indices": fetch_market_indices(),
        "is_live": is_live,
        "timestamp": datetime.now(),
    }


def clear_cache() -> None:
    """Clear all cached market data (for manual refresh)."""
    fetch_treasury_yields.clear()
    fetch_fed_funds_rate.clear()
    fetch_market_indices.clear()
