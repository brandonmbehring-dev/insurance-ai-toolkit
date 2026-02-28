"""
Custom Scenario Builder Component for Streamlit UI.

Provides interactive stress testing interface:
- Parameter sliders for equity, rate, vol, and lapse shocks
- Side-by-side base vs stressed results comparison
- Delta columns showing impact of each stress
- Charts comparing distributions

Usage:
    from insurance_ai.web.components.scenario_builder import (
        render_scenario_builder,
        apply_stress_scenario,
    )
"""

from dataclasses import dataclass
from typing import Any

import streamlit as st

# Default base scenario parameters
DEFAULT_BASE_SCENARIO = {
    "equity_return": 0.07,  # 7% annual return
    "interest_rate": 0.04,  # 4% risk-free rate
    "volatility": 0.20,  # 20% implied vol
    "lapse_multiplier": 1.0,  # Base lapse rates
    "account_value": 350000,
    "benefit_base": 350000,
}


@dataclass
class ScenarioParameters:
    """Parameters defining a stress scenario."""

    equity_shock_pct: float  # e.g., -30 means -30% equity shock
    rate_shock_bps: int  # e.g., -200 means -200 basis points
    vol_shock_pct: float  # e.g., +50 means +50% vol increase
    lapse_multiplier: float  # e.g., 1.5 means 50% higher lapse

    @property
    def label(self) -> str:
        """Human-readable scenario label."""
        parts = []
        if self.equity_shock_pct != 0:
            parts.append(f"Eq {self.equity_shock_pct:+.0f}%")
        if self.rate_shock_bps != 0:
            parts.append(f"Rate {self.rate_shock_bps:+d}bps")
        if self.vol_shock_pct != 0:
            parts.append(f"Vol {self.vol_shock_pct:+.0f}%")
        if self.lapse_multiplier != 1.0:
            parts.append(f"Lapse {self.lapse_multiplier:.1f}x")
        return " | ".join(parts) if parts else "Base Case"


# Preset scenarios for quick selection
PRESET_SCENARIOS = {
    "Base Case": ScenarioParameters(0, 0, 0, 1.0),
    "2008 Crisis": ScenarioParameters(-40, -200, +80, 1.5),
    "March 2020": ScenarioParameters(-35, -150, +100, 1.3),
    "Rising Rates": ScenarioParameters(-10, +200, +20, 1.1),
    "Prolonged Low Rates": ScenarioParameters(+5, -100, -10, 0.9),
    "Vol Spike": ScenarioParameters(-15, 0, +100, 1.2),
    "Favorable": ScenarioParameters(+15, +50, -20, 0.8),
}


def calculate_moneyness(account_value: float, benefit_base: float) -> float:
    """Calculate moneyness (AV / BB)."""
    if benefit_base <= 0:
        return 1.0
    return account_value / benefit_base


def calculate_dynamic_lapse_rate(
    moneyness: float,
    base_rate: float = 0.08,
    lapse_multiplier: float = 1.0,
) -> float:
    """
    Calculate dynamic lapse rate with stress multiplier.

    Args:
        moneyness: Account Value / Benefit Base ratio
        base_rate: Base annual lapse rate
        lapse_multiplier: Stress multiplier for lapse rates

    Returns:
        Dynamic lapse rate after stress
    """
    if moneyness > 1.1:
        rate = max(0.02, base_rate * 0.4)
    elif moneyness < 0.9:
        rate = min(0.25, base_rate * 2.5)
    else:
        rate = base_rate

    return min(0.50, rate * lapse_multiplier)  # Cap at 50%


def calculate_cte70_reserve(
    account_value: float,
    benefit_base: float,
    age: int,
    volatility: float = 0.20,
    interest_rate: float = 0.04,
) -> float:
    """
    Simplified CTE70 reserve with vol and rate sensitivity.

    Higher vol → higher reserve (more option value)
    Lower rates → higher reserve (longer duration)
    """
    moneyness = calculate_moneyness(account_value, benefit_base)

    # Base reserve factor by moneyness
    if moneyness > 1.1:
        base_factor = 0.12
    elif moneyness < 0.9:
        base_factor = 0.22
    else:
        base_factor = 0.17

    # Volatility adjustment: +10% vol → +15% reserve
    vol_adjustment = 1.0 + (volatility - 0.20) * 1.5

    # Rate adjustment: -100bps → +8% reserve
    rate_adjustment = 1.0 + (0.04 - interest_rate) * 2.0

    # Age adjustment
    age_factor = 1.0 + max(0, (age - 60)) * 0.02

    return benefit_base * base_factor * vol_adjustment * rate_adjustment * age_factor


def apply_equity_shock(account_value: float, shock_pct: float) -> float:
    """Apply equity shock to account value."""
    return account_value * (1 + shock_pct / 100)


def apply_stress_scenario(
    base_scenario: dict[str, Any],
    stress: ScenarioParameters,
    age: int = 65,
) -> dict[str, Any]:
    """
    Apply stress scenario to base case and calculate all metrics.

    Args:
        base_scenario: Dictionary with base scenario parameters
        stress: ScenarioParameters defining the stress
        age: Policyholder age for reserve calculation

    Returns:
        Dictionary with stressed metrics
    """
    # Apply shocks
    stressed_av = apply_equity_shock(
        base_scenario["account_value"],
        stress.equity_shock_pct,
    )
    stressed_rate = base_scenario["interest_rate"] + (stress.rate_shock_bps / 10000)
    stressed_vol = base_scenario["volatility"] * (1 + stress.vol_shock_pct / 100)

    moneyness = calculate_moneyness(stressed_av, base_scenario["benefit_base"])
    lapse_rate = calculate_dynamic_lapse_rate(
        moneyness,
        base_rate=0.08,
        lapse_multiplier=stress.lapse_multiplier,
    )
    cte70 = calculate_cte70_reserve(
        stressed_av,
        base_scenario["benefit_base"],
        age,
        volatility=stressed_vol,
        interest_rate=stressed_rate,
    )

    return {
        "scenario_label": stress.label,
        "account_value": stressed_av,
        "benefit_base": base_scenario["benefit_base"],
        "interest_rate": stressed_rate,
        "volatility": stressed_vol,
        "moneyness": moneyness,
        "dynamic_lapse_rate": lapse_rate,
        "cte70_reserve": cte70,
        "reserve_ratio": cte70 / stressed_av if stressed_av > 0 else 0,
        "equity_shock_pct": stress.equity_shock_pct,
        "rate_shock_bps": stress.rate_shock_bps,
        "vol_shock_pct": stress.vol_shock_pct,
        "lapse_multiplier": stress.lapse_multiplier,
    }


def calculate_delta(base_value: float, stressed_value: float) -> tuple[float, str]:
    """
    Calculate delta and format for display.

    Returns:
        Tuple of (delta_pct, formatted_string)
    """
    if base_value == 0:
        return 0, "N/A"
    delta_pct = (stressed_value - base_value) / base_value * 100
    return delta_pct, f"{delta_pct:+.1f}%"


def render_scenario_builder() -> dict[str, Any] | None:
    """
    Render custom scenario builder UI with sliders and presets.

    Returns:
        Dictionary with stressed scenario results, or None if not yet configured
    """
    st.markdown("## Custom Scenario Builder")
    st.markdown("""
    Define custom stress tests to understand reserve sensitivity.
    Adjust parameters below or select a preset scenario.
    """)

    # Preset selector
    col1, col2 = st.columns([3, 1])
    with col1:
        preset_name = st.selectbox(
            "Quick Presets",
            options=list(PRESET_SCENARIOS.keys()),
            index=0,
            help="Select a predefined stress scenario",
        )
    with col2:
        apply_preset = st.button("Apply Preset", use_container_width=True)

    # Initialize or load current stress parameters
    if "custom_stress" not in st.session_state:
        st.session_state["custom_stress"] = PRESET_SCENARIOS["Base Case"]

    if apply_preset:
        st.session_state["custom_stress"] = PRESET_SCENARIOS[preset_name]

    current_stress = st.session_state["custom_stress"]

    # Stress parameter sliders
    st.markdown("### Stress Parameters")

    col1, col2 = st.columns(2)

    with col1:
        equity_shock = st.slider(
            "Equity Shock (%)",
            min_value=-50,
            max_value=50,
            value=int(current_stress.equity_shock_pct),
            step=5,
            help="Immediate shock to account value. -40% simulates 2008 crisis.",
        )

        rate_shock = st.slider(
            "Rate Shock (bps)",
            min_value=-300,
            max_value=300,
            value=int(current_stress.rate_shock_bps),
            step=25,
            help="Parallel shift in interest rates. -200bps simulates Fed cuts.",
        )

    with col2:
        vol_shock = st.slider(
            "Volatility Shock (%)",
            min_value=-50,
            max_value=150,
            value=int(current_stress.vol_shock_pct),
            step=10,
            help="Change in implied volatility. +100% simulates VIX spike.",
        )

        lapse_mult = st.slider(
            "Lapse Multiplier",
            min_value=0.5,
            max_value=2.5,
            value=float(current_stress.lapse_multiplier),
            step=0.1,
            help="Multiplier on dynamic lapse rates. 1.5x = 50% higher lapse.",
        )

    # Update stored stress parameters
    new_stress = ScenarioParameters(
        equity_shock_pct=equity_shock,
        rate_shock_bps=rate_shock,
        vol_shock_pct=vol_shock,
        lapse_multiplier=lapse_mult,
    )
    st.session_state["custom_stress"] = new_stress

    # Base scenario inputs
    st.markdown("### Base Scenario")

    col1, col2, col3 = st.columns(3)
    with col1:
        base_av = st.number_input(
            "Account Value ($)",
            min_value=10000,
            max_value=5000000,
            value=350000,
            step=10000,
        )
    with col2:
        base_bb = st.number_input(
            "Benefit Base ($)",
            min_value=10000,
            max_value=5000000,
            value=350000,
            step=10000,
        )
    with col3:
        age = st.number_input(
            "Policyholder Age",
            min_value=40,
            max_value=90,
            value=65,
            step=1,
        )

    # Build base scenario
    base_scenario = {
        **DEFAULT_BASE_SCENARIO,
        "account_value": base_av,
        "benefit_base": base_bb,
    }

    # Calculate base and stressed results
    base_result = apply_stress_scenario(
        base_scenario,
        ScenarioParameters(0, 0, 0, 1.0),
        age=age,
    )
    stressed_result = apply_stress_scenario(
        base_scenario,
        new_stress,
        age=age,
    )

    # Results comparison
    st.markdown("---")
    st.markdown("## Results Comparison")
    st.markdown(f"**Stress Applied:** {new_stress.label}")

    # Key metrics comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Base Case")
        st.metric("Account Value", f"${base_result['account_value']:,.0f}")
        st.metric("CTE70 Reserve", f"${base_result['cte70_reserve']:,.0f}")
        st.metric("Reserve Ratio", f"{base_result['reserve_ratio']:.1%}")
        st.metric("Moneyness", f"{base_result['moneyness']:.3f}")
        st.metric("Dynamic Lapse", f"{base_result['dynamic_lapse_rate']:.2%}")

    with col2:
        st.markdown("### Stressed")
        _, av_delta = calculate_delta(
            base_result["account_value"], stressed_result["account_value"]
        )
        st.metric(
            "Account Value",
            f"${stressed_result['account_value']:,.0f}",
            av_delta,
        )
        _, res_delta = calculate_delta(
            base_result["cte70_reserve"], stressed_result["cte70_reserve"]
        )
        st.metric(
            "CTE70 Reserve",
            f"${stressed_result['cte70_reserve']:,.0f}",
            res_delta,
        )
        _, ratio_delta = calculate_delta(
            base_result["reserve_ratio"], stressed_result["reserve_ratio"]
        )
        st.metric(
            "Reserve Ratio",
            f"{stressed_result['reserve_ratio']:.1%}",
            ratio_delta,
        )
        _, mon_delta = calculate_delta(base_result["moneyness"], stressed_result["moneyness"])
        st.metric(
            "Moneyness",
            f"{stressed_result['moneyness']:.3f}",
            mon_delta,
        )
        _, lapse_delta = calculate_delta(
            base_result["dynamic_lapse_rate"], stressed_result["dynamic_lapse_rate"]
        )
        st.metric(
            "Dynamic Lapse",
            f"{stressed_result['dynamic_lapse_rate']:.2%}",
            lapse_delta,
        )

    with col3:
        st.markdown("### Delta Impact")
        av_pct, _ = calculate_delta(base_result["account_value"], stressed_result["account_value"])
        st.metric("AV Change", f"{av_pct:+.1f}%")

        res_pct, _ = calculate_delta(base_result["cte70_reserve"], stressed_result["cte70_reserve"])
        st.metric("Reserve Change", f"{res_pct:+.1f}%")

        # Capital impact
        capital_impact = stressed_result["cte70_reserve"] - base_result["cte70_reserve"]
        st.metric(
            "Additional Capital",
            f"${capital_impact:+,.0f}",
            "Required" if capital_impact > 0 else "Released",
        )

    # Store results for export
    st.session_state["scenario_base"] = base_result
    st.session_state["scenario_stressed"] = stressed_result

    # Sensitivity insights
    st.markdown("---")
    st.markdown("### Sensitivity Insights")

    insights = []

    # Reserve sensitivity
    res_pct, _ = calculate_delta(base_result["cte70_reserve"], stressed_result["cte70_reserve"])
    if abs(res_pct) > 20:
        insights.append(
            f"Reserve change of {res_pct:+.1f}% indicates **high sensitivity** to this stress combination."
        )

    # Vol sensitivity
    if new_stress.vol_shock_pct != 0:
        (stressed_result["volatility"] - base_result["volatility"]) / base_result["volatility"]
        insights.append(
            f"Volatility moved from {base_result['volatility']:.0%} to {stressed_result['volatility']:.0%}."
        )

    # Moneyness shift
    if stressed_result["moneyness"] < 0.9 and base_result["moneyness"] >= 0.9:
        insights.append(
            "Scenario pushes policy **out-of-the-money** (moneyness < 0.9), significantly increasing lapse risk."
        )
    elif stressed_result["moneyness"] > 1.1 and base_result["moneyness"] <= 1.1:
        insights.append(
            "Scenario pushes policy **deep-in-the-money** (moneyness > 1.1), reducing lapse risk."
        )

    # Lapse rate warning
    if stressed_result["dynamic_lapse_rate"] > 0.20:
        insights.append(
            f"Dynamic lapse rate of {stressed_result['dynamic_lapse_rate']:.1%} exceeds 20% threshold — significant persistency risk."
        )

    if insights:
        for insight in insights:
            st.info(insight)
    else:
        st.success("Stress parameters within normal sensitivity ranges.")

    return stressed_result


def render_scenario_builder_mini() -> None:
    """
    Render compact scenario builder widget for sidebar.

    Shows current stress parameters and quick preset selector.
    """
    st.markdown("### Quick Stress Test")

    preset = st.selectbox(
        "Scenario",
        options=list(PRESET_SCENARIOS.keys()),
        index=0,
        key="sidebar_scenario_preset",
    )

    if st.button("Apply", key="sidebar_apply_stress", use_container_width=True):
        st.session_state["custom_stress"] = PRESET_SCENARIOS[preset]
        st.info(f"Applied: {preset}")

    # Show current stress if set
    if "custom_stress" in st.session_state:
        stress = st.session_state["custom_stress"]
        if stress.label != "Base Case":
            st.caption(f"Current: {stress.label}")
