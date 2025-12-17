"""
InsuranceAI Toolkit - Streamlit Web UI

Main entry point for the Streamlit application.
Orchestrates multi-page navigation, theme configuration, and session state.

Run with:
    streamlit run src/insurance_ai/web/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from insurance_ai.web import __version__
from insurance_ai.web.components.export import render_all_exports_section
from insurance_ai.web.components.market_data import render_market_sidebar
from insurance_ai.web.components.pdf_report import render_report_download_section
from insurance_ai.web.config import (
    EXECUTION_MODE,
    GuardianTheme,
    STREAMLIT_CONFIG,
    list_available_scenarios,
)
from insurance_ai.web.utils.state_manager import initialize_session_state


# ===== PAGE CONFIGURATION =====

st.set_page_config(
    page_title="InsuranceAI Toolkit",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": f"InsuranceAI Toolkit v{__version__} - Streamlit Web UI for insurance automation"
    },
)

# Apply theme
st.markdown(
    f"""
    <style>
    :root {{
        --primary-color: {GuardianTheme.PRIMARY_BLUE};
        --secondary-color: {GuardianTheme.SECONDARY_BLUE};
        --accent-color: {GuardianTheme.ACCENT_GOLD};
        --text-color: {GuardianTheme.TEXT_DARK};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ===== SESSION STATE INITIALIZATION =====

initialize_session_state()


# ===== HEADER & BRANDING =====

def render_header() -> None:
    """Render app header with Guardian branding."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("### 🛡️ InsuranceAI")

    with col2:
        st.markdown(
            "<h3 style='text-align: center; color: #003DA5;'>Guardian Toolkit</h3>",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(f"<p style='text-align: right;'><small>v{__version__}</small></p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """
        **Variable Annuity Lifecycle Automation**

        End-to-end processing: Underwriting → Reserves → Hedging → Behavior Modeling
        """
    )


# ===== SIDEBAR NAVIGATION =====

def render_sidebar() -> None:
    """Render sidebar with navigation, scenario selector, and mode toggle."""
    with st.sidebar:
        st.markdown("### ⚙️ Controls")

        # ===== SCENARIO SELECTOR =====
        st.markdown("#### 📊 Select Scenario")
        scenarios = list_available_scenarios()
        scenario_labels = {
            "001_itm": "💰 In-The-Money (1.286 moneyness)",
            "002_otm": "🔽 Out-The-Money (0.8 moneyness)",
            "003_atm": "⚖️ At-The-Money (1.0 moneyness)",
            "004_high_withdrawal": "📉 High Withdrawal Stress",
        }

        selected_scenario = st.selectbox(
            "Scenario",
            scenarios,
            format_func=lambda x: scenario_labels.get(x, x),
            key="selected_scenario",
            label_visibility="collapsed",
        )

        # ===== MODE TOGGLE =====
        st.markdown("#### 🔄 Execution Mode")

        current_mode = st.session_state.get("selected_mode", "offline")

        # Radio button for mode selection
        mode_choice = st.radio(
            "Mode",
            options=["offline", "online"],
            index=0 if current_mode == "offline" else 1,
            format_func=lambda x: "📊 Offline (Fixtures)" if x == "offline" else "🌐 Online (API)",
            horizontal=True,
            label_visibility="collapsed",
            key="mode_radio",
        )

        # Update mode if changed
        if mode_choice != current_mode:
            st.session_state.selected_mode = mode_choice
            st.rerun()

        # Mode status indicator
        if current_mode == "offline":
            st.success("**Offline**: Using pre-computed fixtures (fast, no API)")
        else:
            # Check if API key is available
            import os
            api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
            if api_key_set:
                st.info("**Online**: Claude API enabled")
            else:
                st.warning("**Online**: API key not set. Add ANTHROPIC_API_KEY to secrets.")

        # ===== RUN BUTTON =====
        st.markdown("---")
        if st.button(
            "🚀 Run Workflow",
            use_container_width=True,
            type="primary",
        ):
            from insurance_ai.web.utils.state_manager import run_workflow

            run_workflow(selected_scenario, current_mode)
            st.rerun()

        # ===== INFO PANEL =====
        st.markdown("---")
        st.markdown("#### ℹ️ Status")

        status = st.session_state.get("workflow_status", "idle")
        if status == "idle":
            st.info("Ready to run")
        elif status == "running":
            st.warning("Workflow running...")
        elif status == "completed":
            st.success("Workflow completed")
        elif status == "error":
            st.error("Workflow error")

        # ===== MARKET DATA =====
        st.markdown("---")
        render_market_sidebar()


# ===== MAIN CONTENT AREA =====

def render_main_dashboard() -> None:
    """Render main dashboard page."""
    from insurance_ai.web.components.warnings import (
        display_approval_decision,
        display_execution_errors,
        display_mode_info,
        display_scenario_info,
        display_validation_warnings,
        display_workflow_status_badges,
        display_workflow_summary,
    )

    st.markdown("## 📈 Workflow Dashboard")

    # ===== MODE & SCENARIO INFO =====
    col1, col2 = st.columns(2)
    with col1:
        display_mode_info()
    with col2:
        display_scenario_info()

    st.markdown("---")

    # ===== WORKFLOW STATUS =====
    st.markdown("### Crew Status")
    display_workflow_status_badges()

    st.markdown("---")

    # ===== APPROVAL DECISION =====
    display_approval_decision()

    # ===== WORKFLOW SUMMARY =====
    st.markdown("### Execution Summary")
    display_workflow_summary()

    st.markdown("---")

    # ===== ERROR MESSAGES (if any) =====
    display_execution_errors()

    # ===== VALIDATION WARNINGS =====
    display_validation_warnings()

    st.markdown("---")

    # ===== RESULTS PANELS =====
    st.markdown("### 📊 Detailed Results")

    # Underwriting Results
    uw_result = st.session_state.get("underwriting_result")
    if uw_result:
        with st.expander("✅ Underwriting Results", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Policy ID", uw_result.get("policy_id", "—"))
            with col2:
                st.metric("Approval", uw_result.get("approval_decision", "—"))
            with col3:
                st.metric("Confidence", f"{uw_result.get('confidence_score', 0):.1%}")

    # Reserve Results
    res_result = st.session_state.get("reserve_result")
    if res_result:
        with st.expander("✅ Reserve Calculation Results", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Account Value", f"${res_result.get('account_value', 0):,.0f}")
            with col2:
                st.metric("CTE70 Reserve", f"${res_result.get('cte70_reserve', 0):,.0f}")

    # Behavior Results
    beh_result = st.session_state.get("behavior_result")
    if beh_result:
        with st.expander("✅ Behavior Modeling Results", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Moneyness", f"{beh_result.get('moneyness', 0):.2f}")
            with col2:
                st.metric("Dynamic Lapse", f"{beh_result.get('dynamic_lapse_rate', 0):.1%}")
            with col3:
                st.metric("Probability In-Force", f"{beh_result.get('probability_in_force', 0):.1%}")

    # Hedging Results
    hedge_result = st.session_state.get("hedging_result")
    if hedge_result:
        with st.expander("✅ Hedging Analysis Results", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Delta", f"{hedge_result.get('delta', 0):.2f}")
            with col2:
                st.metric("Vega", f"{hedge_result.get('vega', 0):.3f}")
            with col3:
                st.metric("Hedge Cost", f"${hedge_result.get('hedge_cost', 0):,.0f}")

    st.markdown("---")

    # ===== NEXT STEPS =====
    st.markdown("### 📋 Next Steps")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Try Different Scenarios:**
        - Switch between ITM/OTM/ATM scenarios in the sidebar
        - Each scenario demonstrates different policyholder behavior
        - Observe how reserves and lapse rates change
        """)

    with col2:
        st.markdown("""
        **Learn More:**
        - Check `docs/STREAMLIT_DESIGN.md` for architecture details
        - Review fixture data in `tests/fixtures/behavior/`
        - See implementation in `src/insurance_ai/web/`
        """)

    # ===== EXPORT ALL RESULTS =====
    st.markdown("---")
    render_all_exports_section()

    # ===== GENERATE REPORTS =====
    render_report_download_section()


# ===== FOOTER =====

def render_footer() -> None:
    """Render footer with version and links."""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"InsuranceAI Toolkit v{__version__}")

    with col2:
        st.caption(f"Mode: {st.session_state.get('selected_mode', 'offline').upper()}")

    with col3:
        st.caption(
            "⚠️ Prototype - For demonstration only | Not for production use"
        )


# ===== MAIN APP LOGIC =====

def main() -> None:
    """Main application entry point."""
    # Render header
    render_header()

    # Render sidebar
    render_sidebar()

    # Render main dashboard
    render_main_dashboard()

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
