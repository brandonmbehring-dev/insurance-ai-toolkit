"""
PDF Report Generation for InsuranceAI Toolkit.

Generates comprehensive analysis reports in Markdown format.
PDF generation available when fpdf2 is installed.

Usage:
    from insurance_ai.web.components.pdf_report import (
        generate_markdown_report,
        render_report_download_section,
    )
"""

import io
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st


def _format_value(value: Any) -> str:
    """Format a value for display in reports."""
    if isinstance(value, float):
        if abs(value) < 1 and value != 0:
            return f"{value:.2%}"
        else:
            return f"{value:,.2f}"
    elif isinstance(value, int):
        return f"{value:,}"
    elif value is None:
        return "N/A"
    else:
        return str(value)


def _generate_section(title: str, data: Dict[str, Any]) -> str:
    """Generate a markdown section for a crew result."""
    lines = [
        f"## {title}",
        "",
    ]

    if not data:
        lines.append("*No data available - workflow not run*")
        lines.append("")
        return "\n".join(lines)

    # Create table
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    for key, value in data.items():
        formatted = _format_value(value)
        lines.append(f"| {key} | {formatted} |")

    lines.append("")
    return "\n".join(lines)


def generate_markdown_report() -> str:
    """
    Generate a comprehensive markdown report of all crew results.

    Returns:
        Markdown string containing full analysis report
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scenario = st.session_state.get("selected_scenario", "Unknown")
    mode = st.session_state.get("selected_mode", "offline")

    lines = [
        "# InsuranceAI Toolkit - Analysis Report",
        "",
        f"**Generated**: {timestamp}",
        f"**Scenario**: {scenario}",
        f"**Mode**: {mode.upper()}",
        "",
        "---",
        "",
    ]

    # Executive Summary
    uw = st.session_state.get("underwriting_result", {})
    res = st.session_state.get("reserve_result", {})
    hdg = st.session_state.get("hedging_result", {})
    beh = st.session_state.get("behavior_result", {})

    lines.extend([
        "## Executive Summary",
        "",
    ])

    if uw:
        approval = uw.get("approval_decision", "N/A")
        confidence = uw.get("confidence_score", 0)
        lines.append(f"- **Underwriting Decision**: {approval} (Confidence: {confidence:.1%})")

    if res:
        cte70 = res.get("cte70_reserve", 0)
        av = res.get("account_value", 0)
        lines.append(f"- **CTE70 Reserve**: ${cte70:,.0f} ({cte70/av:.1%} of AV)" if av else f"- **CTE70 Reserve**: ${cte70:,.0f}")

    if hdg:
        delta = hdg.get("delta", 0)
        hedge_cost = hdg.get("hedge_cost", 0)
        lines.append(f"- **Portfolio Delta**: {delta:.2f} | **Hedge Cost**: ${hedge_cost:,.0f}")

    if beh:
        moneyness = beh.get("moneyness", 0)
        lapse = beh.get("dynamic_lapse_rate", 0)
        lines.append(f"- **Moneyness**: {moneyness:.2f} | **Dynamic Lapse**: {lapse:.1%}")

    lines.extend(["", "---", ""])

    # Underwriting Section
    if uw:
        lines.append(_generate_section("Underwriting Results", {
            "Policy ID": uw.get("policy_id", "N/A"),
            "Approval Decision": uw.get("approval_decision", "N/A"),
            "Risk Class": uw.get("risk_class", "N/A"),
            "Confidence Score": uw.get("confidence_score", 0),
            "Extraction Confidence": uw.get("extraction_confidence", 0),
            "Product Type": "VA + GLWB",
        }))
    else:
        lines.append(_generate_section("Underwriting Results", {}))

    # Reserve Section
    if res:
        avg_res = res.get("avg_reserve", 1)
        cte70 = res.get("cte70_reserve", 0)
        lines.append(_generate_section("Reserve Analysis (VM-21)", {
            "Account Value": res.get("account_value", 0),
            "CTE70 Reserve": cte70,
            "Mean Reserve": avg_res,
            "Number of Scenarios": res.get("num_scenarios", 0),
            "Tail Ratio (CTE70/Mean)": cte70 / avg_res if avg_res > 0 else 0,
        }))
    else:
        lines.append(_generate_section("Reserve Analysis (VM-21)", {}))

    # Hedging Section
    if hdg:
        lines.append(_generate_section("Hedging Analysis (Greeks)", {
            "Delta": hdg.get("delta", 0),
            "Gamma": hdg.get("gamma", 0),
            "Vega": hdg.get("vega", 0),
            "Theta": hdg.get("theta", 0),
            "Rho": hdg.get("rho", 0),
            "Hedge Action": hdg.get("hedge_action", "N/A"),
            "Hedge Cost": hdg.get("hedge_cost", 0),
            "Delta Reduction": hdg.get("delta_reduction", 0),
            "Vega Reduction": hdg.get("vega_reduction", 0),
        }))
    else:
        lines.append(_generate_section("Hedging Analysis (Greeks)", {}))

    # Behavior Section
    if beh:
        lines.append(_generate_section("Behavior Analysis", {
            "Moneyness": beh.get("moneyness", 0),
            "Base Lapse Rate": beh.get("base_lapse_rate", 0),
            "Dynamic Lapse Rate": beh.get("dynamic_lapse_rate", 0),
            "Annual Withdrawal Rate": beh.get("annual_withdrawal_rate", 0),
            "Annual Withdrawal ($)": beh.get("annual_withdrawal_dollars", 0),
            "Life Expectancy (Years)": beh.get("life_expectancy_years", 0),
            "Probability In-Force": beh.get("probability_in_force", 0),
        }))
    else:
        lines.append(_generate_section("Behavior Analysis", {}))

    # Footer
    lines.extend([
        "---",
        "",
        "## Disclaimer",
        "",
        "This report is generated by InsuranceAI Toolkit for **educational and demonstration purposes only**.",
        "It should not be used for actual insurance decisions, regulatory filings, or production systems.",
        "",
        "---",
        "",
        f"*Report generated by InsuranceAI Toolkit v{st.session_state.get('__version__', '0.2.1')}*",
    ])

    return "\n".join(lines)


def generate_pdf_report() -> Optional[bytes]:
    """
    Generate a PDF report using fpdf2.

    Returns:
        PDF bytes or None if fpdf2 is not installed
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    # Create PDF
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "InsuranceAI Toolkit - Analysis Report", ln=True, align="C")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {timestamp}", ln=True, align="C")
    pdf.ln(10)

    # Helper function to add section
    def add_section(title: str, data: Dict[str, Any]) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Helvetica", "", 10)

        if not data:
            pdf.cell(0, 6, "No data available", ln=True)
        else:
            for key, value in data.items():
                formatted = _format_value(value)
                pdf.cell(70, 6, str(key), border=1)
                pdf.cell(0, 6, str(formatted), border=1, ln=True)

        pdf.ln(5)

    # Add sections
    uw = st.session_state.get("underwriting_result", {})
    res = st.session_state.get("reserve_result", {})
    hdg = st.session_state.get("hedging_result", {})
    beh = st.session_state.get("behavior_result", {})

    if uw:
        add_section("Underwriting Results", {
            "Policy ID": uw.get("policy_id", "N/A"),
            "Approval": uw.get("approval_decision", "N/A"),
            "Confidence": uw.get("confidence_score", 0),
        })

    if res:
        add_section("Reserve Analysis", {
            "Account Value": res.get("account_value", 0),
            "CTE70 Reserve": res.get("cte70_reserve", 0),
        })

    if hdg:
        add_section("Hedging Analysis", {
            "Delta": hdg.get("delta", 0),
            "Hedge Cost": hdg.get("hedge_cost", 0),
        })

    if beh:
        add_section("Behavior Analysis", {
            "Moneyness": beh.get("moneyness", 0),
            "Dynamic Lapse": beh.get("dynamic_lapse_rate", 0),
        })

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, "This report is for educational purposes only. Not for production use.")

    return pdf.output()


def render_report_download_section() -> None:
    """
    Render the report download section on the dashboard.

    Shows buttons to download markdown and PDF reports.
    """
    if st.session_state.get("underwriting_status") is None:
        return

    st.markdown("### 📄 Generate Report")

    col1, col2 = st.columns(2)

    # Markdown report (always available)
    with col1:
        md_report = generate_markdown_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        st.download_button(
            label="📝 Download Markdown Report",
            data=md_report.encode("utf-8"),
            file_name=f"insurance_ai_report_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # PDF report (if fpdf2 available)
    with col2:
        pdf_data = generate_pdf_report()
        if pdf_data:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name=f"insurance_ai_report_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button(
                "📄 PDF (install fpdf2)",
                disabled=True,
                use_container_width=True,
                help="Install fpdf2: pip install fpdf2",
            )
