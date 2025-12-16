"""
KPI Card Components for Streamlit UI.

Reusable metric display components with consistent Guardian branding.
Wraps Streamlit's st.metric() with additional styling and grouping.

Usage:
    display_metric_row({
        "CTE70": ("$65,000", "$2,000"),
        "Reserve": ("$58,000", "-$1,000"),
    })
"""

from typing import Dict, Tuple, Optional
import streamlit as st


def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
) -> None:
    """
    Display a single metric card.

    Args:
        label: Metric name (e.g., "CTE70 Reserve")
        value: Display value (e.g., "$65,000")
        delta: Change indicator (e.g., "+$2,000" or "-$1,000")
        delta_color: "normal" (red/green), "inverse" (opposite), or "off"
        help_text: Tooltip text on hover
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def metric_row(metrics: Dict[str, Tuple[str, Optional[str]]]) -> None:
    """
    Display multiple metrics in a single row (columns layout).

    Args:
        metrics: Dict of {metric_name: (value, delta)}
               e.g., {"CTE70": ("$65K", "+$2K"), "Reserve": ("$58K", "-$1K")}

    Example:
        metric_row({
            "Account Value": ("$450,000", None),
            "CTE70 Reserve": ("$65,000", "+$2,000"),
            "Hedge Cost": ("$4,200", "-$500"),
        })
    """
    num_metrics = len(metrics)
    cols = st.columns(num_metrics)

    for col, (metric_name, (value, delta)) in zip(cols, metrics.items()):
        with col:
            metric_card(
                label=metric_name,
                value=value,
                delta=delta,
            )


def approval_badge(
    status: str,
    confidence: Optional[float] = None,
    risk_class: Optional[str] = None,
) -> None:
    """
    Display approval decision badge (large, prominent).

    Args:
        status: "APPROVE", "DECLINE", "RATED", or "PENDING"
        confidence: Confidence score 0-1 (e.g., 0.94 for 94%)
        risk_class: Risk classification (e.g., "PREFERRED", "STANDARD", "RATED")

    Example:
        approval_badge("APPROVE", confidence=0.94, risk_class="PREFERRED")
    """
    # Color based on status
    status_colors = {
        "APPROVE": "#28A745",  # Green
        "DECLINE": "#DC3545",   # Red
        "RATED": "#FFC107",     # Orange
        "PENDING": "#6C757D",   # Gray
    }
    color = status_colors.get(status, "#003DA5")  # Default to Guardian blue

    # Format HTML badge
    badge_html = f"""
    <div style="
        background-color: {color};
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
    ">
        {status}
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)

    # Show confidence and risk class if provided
    if confidence is not None or risk_class is not None:
        col1, col2 = st.columns(2)
        if confidence is not None:
            with col1:
                st.metric("Confidence", f"{confidence:.1%}")
        if risk_class is not None:
            with col2:
                st.metric("Risk Class", risk_class)


def status_badge_row(crew_statuses: Dict[str, str]) -> None:
    """
    Display workflow status badges for all crews.

    Args:
        crew_statuses: Dict of {crew_name: status}
                     status: "success" ✅, "failed" ❌, "pending" ⏳, "skipped" ⏭️

    Example:
        status_badge_row({
            "Underwriting": "success",
            "Reserves": "success",
            "Behavior": "success",
            "Hedging": "pending",
        })
    """
    status_icons = {
        "success": "✅",
        "failed": "❌",
        "pending": "⏳",
        "skipped": "⏭️",
    }

    status_colors = {
        "success": "#28A745",  # Green
        "failed": "#DC3545",    # Red
        "pending": "#FFC107",   # Orange
        "skipped": "#6C757D",   # Gray
    }

    # Create columns for each crew
    num_crews = len(crew_statuses)
    cols = st.columns(num_crews)

    for col, (crew_name, status) in zip(cols, crew_statuses.items()):
        with col:
            icon = status_icons.get(status, "❓")
            color = status_colors.get(status, "#003DA5")

            badge_html = f"""
            <div style="
                background-color: {color};
                color: white;
                padding: 12px;
                border-radius: 6px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            ">
                {icon} {crew_name}
            </div>
            """

            st.markdown(badge_html, unsafe_allow_html=True)


def metric_group(
    title: str,
    metrics: Dict[str, Tuple[str, Optional[str]]],
    help_text: Optional[str] = None,
) -> None:
    """
    Display a titled group of metrics (expandable).

    Args:
        title: Group title (e.g., "Reserves Summary")
        metrics: Dict of {metric_name: (value, delta)}
        help_text: Explanation of the metric group

    Example:
        metric_group(
            "Reserves Summary",
            {
                "Account Value": ("$450,000", None),
                "CTE70 Reserve": ("$65,000", "+$2,000"),
            },
            help_text="VM-21 reserve calculation"
        )
    """
    with st.expander(title, expanded=True):
        if help_text:
            st.markdown(f"_{help_text}_")
        metric_row(metrics)


def validation_checklist(checks: Dict[str, bool]) -> None:
    """
    Display validation checklist with pass/fail status.

    Args:
        checks: Dict of {check_name: passed_bool}

    Example:
        validation_checklist({
            "Age within acceptable range": True,
            "Required fields complete": True,
            "No contradictory data": False,
        })
    """
    st.markdown("### ✓ Validation Checks")

    for check_name, passed in checks.items():
        status_icon = "✅" if passed else "❌"
        status_text = "Pass" if passed else "FAIL"
        color = "#28A745" if passed else "#DC3545"

        check_html = f"""
        <div style="
            padding: 8px 12px;
            margin: 4px 0;
            background-color: {'#E8F5E9' if passed else '#FFEBEE'};
            border-left: 4px solid {color};
            border-radius: 4px;
        ">
            {status_icon} <span style="color: {color};">{check_name}</span>
        </div>
        """
        st.markdown(check_html, unsafe_allow_html=True)


def warning_banner(title: str, message: str, icon: str = "⚠️") -> None:
    """
    Display warning/alert banner.

    Args:
        title: Banner title (e.g., "Validation Warning")
        message: Warning message
        icon: Icon to display (default: ⚠️)

    Example:
        warning_banner(
            "Extraction Confidence Low",
            "Medical record quality is poor. Manual review recommended."
        )
    """
    banner_html = f"""
    <div style="
        background-color: #FFF3CD;
        border-left: 4px solid #FFC107;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
    ">
        <strong>{icon} {title}</strong><br/>
        {message}
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def success_banner(title: str, message: str, icon: str = "✅") -> None:
    """
    Display success banner.

    Args:
        title: Banner title
        message: Success message
        icon: Icon to display (default: ✅)
    """
    banner_html = f"""
    <div style="
        background-color: #D4EDDA;
        border-left: 4px solid #28A745;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
    ">
        <strong>{icon} {title}</strong><br/>
        {message}
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)


def info_banner(title: str, message: str, icon: str = "ℹ️") -> None:
    """
    Display information banner.

    Args:
        title: Banner title
        message: Information message
        icon: Icon to display (default: ℹ️)
    """
    banner_html = f"""
    <div style="
        background-color: #D1ECF1;
        border-left: 4px solid #17A2B8;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
    ">
        <strong>{icon} {title}</strong><br/>
        {message}
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)
