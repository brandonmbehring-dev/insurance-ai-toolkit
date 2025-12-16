"""
Plotly chart components for Streamlit.

Reusable chart functions with Guardian branding and styling.
All charts cached with @st.cache_resource for performance.
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Tuple

from ..config import GuardianTheme


# ===== COLOR SCHEME =====

def get_guardian_colors():
    """Return Guardian-branded color palette."""
    return {
        "primary": GuardianTheme.PRIMARY_BLUE,
        "secondary": GuardianTheme.SECONDARY_BLUE,
        "accent": GuardianTheme.ACCENT_GOLD,
        "success": GuardianTheme.SUCCESS,
        "warning": GuardianTheme.WARNING,
        "error": GuardianTheme.ERROR,
    }


# ===== CTE70 HISTOGRAM =====

@st.cache_resource
def plot_cte70_histogram(
    simulated_values: List[float],
    cte70_value: float,
    mean_value: float,
    title: str = "CTE70 Reserve Distribution",
) -> go.Figure:
    """
    Plot CTE70 distribution histogram with percentile lines.

    Args:
        simulated_values: List of simulated reserve values (Monte Carlo output)
        cte70_value: CTE70 (70th percentile) reserve value
        mean_value: Mean reserve value
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure()

    # Histogram
    fig.add_trace(
        go.Histogram(
            x=simulated_values,
            nbinsx=30,
            name="Distribution",
            marker_color=colors["primary"],
            marker_line_color="white",
            marker_line_width=1,
        )
    )

    # CTE70 line
    fig.add_vline(
        x=cte70_value,
        line_dash="solid",
        line_color=colors["error"],
        annotation_text=f"CTE70: ${cte70_value:,.0f}",
        annotation_position="top right",
        name="CTE70 (70th percentile)",
    )

    # Mean line
    fig.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color=colors["success"],
        annotation_text=f"Mean: ${mean_value:,.0f}",
        annotation_position="top left",
        name="Mean Reserve",
    )

    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Reserve Amount ($)",
        yaxis_title="Frequency",
        barmode="overlay",
        hovermode="x unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== SENSITIVITY TORNADO CHART =====

@st.cache_resource
def plot_sensitivity_tornado(
    drivers: Dict[str, Tuple[float, float]],
    baseline: float,
    title: str = "Reserve Sensitivity Analysis",
) -> go.Figure:
    """
    Plot tornado chart showing sensitivity to parameter changes.

    Args:
        drivers: Dict of {driver_name: (low_value, high_value)}
                e.g., {"Rate Shock": (0.08, 0.12), ...}
        baseline: Baseline reserve value
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    driver_names = list(drivers.keys())
    low_impacts = []
    high_impacts = []

    for low, high in drivers.values():
        low_impacts.append(low - baseline)
        high_impacts.append(high - baseline)

    fig = go.Figure()

    # Negative impacts (left)
    fig.add_trace(
        go.Bar(
            y=driver_names,
            x=low_impacts,
            name="Low Impact",
            marker_color=colors["success"],
            orientation="h",
        )
    )

    # Positive impacts (right)
    fig.add_trace(
        go.Bar(
            y=driver_names,
            x=high_impacts,
            name="High Impact",
            marker_color=colors["error"],
            orientation="h",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Reserve Change ($)",
        barmode="relative",
        hovermode="y unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== LAPSE CURVE (MONEYNESS) =====

@st.cache_resource
def plot_lapse_curve(
    moneyness_values: List[float],
    lapse_rates: List[float],
    current_moneyness: float = None,
    title: str = "Dynamic Lapse Rate by Moneyness",
) -> go.Figure:
    """
    Plot lapse rate vs moneyness curve.

    Shows relationship between account value and surrender rates.

    Args:
        moneyness_values: List of moneyness ratios (account/benefit)
        lapse_rates: Corresponding lapse rates
        current_moneyness: Current scenario's moneyness (highlighted)
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure()

    # Curve
    fig.add_trace(
        go.Scatter(
            x=moneyness_values,
            y=[r * 100 for r in lapse_rates],  # Convert to percentage
            mode="lines+markers",
            name="Lapse Rate",
            line=dict(color=colors["primary"], width=3),
            marker=dict(size=8),
        )
    )

    # Current point
    if current_moneyness is not None:
        # Interpolate current lapse rate
        current_lapse = np.interp(current_moneyness, moneyness_values, lapse_rates)
        fig.add_trace(
            go.Scatter(
                x=[current_moneyness],
                y=[current_lapse * 100],
                mode="markers",
                name="Current Scenario",
                marker=dict(size=15, color=colors["accent"]),
            )
        )

    # Reference zones
    fig.add_hline(
        y=6,
        line_dash="dash",
        line_color="gray",
        annotation_text="ATM baseline (1.0 moneyness)",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Moneyness (Account Value / Benefit Base)",
        yaxis_title="Lapse Rate (%)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== CONVERGENCE GRAPH =====

@st.cache_resource
def plot_convergence(
    scenario_counts: List[int],
    cte70_values: List[float],
    title: str = "Reserve Convergence (Monte Carlo Stability)",
) -> go.Figure:
    """
    Plot CTE70 convergence as number of scenarios increases.

    Shows stability of reserve estimate.

    Args:
        scenario_counts: List of scenario counts (e.g., [100, 500, 1000])
        cte70_values: Corresponding CTE70 values
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=scenario_counts,
            y=cte70_values,
            mode="lines+markers",
            name="CTE70 Estimate",
            line=dict(color=colors["primary"], width=3),
            marker=dict(size=10),
        )
    )

    # Convergence band (±2%)
    if cte70_values:
        final_value = cte70_values[-1]
        upper_band = [v * 1.02 for v in cte70_values]
        lower_band = [v * 0.98 for v in cte70_values]

        fig.add_trace(
            go.Scatter(
                x=scenario_counts + scenario_counts[::-1],
                y=upper_band + lower_band[::-1],
                fill="toself",
                fillcolor="rgba(0, 61, 165, 0.1)",
                line=dict(color="rgba(255, 255, 255, 0)"),
                name="±2% Convergence Band",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Number of Monte Carlo Scenarios",
        yaxis_title="CTE70 Reserve ($)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== GREEK HEATMAP =====

@st.cache_resource
def plot_greek_heatmap(
    underlying_prices: List[float],
    volatilities: List[float],
    greek_matrix: np.ndarray,
    greek_name: str = "Delta",
    title: str = "Greeks Sensitivity Surface",
) -> go.Figure:
    """
    Plot heatmap of Greek value across price and vol dimensions.

    Args:
        underlying_prices: Price range (e.g., -20% to +20% from spot)
        volatilities: Volatility range (e.g., 12% to 24%)
        greek_matrix: 2D array of Greek values
        greek_name: Name of Greek (Delta, Vega, etc.)
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure(
        data=go.Heatmap(
            z=greek_matrix,
            x=volatilities,
            y=underlying_prices,
            colorscale="RdYlGn",
            name=greek_name,
            colorbar=dict(title=greek_name),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Volatility (%)",
        yaxis_title="Underlying Price (%)",
        template="plotly_white",
        height=500,
    )

    return fig


# ===== SCENARIO COMPARISON BOX PLOT =====

@st.cache_resource
def plot_scenario_comparison(
    scenarios: Dict[str, List[float]],
    title: str = "Scenario Comparison: Reserve Distribution",
) -> go.Figure:
    """
    Plot box plot comparing distributions across scenarios.

    Args:
        scenarios: Dict of {scenario_name: [values]}
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure()

    for scenario_name, values in scenarios.items():
        fig.add_trace(
            go.Box(
                y=values,
                name=scenario_name,
                marker_color=colors["primary"],
            )
        )

    fig.update_layout(
        title=title,
        yaxis_title="Reserve Amount ($)",
        boxmode="group",
        hovermode="y unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== PAYOFF DIAGRAM =====

@st.cache_resource
def plot_payoff_diagram(
    underlying_prices: List[float],
    unhedged_pnl: List[float],
    hedged_pnl: List[float],
    title: str = "P&L Payoff Diagram",
) -> go.Figure:
    """
    Plot payoff diagram comparing unhedged vs hedged portfolio P&L.

    Args:
        underlying_prices: List of underlying price levels
        unhedged_pnl: P&L for unhedged portfolio
        hedged_pnl: P&L for hedged portfolio
        title: Chart title

    Returns:
        Plotly Figure
    """
    colors = get_guardian_colors()

    fig = go.Figure()

    # Unhedged P&L line
    fig.add_trace(
        go.Scatter(
            x=underlying_prices,
            y=unhedged_pnl,
            mode="lines",
            name="Unhedged",
            line=dict(color=colors["error"], width=3),
        )
    )

    # Hedged P&L line
    fig.add_trace(
        go.Scatter(
            x=underlying_prices,
            y=hedged_pnl,
            mode="lines",
            name="Hedged",
            line=dict(color=colors["success"], width=3),
        )
    )

    # Break-even line (P&L = 0)
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Break-even",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Underlying Price",
        yaxis_title="Portfolio P&L ($)",
        hovermode="x unified",
        template="plotly_white",
        height=400,
    )

    return fig


# ===== BASIC METRICS DISPLAY =====

def display_metric_row(metrics: Dict[str, Tuple[str, str]]) -> None:
    """
    Display a row of metrics with values and deltas.

    Args:
        metrics: Dict of {metric_name: (value, delta)}
               e.g., {"CTE70": ("$450K", "+$25K")}
    """
    cols = st.columns(len(metrics))

    for col, (metric_name, (value, delta)) in zip(cols, metrics.items()):
        with col:
            st.metric(metric_name, value, delta=delta)
