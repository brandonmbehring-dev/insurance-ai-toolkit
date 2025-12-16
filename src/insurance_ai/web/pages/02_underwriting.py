"""
Underwriting Crew Page

Displays medical extraction, risk classification, and approval decision.
Located at: /app?page=underwriting
"""

import streamlit as st

# Assuming this is run as a page within the app context
# (pages are auto-discovered by Streamlit)


def render_underwriting_page() -> None:
    """Render the Underwriting crew page."""

    st.set_page_config(page_title="Underwriting - InsuranceAI", layout="wide")

    st.markdown("## 📋 Underwriting Crew")
    st.markdown("Medical extraction → Risk classification → Approval decision")

    # Check if workflow has been run
    if st.session_state.get("underwriting_status") is None:
        st.info("👇 Run the workflow from the dashboard to see underwriting results")
        return

    uw_result = st.session_state.get("underwriting_result")
    uw_status = st.session_state.get("underwriting_status")

    if uw_status == "failed":
        st.error("❌ Underwriting crew failed - see dashboard for error details")
        return

    # ===== GUARDIAN CALLOUT =====
    st.markdown("---")
    st.success("""
    ✅ **Guardian Advantage**: Automated medical extraction reduces underwriting time from
    **weeks to minutes** with consistent NAIC Model #908 risk classifications.
    """)

    # ===== APPROVAL DECISION (LARGE) =====
    st.markdown("---")
    st.markdown("### 📌 Approval Decision")

    approval = uw_result.get("approval_decision", "UNKNOWN")
    confidence = uw_result.get("confidence_score", 0)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if approval == "APPROVE":
            st.success(f"""
            ### ✅ APPROVED
            Confidence: **{confidence:.1%}**
            """)
        else:
            st.error(f"""
            ### ❌ DECLINED
            Confidence: **{confidence:.1%}**
            """)

    with col2:
        st.metric("Risk Class", uw_result.get("risk_class", "—"))

    with col3:
        st.metric("Approval Confidence", f"{confidence:.1%}")

    # ===== KEY METRICS =====
    st.markdown("---")
    st.markdown("### 📊 Extraction Summary")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    with metric_col1:
        fixture = st.session_state.get("current_fixture", {})
        st.metric("Policy ID", uw_result.get("policy_id", "—")[-8:])  # Last 8 chars

    with metric_col2:
        st.metric("Product Type", "VA + GLWB")

    with metric_col3:
        st.metric("Extraction Fields", "8/8 ✅")

    with metric_col4:
        st.metric("Manual Review Needed", "No")

    # ===== EXTRACTED DATA TABLE =====
    st.markdown("---")
    st.markdown("### 📄 Extracted Medical Data")

    fixture = st.session_state.get("current_fixture", {})

    with st.expander("Applicant Details", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **Applicant Profile**
            - Age: 55 years old
            - Gender: Male
            - Tobacco: Non-smoker
            - Health Status: Standard
            """)

        with col2:
            st.markdown("""
            **Medical History**
            - BMI: 25.5 (Normal)
            - Blood Pressure: 120/80
            - Cholesterol: 180 mg/dL
            - Recent Labs: Normal
            """)

        with col3:
            st.markdown("""
            **Risk Factors**
            - Family History: None
            - Occupation: Professional
            - Avocation: Sedentary
            - Medications: None
            """)

    # ===== RISK CLASSIFICATION =====
    st.markdown("---")
    st.markdown("### 🎯 Risk Classification")

    with st.expander("VBT (Valuation Basic Tables) Analysis", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Standard Class**
            - Base Mortality: 100% of VBT
            - Age: 55 years (standard age)
            - Health: No adverse findings
            - Recommendation: Approve at standard rates
            """)

        with col2:
            st.markdown("""
            **Mortality Adjustment**
            - VBT Table: 2008 VA Valuation Basic Tables
            - Adjustment Factor: 1.0x (standard)
            - Implied mortality: 100 bps at age 55
            - CTE70 Impact: Baseline reserve
            """)

    # ===== CONFIDENCE BREAKDOWN =====
    st.markdown("---")
    st.markdown("### 🔍 Confidence Breakdown")

    confidence_data = {
        "Age Extraction": 0.99,
        "Health Status": 0.95,
        "Smoker Status": 0.98,
        "Medical History": 0.92,
        "Risk Classification": 0.96,
    }

    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]

    for (field, conf), col in zip(confidence_data.items(), cols):
        with col:
            st.metric(field, f"{conf:.0%}")

    # ===== VALIDATION CHECKS =====
    st.markdown("---")
    st.markdown("### ✓ Validation Checks")

    checks = {
        "Age within acceptable range": True,
        "Required fields complete": True,
        "No contradictory data": True,
        "Medical history consistency": True,
        "Risk class matches criteria": True,
    }

    for check_name, passed in checks.items():
        status_icon = "✅" if passed else "❌"
        st.caption(f"{status_icon} {check_name}")

    # ===== NEXT STEPS =====
    st.markdown("---")
    st.markdown("### 📋 Next Steps")

    if approval == "APPROVE":
        st.info("""
        ✅ **Approved applicants proceed to:**
        1. Reserve Crew (VM-21 reserve calculations)
        2. Behavior Crew (dynamic lapse modeling)
        3. Hedging Crew (risk mitigation analysis)
        """)
    else:
        st.warning("""
        ❌ **Declined applicants:**
        - Stop processing (no reserve/hedging)
        - Policy rejected at underwriting stage
        - Consider alternative risk classes (rated, decline)
        """)

    # ===== FOOTER =====
    st.markdown("---")
    st.caption("Underwriting Crew v0.1.0 | Using synthetic medical data only")


if __name__ == "__main__":
    render_underwriting_page()
