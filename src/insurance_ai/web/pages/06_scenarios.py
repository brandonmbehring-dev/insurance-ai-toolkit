"""
Scenarios Comparison Page

Displays side-by-side scenario comparison and what-if analysis.
Located at: /app?page=scenarios
"""

import streamlit as st

from insurance_ai.web import __version__


def render_scenarios_page() -> None:
    """Render the Scenarios comparison page."""

    st.set_page_config(page_title="Scenarios - InsuranceAI", layout="wide")

    st.markdown("## 🎯 Scenarios & What-If Analysis")
    st.markdown("Compare scenarios → Stress test parameters → Sensitivity analysis")

    # Check if any workflow has been run
    if st.session_state.get("underwriting_status") is None:
        st.info("👇 Run the workflow from the dashboard to analyze scenarios")
        return

    # ===== GUARDIAN CALLOUT =====
    st.markdown("---")
    st.success("""
    ✅ **Guardian Advantage**: Real-time scenario analysis enables rapid business decisions—
    compare applicants, stress-test portfolios, and model "what-if" outcomes instantly.
    """)

    # ===== SCENARIO SELECTOR =====
    st.markdown("---")
    st.markdown("### 📋 Scenario Comparison Matrix")

    scenarios_data = [
        {
            "ID": "001_itm",
            "Label": "In-The-Money",
            "Moneyness": 1.286,
            "Account Value": "$450K",
            "Benefit Base": "$350K",
            "CTE70 Reserve": "$58K",
            "Lapse Rate": "3%",
            "Withdrawal": "2%",
            "Hedge Cost": "$4.2K",
            "Approval": "✅ APPROVE",
        },
        {
            "ID": "002_otm",
            "Label": "Out-The-Money",
            "Moneyness": 0.800,
            "Account Value": "$280K",
            "Benefit Base": "$350K",
            "CTE70 Reserve": "$72K",
            "Lapse Rate": "18%",
            "Withdrawal": "5%",
            "Hedge Cost": "$6.5K",
            "Approval": "❌ DECLINE",
        },
        {
            "ID": "003_atm",
            "Label": "At-The-Money",
            "Moneyness": 1.000,
            "Account Value": "$350K",
            "Benefit Base": "$350K",
            "CTE70 Reserve": "$65K",
            "Lapse Rate": "8%",
            "Withdrawal": "3%",
            "Hedge Cost": "$5.0K",
            "Approval": "✅ APPROVE",
        },
        {
            "ID": "004_stress",
            "Label": "High Withdrawal Stress",
            "Moneyness": 0.750,
            "Account Value": "$300K",
            "Benefit Base": "$400K",
            "CTE70 Reserve": "$85K",
            "Lapse Rate": "22%",
            "Withdrawal": "7%",
            "Hedge Cost": "$8.2K",
            "Approval": "⚠️ RATED",
        },
    ]

    st.dataframe(
        scenarios_data,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Scenario Interpretation", expanded=False):
        st.markdown("""
        **Scenario #1: In-The-Money (ITM)**
        - Account value >> benefit base (customer winning)
        - Low lapse risk (keeps valuable account)
        - Low reserve (favorable economics)
        - **Action**: Standard approval, minimal hedging

        **Scenario #2: Out-The-Money (OTM)**
        - Account value < benefit base (customer underwater)
        - High lapse risk (likely to surrender)
        - High reserve (insure downside)
        - **Action**: Decline or rate-up (margin insufficient)

        **Scenario #3: At-The-Money (ATM)**
        - Baseline economics (account ≈ benefit)
        - Medium lapse (market-dependent)
        - Medium reserve (neutral)
        - **Action**: Standard approval, standard hedging

        **Scenario #4: Stress Test**
        - OTM + high withdrawal (worst-case behavior)
        - Very high lapse + withdrawal (rapid depletion)
        - Highest reserve (tail risk)
        - **Action**: Decline for standard terms; allow with rider adjustments
        """)

    # ===== WHAT-IF ANALYSIS =====
    st.markdown("---")
    st.markdown("### 🔄 What-If Parameter Adjustment")

    st.markdown(
        "Adjust account value, benefit base, or volatility to see reserve impact in real-time:"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        account_value = st.slider(
            "Account Value ($K)",
            min_value=100,
            max_value=1000,
            value=350,
            step=10,
            help="Initial account value in thousands",
        )

    with col2:
        benefit_base = st.slider(
            "Benefit Base ($K)",
            min_value=100,
            max_value=1000,
            value=350,
            step=10,
            help="GLWB benefit base in thousands",
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

    # Calculate derived metrics based on slider inputs
    moneyness = account_value / benefit_base
    base_lapse = 0.08
    dynamic_lapse = base_lapse * (1.0 + 1.5 * (1.0 - moneyness) / 0.3)
    dynamic_lapse = max(0.01, min(0.25, dynamic_lapse))

    # Simple reserve estimate based on moneyness and volatility
    base_reserve = 65000
    reserve_adjustment = (moneyness - 1.0) * -30000 + (volatility - 18) * 1000
    estimated_reserve = base_reserve + reserve_adjustment

    # Display what-if results
    st.markdown("---")
    st.markdown("### 📊 What-If Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Moneyness",
            f"{moneyness:.2f}",
            help="Account / Benefit (current: 1.0)",
        )

    with col2:
        st.metric(
            "Dynamic Lapse",
            f"{dynamic_lapse:.1%}",
            help="Predicted lapse rate",
        )

    with col3:
        st.metric(
            "Est. CTE70 Reserve",
            f"${estimated_reserve:,.0f}",
            help="Estimated reserve (changes in real-time)",
        )

    with col4:
        approval = (
            "✅ APPROVE"
            if estimated_reserve < account_value * 0.25
            else "⚠️ RATED"
            if estimated_reserve < account_value * 0.3
            else "❌ DECLINE"
        )
        st.metric(
            "Decision",
            approval,
            help="Approval recommendation",
        )

    # Sensitivity table
    st.markdown("---")
    st.markdown("### 📈 Reserve Sensitivity to Parameters")

    sensitivity_data = []
    for av in [300, 350, 400]:
        for bb in [350]:
            bb_calc = bb
            m = av / bb_calc
            base_res = 65000
            res_adj = (m - 1.0) * -30000
            res = base_res + res_adj
            sensitivity_data.append(
                {
                    "Account Value ($K)": av,
                    "Benefit Base ($K)": bb_calc,
                    "Moneyness": f"{m:.2f}",
                    "CTE70 Reserve ($K)": f"{res/1000:.0f}",
                    "% of AV": f"{res/av:.1%}",
                }
            )

    st.dataframe(sensitivity_data, use_container_width=True, hide_index=True)

    # ===== PORTFOLIO-LEVEL ANALYSIS =====
    st.markdown("---")
    st.markdown("### 💼 Portfolio-Level Aggregation")

    st.markdown("**Hypothetical cohort of 250 VA policies with GLWB riders:**")

    portfolio_data = {
        "Metric": [
            "Total Account Value",
            "Total Benefit Base",
            "Total CTE70 Reserves",
            "Avg Reserve/AV",
            "Avg Moneyness",
            "Avg Lapse Rate",
            "Expected Lapses (Annual)",
            "Total Hedge Cost",
            "Annualized Hedge Cost",
        ],
        "Baseline": [
            "$87.5M",
            "$92M",
            "$16.2M",
            "18.5%",
            "0.95",
            "9.2%",
            "23 policies",
            "$1.25M",
            "$62K/mo",
        ],
        "Optimized (w/ Behavior)": [
            "$87.5M",
            "$92M",
            "$15.8M",
            "18.1%",
            "0.95",
            "8.1%",
            "20 policies",
            "$1.15M",
            "$57K/mo",
        ],
        "Delta": [
            "—",
            "—",
            "-$400K",
            "-0.4 pp",
            "—",
            "-1.1 pp",
            "-3 fewer",
            "-$100K",
            "-$5K/mo",
        ],
    }

    st.dataframe(portfolio_data, use_container_width=True, hide_index=True)

    with st.expander("Portfolio Insights", expanded=False):
        st.markdown("""
        **Key Findings:**
        1. Dynamic lapse model reduces reserve by $400K (2.5%)
        2. Better lapse predictions → 3 fewer policies lapsing (more accurate forecasting)
        3. Hedge optimization saves $100K capital, $5K/month
        4. Total portfolio value: 0.5% improvement = $437K annual benefit

        **Recommendations:**
        - Adopt rational lapse model for all VA+GLWB products
        - Implement dynamic hedging triggers (monthly rebalancing)
        - Monitor cohort lapse rates vs model predictions
        - Adjust riders for OTM cohorts (increase benefit or reduce withdrawal)
        """)

    # ===== STRESS TEST SCENARIOS =====
    st.markdown("---")
    st.markdown("### 🚨 Stress Testing")

    st.markdown("**How reserves respond to market shocks:**")

    stress_data = {
        "Scenario": [
            "Baseline",
            "Equity -30% Crash",
            "Volatility +50%",
            "Rates +200bps",
            "Combined Stress",
        ],
        "CTE70 Reserve": ["$16.2M", "$22.1M", "$18.5M", "$16.8M", "$26.4M"],
        "Reserve Change": ["+0%", "+36%", "+14%", "+4%", "+63%"],
        "Capital Required": ["$16.2M", "$22.1M", "$18.5M", "$16.8M", "$26.4M"],
        "Hedge Effectiveness": ["—", "60% reduction", "75% reduction", "—", "50% reduction"],
    }

    st.dataframe(stress_data, use_container_width=True, hide_index=True)

    with st.expander("Stress Test Interpretation", expanded=False):
        st.markdown("""
        **Equity -30% Crash:**
        - Accounts fall 30%, moneyness drops below 1.0 (ITM → OTM)
        - Lapse rates spike (customers surrender underwater accounts)
        - Reserve increases 36% (tail risk)
        - Hedge reduces impact by 60% (put protection limits losses)

        **Volatility Spike:**
        - Vega exposure activates (larger option payouts)
        - Reserve increases 14%
        - Hedge vega reduction: 75% effective

        **Interest Rate Shock:**
        - Modest impact (GLWB less rate-sensitive than bonds)
        - Reserve increases 4% (duration effect)

        **Combined Stress:**
        - Multiple shocks compound (36% + 14% + 4% ≠ 63% due to correlation)
        - Worst-case capital need: $26.4M (63% above baseline)
        - Conservative stress hedge reduces to ~$20M
        """)

    # ===== DECISION SUPPORT =====
    st.markdown("---")
    st.markdown("### ✓ Decision Support Matrix")

    decision_matrix = {
        "If...": [
            "Moneyness > 1.3 (deep ITM)",
            "Moneyness 0.9-1.1 (ATM)",
            "Moneyness < 0.7 (deep OTM)",
            "Volatility > 25%",
            "Benefit withdrawal > 6%",
        ],
        "Then...": [
            "✅ Approve at std rates; minimal hedging",
            "✅ Approve at std rates; standard hedging",
            "❌ Decline OR rate-up benefit base",
            "⚠️ Add volatility rider or increase margins",
            "❌ Decline on product (or reduce withdrawal %)",
        ],
        "Reserve Impact": [
            "-30% vs baseline",
            "Baseline",
            "+50% vs baseline",
            "+25% vs baseline",
            "+15% vs baseline",
        ],
    }

    st.dataframe(decision_matrix, use_container_width=True, hide_index=True)

    # ===== NEXT STEPS =====
    st.markdown("---")
    st.markdown("### 📋 Next Steps")

    st.info("""
    ✅ **Scenario analysis complete.** To optimize further:
    1. Upload real policy data (CSV) for portfolio-level analysis
    2. Model rate/equity paths for multi-year projections
    3. Backtesting: Compare model predictions vs actual lapse behavior
    4. Integration with Guardian's pricing system for rate tables
    """)

    # ===== FOOTER =====
    st.markdown("---")
    st.caption(f"Scenarios Crew v{__version__} | Comparison & What-If Analysis | Educational Prototype")


if __name__ == "__main__":
    render_scenarios_page()
