"""
Error and warning display components for Streamlit UI.

Implements Decision 4: Graceful Degradation + Warnings
- Shows yellow warning banners instead of red error crashes
- Displays crew status with emojis: ✅ (success), ❌ (failed), ⏭️ (skipped)
- Lists error messages without stopping workflow execution
"""

from typing import Optional

import streamlit as st


def display_workflow_status_badges() -> None:
    """
    Display crew execution status as color-coded badges in a row.

    Shows: ✅ Underwriting | ⚠️ Reserves | ✅ Behavior | ⏭️ Hedging
    """
    col1, col2, col3, col4 = st.columns(4)

    # ===== UNDERWRITING =====
    with col1:
        uw_status = st.session_state.get("underwriting_status")

        if uw_status == "success":
            st.success("✅ **Underwriting**\nApproved")
        elif uw_status == "failed":
            st.error("❌ **Underwriting**\nFailed")
        elif uw_status == "skipped":
            st.info("⏭️ **Underwriting**\nSkipped")
        else:
            st.info("⏳ **Underwriting**\nPending")

    # ===== RESERVES =====
    with col2:
        res_status = st.session_state.get("reserve_status")

        if res_status == "success":
            st.success("✅ **Reserves**\nCalculated")
        elif res_status == "failed":
            st.warning("⚠️ **Reserves**\nFailed")
        elif res_status == "skipped":
            st.info("⏭️ **Reserves**\nSkipped")
        else:
            st.info("⏳ **Reserves**\nPending")

    # ===== BEHAVIOR =====
    with col3:
        beh_status = st.session_state.get("behavior_status")

        if beh_status == "success":
            st.success("✅ **Behavior**\nModeled")
        elif beh_status == "failed":
            st.warning("⚠️ **Behavior**\nFailed")
        elif beh_status == "skipped":
            st.info("⏭️ **Behavior**\nSkipped")
        else:
            st.info("⏳ **Behavior**\nPending")

    # ===== HEDGING =====
    with col4:
        hedge_status = st.session_state.get("hedging_status")

        if hedge_status == "success":
            st.success("✅ **Hedging**\nAnalyzed")
        elif hedge_status == "failed":
            st.warning("⚠️ **Hedging**\nFailed")
        elif hedge_status == "skipped":
            st.info("⏭️ **Hedging**\nSkipped")
        else:
            st.info("⏳ **Hedging**\nPending")


def display_execution_errors() -> None:
    """
    Display error messages from workflow execution.

    Shows as yellow warning banner with error details.
    Does NOT prevent further execution.
    """
    errors = st.session_state.get("execution_errors", [])

    if not errors:
        return

    # Main warning container
    st.warning("⚠️ **Workflow encountered issues during execution**")

    # Expandable error details
    with st.expander("📋 Error Details", expanded=False):
        for i, error_record in enumerate(errors, 1):
            crew = error_record.get("crew", "unknown").upper()
            error_msg = error_record.get("error", "Unknown error")
            timestamp = error_record.get("timestamp", "N/A")

            st.markdown(f"""
            **Error {i}: {crew}**
            - Message: `{error_msg}`
            - Time: {timestamp}
            """)

        # Recovery suggestions
        st.markdown("---")
        st.markdown("""
        **Recovery suggestions:**
        - Try selecting a different scenario
        - Check that fixtures directory is readable
        - Verify ANTHROPIC_API_KEY if using online mode
        - View logs for more details
        """)


def display_approval_decision() -> None:
    """
    Display underwriting approval decision prominently.

    Shows: ✅ APPROVED or ❌ DECLINED
    """
    if st.session_state.get("underwriting_status") is None:
        return

    approved = st.session_state.get("underwriting_approval")

    if approved is None:
        return

    if approved:
        st.success(
            """
            ✅ **APPLICATION APPROVED**

            This applicant has passed underwriting review.
            Proceeding with reserve calculations and hedging analysis.
            """
        )
    else:
        st.error(
            """
            ❌ **APPLICATION DECLINED**

            This applicant did not pass underwriting review.
            Reserve and behavior analysis have been skipped.
            """
        )


def display_workflow_summary() -> None:
    """
    Display a summary of workflow execution with key metrics.

    Shows execution time, which crews succeeded, any warnings.
    """
    status = st.session_state.get("workflow_status")

    if status == "idle":
        st.info("👇 Select a scenario and click 'Run' to begin analysis")
        return

    if status == "running":
        st.info("⏳ Workflow is running... please wait")
        return

    if status != "completed":
        return

    # Workflow completed - show summary
    st.success("✅ **Workflow completed successfully**")

    # Get execution timestamp
    timestamp = st.session_state.get("execution_timestamp")
    if timestamp:
        st.caption(f"Executed: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Show brief status summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        uw_st = st.session_state.get("underwriting_status")
        st.metric("Underwriting", uw_st or "—", delta=None)

    with col2:
        res_st = st.session_state.get("reserve_status")
        st.metric("Reserves", res_st or "—", delta=None)

    with col3:
        beh_st = st.session_state.get("behavior_status")
        st.metric("Behavior", beh_st or "—", delta=None)

    with col4:
        hedge_st = st.session_state.get("hedging_status")
        st.metric("Hedging", hedge_st or "—", delta=None)


def display_mode_info() -> None:
    """
    Display current execution mode (offline/online).

    Shows icon and brief description.
    """
    mode = st.session_state.get("selected_mode", "offline")

    if mode == "offline":
        st.info("📊 **Offline Mode** - Using pre-computed fixtures (no API calls)")
    else:
        st.info("🌐 **Online Mode** - Using Claude API for real-time calculations")


def display_scenario_info() -> None:
    """
    Display information about selected scenario.

    Shows scenario name, moneyness, key insight.
    """
    from ..config import SCENARIO_METADATA

    scenario_id = st.session_state.get("selected_scenario", "001_itm")
    fixture = st.session_state.get("current_fixture")

    if not fixture:
        return

    # Get metadata
    metadata = SCENARIO_METADATA.get(
        scenario_id.split("_")[1], {}  # Extract scenario type from ID
    )

    if metadata:
        st.markdown(f"**{metadata.get('label', scenario_id)}**")
        st.caption(metadata.get("description", ""))
        st.markdown(f"*{metadata.get('key_insight', '')}*")


def display_validation_warnings() -> None:
    """
    Display validation warnings from crew results.

    Examples:
    - High withdrawal rate sustainability warning
    - Low probability of policy in-force at maturity
    - Extreme sensitivity to market moves
    """
    behavior_result = st.session_state.get("behavior_result")
    if not behavior_result:
        return

    validation_metrics = behavior_result.get("validation_metrics", {})
    if not validation_metrics:
        return

    # Check for warnings
    warnings = []

    withdrawal_sust = validation_metrics.get("withdrawal_sustainable")
    if withdrawal_sust == "WARN":
        warnings.append("⚠️ Withdrawal rate may not be sustainable")

    in_force_prob_str = validation_metrics.get("in_force_probability", "")
    if in_force_prob_str:
        try:
            in_force_pct = float(in_force_prob_str.rstrip("%"))
            if in_force_pct < 0.50:
                warnings.append(f"⚠️ Low probability in-force at maturity: {in_force_prob_str}")
        except ValueError:
            pass

    if warnings:
        with st.expander("⚠️ Validation Warnings", expanded=False):
            for warning in warnings:
                st.warning(warning)


# ===== CONTEXT MANAGERS FOR ERROR HANDLING =====

class StreamlitErrorHandler:
    """
    Context manager for safe error handling in Streamlit.

    Usage:
        with StreamlitErrorHandler("crew_name"):
            run_crew(...)
    """

    def __init__(self, crew_name: str):
        self.crew_name = crew_name
        self.error_occurred = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Error occurred
            self.error_occurred = True

            # Log error
            error_msg = str(exc_val) if exc_val else str(exc_type)
            st.session_state.execution_errors.append({
                "crew": self.crew_name,
                "error": error_msg[:200],  # Truncate long messages
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            })

            # Return True to suppress the exception (don't re-raise)
            return True

        return False
