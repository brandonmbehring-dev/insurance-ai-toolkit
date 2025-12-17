"""
Market Data Sidebar Widget for InsuranceAI Toolkit.

Displays live Treasury yields, S&P 500, VIX, and a mini yield curve chart
in the Streamlit sidebar.

Usage:
    from insurance_ai.web.components.market_data import render_market_sidebar

    with st.sidebar:
        render_market_sidebar()
"""

import streamlit as st

from insurance_ai.data.market_data import MarketData, get_market_snapshot
from insurance_ai.data.fred_client import clear_cache


def render_yield_curve_chart(market_data: MarketData) -> None:
    """
    Render a mini yield curve chart.

    Args:
        market_data: MarketData object with Treasury yields
    """
    import pandas as pd

    # Create dataframe for chart
    curve_data = pd.DataFrame(
        market_data.yield_curve,
        columns=["Tenor", "Yield"],
    )

    # Simple line chart
    st.line_chart(
        curve_data.set_index("Tenor"),
        height=150,
        use_container_width=True,
    )


def render_market_sidebar() -> None:
    """
    Render the complete market data sidebar widget.

    Displays:
    - Data source badge (Live/Cached)
    - Treasury yield curve chart
    - Key Treasury rates (2Y, 10Y, 30Y)
    - Fed Funds rate
    - S&P 500 and VIX indices
    - Refresh button
    """
    st.markdown("#### 📈 Market Data")

    # Fetch market data
    try:
        market = get_market_snapshot()
    except Exception as e:
        st.error(f"Error fetching market data: {e}")
        return

    # Data source badge
    st.caption(market.source_badge)

    # Yield curve chart
    st.markdown("**Treasury Yield Curve**")
    render_yield_curve_chart(market)

    # Curve slope indicator
    slope = market.curve_slope_2_10
    if market.is_inverted:
        st.warning(f"⚠️ Inverted: 2Y-10Y = {slope:+.2f}%")
    else:
        st.caption(f"2Y-10Y spread: {slope:+.2f}%")

    # Key rates in compact format
    st.markdown("**Key Rates**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("2Y", f"{market.treasury_2y:.2f}%", label_visibility="visible")
    with col2:
        st.metric("10Y", f"{market.treasury_10y:.2f}%", label_visibility="visible")
    with col3:
        st.metric("30Y", f"{market.treasury_30y:.2f}%", label_visibility="visible")

    # Fed Funds
    st.caption(f"Fed Funds: {market.fed_funds:.2f}%")

    st.markdown("---")

    # Market indices
    st.markdown("**Market Indices**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("S&P 500", f"{market.sp500:,.0f}")
    with col2:
        # Color-coded VIX
        vix_color = (
            "🟢" if market.vix < 15
            else "🟡" if market.vix < 25
            else "🔴"
        )
        st.metric("VIX", f"{vix_color} {market.vix:.1f}")

    st.caption(f"Volatility: {market.vix_level}")

    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_market"):
        clear_cache()
        st.rerun()

    # Attribution (required for VIX)
    st.caption("Data: FRED (St. Louis Fed)")
