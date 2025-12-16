"""
Form Input Components for Streamlit UI.

Reusable form components with consistent Guardian branding and styling.
Wraps Streamlit input methods with custom defaults and layouts.

Usage:
    scenario = scenario_selector()
    account_value = currency_slider("Account Value", 100, 1000, 350)
"""

from typing import List, Dict, Optional, Tuple
import streamlit as st


def scenario_selector(
    default_scenario: str = "001_itm",
    label: str = "📊 Select Scenario",
) -> str:
    """
    Scenario selection dropdown.

    Args:
        default_scenario: Default scenario ID
        label: Label text

    Returns:
        Selected scenario ID
    """
    scenarios = {
        "001_itm": "💰 In-The-Money (1.286 moneyness)",
        "002_otm": "🔽 Out-The-Money (0.800 moneyness)",
        "003_atm": "⚖️ At-The-Money (1.000 moneyness)",
        "004_high_withdrawal": "📉 High Withdrawal Stress",
    }

    selected = st.selectbox(
        label,
        scenarios.keys(),
        format_func=lambda x: scenarios.get(x, x),
        index=list(scenarios.keys()).index(default_scenario) if default_scenario in scenarios else 0,
        key="scenario_selector",
    )

    return selected


def mode_toggle(default_mode: str = "offline") -> str:
    """
    Offline/Online mode toggle.

    Args:
        default_mode: "offline" or "online"

    Returns:
        Selected mode
    """
    col1, col2 = st.columns(2)

    with col1:
        offline_btn = st.button(
            "📊 Offline",
            use_container_width=True,
            key="mode_offline_btn",
        )

    with col2:
        online_btn = st.button(
            "🌐 Online",
            use_container_width=True,
            key="mode_online_btn",
        )

    # Store in session state
    if offline_btn:
        st.session_state.selected_mode = "offline"
        st.rerun()
    if online_btn:
        st.session_state.selected_mode = "online"
        st.rerun()

    current_mode = st.session_state.get("selected_mode", default_mode)

    # Display current mode
    mode_icon = "📊" if current_mode == "offline" else "🌐"
    st.info(f"**Mode**: {mode_icon} {current_mode.upper()}")

    return current_mode


def currency_slider(
    label: str,
    min_value: int,
    max_value: int,
    value: int,
    step: int = 10,
    help_text: Optional[str] = None,
    suffix: str = "K",  # Display as thousands
) -> int:
    """
    Currency amount slider (in thousands).

    Args:
        label: Slider label
        min_value: Minimum value (in thousands)
        max_value: Maximum value (in thousands)
        value: Initial value (in thousands)
        step: Step size
        help_text: Help tooltip
        suffix: Display suffix ("K" for thousands)

    Returns:
        Selected value (in thousands)
    """
    result = st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        help=help_text,
    )

    # Display formatted value
    st.caption(f"${result}{suffix}")

    return result


def percentage_slider(
    label: str,
    min_value: float,
    max_value: float,
    value: float,
    step: float = 0.1,
    help_text: Optional[str] = None,
) -> float:
    """
    Percentage slider (0-100 range).

    Args:
        label: Slider label
        min_value: Minimum percentage
        max_value: Maximum percentage
        value: Initial value
        step: Step size
        help_text: Help tooltip

    Returns:
        Selected percentage (as decimal, 0.0-1.0)
    """
    result = st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        format="%.1f%%",
        help=help_text,
    )

    return result / 100  # Convert to decimal


def what_if_sliders() -> Dict[str, float]:
    """
    What-if parameter adjustment sliders.

    Returns:
        Dict of {param_name: value}
    """
    st.markdown("### 🔄 Parameter Adjustment")
    st.markdown("Adjust parameters to see real-time impact on reserves:")

    col1, col2, col3 = st.columns(3)

    with col1:
        account_value = currency_slider(
            "Account Value ($K)",
            min_value=100,
            max_value=1000,
            value=350,
            step=10,
            help_text="Initial account value in thousands",
        )

    with col2:
        benefit_base = currency_slider(
            "Benefit Base ($K)",
            min_value=100,
            max_value=1000,
            value=350,
            step=10,
            help_text="GLWB benefit base in thousands",
        )

    with col3:
        volatility = st.slider(
            "Equity Volatility (%)",
            min_value=10,
            max_value=40,
            value=18,
            step=1,
            help="Expected annual volatility",
        )

    return {
        "account_value": account_value,
        "benefit_base": benefit_base,
        "volatility": volatility,
    }


def parameter_group(
    title: str,
    parameters: Dict[str, Tuple[str, float, float, float]],  # (label, min, max, default)
) -> Dict[str, float]:
    """
    Group of related parameter sliders.

    Args:
        title: Group title
        parameters: Dict of {param_name: (label, min, max, default)}

    Returns:
        Dict of {param_name: selected_value}

    Example:
        params = parameter_group(
            "Market Parameters",
            {
                "interest_rate": ("Interest Rate (%)", 1, 5, 3),
                "volatility": ("Volatility (%)", 10, 40, 18),
            }
        )
    """
    with st.expander(title, expanded=True):
        cols = st.columns(len(parameters))
        results = {}

        for col, (param_name, (label, min_val, max_val, default)) in zip(cols, parameters.items()):
            with col:
                value = st.slider(
                    label,
                    min_value=min_val,
                    max_value=max_val,
                    value=default,
                    step=0.1 if max_val <= 100 else 1,
                )
                results[param_name] = value

        return results


def confidence_threshold(
    label: str = "Confidence Threshold",
    default: float = 0.7,
) -> float:
    """
    Confidence threshold selector (0.0-1.0).

    Args:
        label: Slider label
        default: Default threshold

    Returns:
        Selected threshold
    """
    threshold = st.slider(
        label,
        min_value=0.0,
        max_value=1.0,
        value=default,
        step=0.05,
        format="%.0f%%",
        help="Fields below this confidence will be flagged for manual review",
    )

    st.caption(f"Threshold: {threshold:.0%}")

    return threshold


def approval_decision_selector(
    label: str = "Override Approval Decision",
) -> str:
    """
    Approval decision override selector.

    Args:
        label: Selector label

    Returns:
        Selected decision: "approve", "decline", or "rate"
    """
    options = {
        "approve": "✅ APPROVE",
        "rate": "⚠️ RATE",
        "decline": "❌ DECLINE",
    }

    selected = st.selectbox(
        label,
        options.keys(),
        format_func=lambda x: options.get(x, x),
    )

    return selected


def date_range_selector(
    label: str = "Analysis Period",
) -> Tuple[str, str]:
    """
    Date range selector.

    Args:
        label: Selector label

    Returns:
        Tuple of (start_date, end_date) as strings
    """
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            key="start_date",
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            key="end_date",
        )

    return str(start_date), str(end_date)


def scenario_comparison_selector(
    available_scenarios: List[str],
) -> List[str]:
    """
    Multi-select for scenario comparison.

    Args:
        available_scenarios: List of available scenario IDs

    Returns:
        List of selected scenario IDs
    """
    scenario_labels = {
        "001_itm": "💰 In-The-Money",
        "002_otm": "🔽 Out-The-Money",
        "003_atm": "⚖️ At-The-Money",
        "004_high_withdrawal": "📉 High Withdrawal Stress",
    }

    selected = st.multiselect(
        "Select scenarios to compare",
        available_scenarios,
        default=available_scenarios[:2],  # Select first 2 by default
        format_func=lambda x: scenario_labels.get(x, x),
    )

    return selected


def chart_style_selector() -> str:
    """
    Chart style selector.

    Returns:
        Selected style: "dark" or "light"
    """
    col1, col2 = st.columns(2)

    with col1:
        light_btn = st.button("☀️ Light", use_container_width=True)

    with col2:
        dark_btn = st.button("🌙 Dark", use_container_width=True)

    if light_btn:
        st.session_state.chart_style = "light"
    if dark_btn:
        st.session_state.chart_style = "dark"

    current_style = st.session_state.get("chart_style", "light")

    return current_style


def export_format_selector() -> str:
    """
    Export format selector.

    Returns:
        Selected format: "csv", "pdf", or "json"
    """
    format_options = {
        "csv": "📊 CSV",
        "pdf": "📄 PDF",
        "json": "⚙️ JSON",
    }

    selected = st.selectbox(
        "Export Format",
        format_options.keys(),
        format_func=lambda x: format_options.get(x, x),
    )

    return selected
