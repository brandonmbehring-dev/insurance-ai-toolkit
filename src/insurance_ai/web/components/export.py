"""
CSV, Excel, and PDF Export Components for Streamlit UI.

Provides export functionality for crew results:
- Individual crew CSV exports
- All-in-one combined CSV export
- Multi-sheet Excel workbook export
- PDF report generation (future)

Usage:
    from insurance_ai.web.components.export import (
        export_underwriting_csv,
        export_all_crews_csv,
        export_all_crews_excel,
        render_download_button,
    )
"""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


def _dict_to_csv_bytes(data: Dict[str, Any], title: str = "Results") -> bytes:
    """
    Convert a dictionary to CSV bytes.

    Args:
        data: Dictionary with key-value pairs
        title: Section title for the CSV

    Returns:
        CSV content as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([title, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])  # Empty row

    # Data rows
    writer.writerow(["Field", "Value"])
    for key, value in data.items():
        # Format value for display
        if isinstance(value, float):
            if abs(value) < 1:
                formatted = f"{value:.2%}"
            else:
                formatted = f"{value:,.2f}"
        elif isinstance(value, int):
            formatted = f"{value:,}"
        else:
            formatted = str(value)
        writer.writerow([key, formatted])

    return output.getvalue().encode("utf-8")


def _list_to_csv_bytes(data: List[Dict[str, Any]], title: str = "Results") -> bytes:
    """
    Convert a list of dictionaries to CSV bytes.

    Args:
        data: List of dictionaries (table rows)
        title: Section title for the CSV

    Returns:
        CSV content as bytes
    """
    if not data:
        return b"No data available"

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([title, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])  # Empty row

    # Column headers from first row keys
    headers = list(data[0].keys())
    writer.writerow(headers)

    # Data rows
    for row in data:
        writer.writerow([row.get(h, "") for h in headers])

    return output.getvalue().encode("utf-8")


def export_underwriting_csv() -> Optional[bytes]:
    """
    Export underwriting crew results to CSV.

    Returns:
        CSV bytes or None if no results available
    """
    uw_result = st.session_state.get("underwriting_result")
    if not uw_result:
        return None

    data = {
        "Policy ID": uw_result.get("policy_id", "N/A"),
        "Approval Decision": uw_result.get("approval_decision", "N/A"),
        "Risk Class": uw_result.get("risk_class", "N/A"),
        "Confidence Score": uw_result.get("confidence_score", 0),
        "Product Type": "VA + GLWB",
        "Extraction Confidence": uw_result.get("extraction_confidence", 0),
    }

    return _dict_to_csv_bytes(data, "Underwriting Results")


def export_reserves_csv() -> Optional[bytes]:
    """
    Export reserve crew results to CSV.

    Returns:
        CSV bytes or None if no results available
    """
    reserve_result = st.session_state.get("reserve_result")
    if not reserve_result:
        return None

    data = {
        "Account Value": reserve_result.get("account_value", 0),
        "CTE70 Reserve": reserve_result.get("cte70_reserve", 0),
        "Mean Reserve": reserve_result.get("avg_reserve", 0),
        "Number of Scenarios": reserve_result.get("num_scenarios", 0),
        "Tail Ratio": (
            reserve_result.get("cte70_reserve", 0) / reserve_result.get("avg_reserve", 1)
            if reserve_result.get("avg_reserve", 0) > 0
            else 0
        ),
    }

    return _dict_to_csv_bytes(data, "Reserve Analysis (VM-21)")


def export_hedging_csv() -> Optional[bytes]:
    """
    Export hedging crew results to CSV.

    Returns:
        CSV bytes or None if no results available
    """
    hedging_result = st.session_state.get("hedging_result")
    if not hedging_result:
        return None

    data = {
        "Delta": hedging_result.get("delta", 0),
        "Gamma": hedging_result.get("gamma", 0),
        "Vega": hedging_result.get("vega", 0),
        "Theta": hedging_result.get("theta", 0),
        "Rho": hedging_result.get("rho", 0),
        "Hedge Action": hedging_result.get("hedge_action", "N/A"),
        "Hedge Cost": hedging_result.get("hedge_cost", 0),
        "Delta Reduction": hedging_result.get("delta_reduction", 0),
        "Vega Reduction": hedging_result.get("vega_reduction", 0),
    }

    return _dict_to_csv_bytes(data, "Hedging Analysis (Greeks)")


def export_behavior_csv() -> Optional[bytes]:
    """
    Export behavior crew results to CSV.

    Returns:
        CSV bytes or None if no results available
    """
    behavior_result = st.session_state.get("behavior_result")
    if not behavior_result:
        return None

    data = {
        "Moneyness": behavior_result.get("moneyness", 0),
        "Base Lapse Rate": behavior_result.get("base_lapse_rate", 0),
        "Dynamic Lapse Rate": behavior_result.get("dynamic_lapse_rate", 0),
        "Annual Withdrawal Rate": behavior_result.get("annual_withdrawal_rate", 0),
        "Annual Withdrawal ($)": behavior_result.get("annual_withdrawal_dollars", 0),
        "Life Expectancy (Years)": behavior_result.get("life_expectancy_years", 0),
    }

    return _dict_to_csv_bytes(data, "Behavior Analysis (Lapse & Withdrawal)")


def export_scenarios_csv() -> Optional[bytes]:
    """
    Export scenario comparison data to CSV.

    Returns:
        CSV bytes or None if no results available
    """
    # Check if workflow has been run
    if st.session_state.get("underwriting_status") is None:
        return None

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
            "Approval": "APPROVE",
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
            "Approval": "DECLINE",
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
            "Approval": "APPROVE",
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
            "Approval": "RATED",
        },
    ]

    return _list_to_csv_bytes(scenarios_data, "Scenario Comparison Matrix")


def export_all_crews_csv() -> bytes:
    """
    Export all crew results to a single combined CSV.

    Returns:
        Combined CSV bytes with all crew results
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Title header
    writer.writerow(["InsuranceAI Toolkit - Complete Analysis Report"])
    writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])

    # Helper to add section
    def add_section(title: str, data: Optional[Dict[str, Any]]) -> None:
        writer.writerow(["=" * 50])
        writer.writerow([title])
        writer.writerow(["=" * 50])
        if data:
            writer.writerow(["Field", "Value"])
            for key, value in data.items():
                if isinstance(value, float):
                    if abs(value) < 1:
                        formatted = f"{value:.2%}"
                    else:
                        formatted = f"{value:,.2f}"
                elif isinstance(value, int):
                    formatted = f"{value:,}"
                else:
                    formatted = str(value)
                writer.writerow([key, formatted])
        else:
            writer.writerow(["No data available"])
        writer.writerow([])

    # Underwriting
    uw = st.session_state.get("underwriting_result", {})
    add_section("UNDERWRITING RESULTS", {
        "Policy ID": uw.get("policy_id", "N/A"),
        "Approval Decision": uw.get("approval_decision", "N/A"),
        "Risk Class": uw.get("risk_class", "N/A"),
        "Confidence Score": uw.get("confidence_score", 0),
    } if uw else None)

    # Reserves
    res = st.session_state.get("reserve_result", {})
    add_section("RESERVE ANALYSIS (VM-21)", {
        "Account Value": res.get("account_value", 0),
        "CTE70 Reserve": res.get("cte70_reserve", 0),
        "Mean Reserve": res.get("avg_reserve", 0),
        "Scenarios": res.get("num_scenarios", 0),
    } if res else None)

    # Hedging
    hdg = st.session_state.get("hedging_result", {})
    add_section("HEDGING ANALYSIS (GREEKS)", {
        "Delta": hdg.get("delta", 0),
        "Gamma": hdg.get("gamma", 0),
        "Vega": hdg.get("vega", 0),
        "Theta": hdg.get("theta", 0),
        "Hedge Action": hdg.get("hedge_action", "N/A"),
        "Hedge Cost": hdg.get("hedge_cost", 0),
    } if hdg else None)

    # Behavior
    beh = st.session_state.get("behavior_result", {})
    add_section("BEHAVIOR ANALYSIS", {
        "Moneyness": beh.get("moneyness", 0),
        "Base Lapse Rate": beh.get("base_lapse_rate", 0),
        "Dynamic Lapse Rate": beh.get("dynamic_lapse_rate", 0),
        "Annual Withdrawal Rate": beh.get("annual_withdrawal_rate", 0),
    } if beh else None)

    return output.getvalue().encode("utf-8")


def render_download_button(
    data: bytes,
    filename: str,
    label: str = "Download CSV",
    mime: str = "text/csv",
) -> None:
    """
    Render a styled download button.

    Args:
        data: File content as bytes
        filename: Download filename
        label: Button label text
        mime: MIME type for download
    """
    st.download_button(
        label=f"📥 {label}",
        data=data,
        file_name=filename,
        mime=mime,
        use_container_width=True,
    )


def render_crew_export_section(crew_name: str) -> None:
    """
    Render export section for a specific crew page.

    Args:
        crew_name: Name of crew ("underwriting", "reserves", "hedging", "behavior", "scenarios")
    """
    export_functions = {
        "underwriting": (export_underwriting_csv, "underwriting_results.csv"),
        "reserves": (export_reserves_csv, "reserve_analysis.csv"),
        "hedging": (export_hedging_csv, "hedging_greeks.csv"),
        "behavior": (export_behavior_csv, "behavior_analysis.csv"),
        "scenarios": (export_scenarios_csv, "scenario_comparison.csv"),
    }

    if crew_name not in export_functions:
        st.warning(f"Unknown crew: {crew_name}")
        return

    export_fn, filename = export_functions[crew_name]
    csv_data = export_fn()

    if csv_data:
        st.markdown("### 📥 Export Results")
        render_download_button(csv_data, filename, f"Download {crew_name.title()} CSV")
    else:
        st.info("Run the workflow first to enable exports.")


def render_all_exports_section() -> None:
    """
    Render combined export section for dashboard.

    Shows "Download All Results" buttons (CSV and Excel) when workflow has been run.
    """
    if st.session_state.get("underwriting_status") is None:
        return

    st.markdown("### 📥 Export All Results")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    col1, col2 = st.columns(2)

    with col1:
        csv_data = export_all_crews_csv()
        csv_filename = f"insurance_ai_analysis_{timestamp}.csv"
        render_download_button(csv_data, csv_filename, "Download CSV")

    with col2:
        excel_data = export_all_crews_excel()
        if excel_data:
            excel_filename = f"insurance_ai_analysis_{timestamp}.xlsx"
            render_download_button(
                excel_data,
                excel_filename,
                "Download Excel",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


def export_all_crews_excel() -> Optional[bytes]:
    """
    Export all crew results to a multi-sheet Excel workbook.

    Sheets:
    - Summary: Key metrics from all crews
    - Underwriting: Detailed underwriting results
    - Reserves: Reserve analysis with VM-21 metrics
    - Hedging: Greeks and hedge recommendations
    - Behavior: Lapse and withdrawal analysis
    - Scenarios: Scenario comparison matrix

    Returns:
        Excel file bytes or None if openpyxl not available
    """
    try:
        from openpyxl.utils.dataframe import dataframe_to_rows
    except ImportError:
        st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")
        return None

    # Collect data from session state
    uw = st.session_state.get("underwriting_result", {})
    res = st.session_state.get("reserve_result", {})
    hdg = st.session_state.get("hedging_result", {})
    beh = st.session_state.get("behavior_result", {})

    # Create Excel buffer
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Summary
        summary_data = {
            "Metric": [
                "Report Generated",
                "Approval Decision",
                "Risk Class",
                "CTE70 Reserve",
                "Reserve Ratio",
                "Delta",
                "Hedge Action",
                "Dynamic Lapse Rate",
            ],
            "Value": [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                uw.get("approval_decision", "N/A"),
                uw.get("risk_class", "N/A"),
                f"${res.get('cte70_reserve', 0):,.0f}" if res else "N/A",
                f"{res.get('cte70_reserve', 0) / res.get('account_value', 1):.1%}" if res.get("account_value") else "N/A",
                f"{hdg.get('delta', 0):.4f}" if hdg else "N/A",
                hdg.get("hedge_action", "N/A"),
                f"{beh.get('dynamic_lapse_rate', 0):.2%}" if beh else "N/A",
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

        # Sheet 2: Underwriting
        if uw:
            uw_data = {
                "Field": ["Policy ID", "Approval Decision", "Risk Class", "Confidence Score", "Extraction Confidence"],
                "Value": [
                    uw.get("policy_id", "N/A"),
                    uw.get("approval_decision", "N/A"),
                    uw.get("risk_class", "N/A"),
                    f"{uw.get('confidence_score', 0):.2%}",
                    f"{uw.get('extraction_confidence', 0):.2%}",
                ],
            }
            pd.DataFrame(uw_data).to_excel(writer, sheet_name="Underwriting", index=False)

        # Sheet 3: Reserves
        if res:
            res_data = {
                "Field": ["Account Value", "Benefit Base", "CTE70 Reserve", "Mean Reserve", "Scenarios", "Tail Ratio"],
                "Value": [
                    f"${res.get('account_value', 0):,.0f}",
                    f"${res.get('benefit_base', res.get('account_value', 0)):,.0f}",
                    f"${res.get('cte70_reserve', 0):,.0f}",
                    f"${res.get('avg_reserve', 0):,.0f}",
                    f"{res.get('num_scenarios', 0):,}",
                    f"{res.get('cte70_reserve', 0) / res.get('avg_reserve', 1):.3f}" if res.get("avg_reserve") else "N/A",
                ],
            }
            pd.DataFrame(res_data).to_excel(writer, sheet_name="Reserves", index=False)

        # Sheet 4: Hedging
        if hdg:
            hdg_data = {
                "Greek": ["Delta", "Gamma", "Vega", "Theta", "Rho"],
                "Value": [
                    hdg.get("delta", 0),
                    hdg.get("gamma", 0),
                    hdg.get("vega", 0),
                    hdg.get("theta", 0),
                    hdg.get("rho", 0),
                ],
                "Description": [
                    "Sensitivity to underlying price",
                    "Rate of change of delta",
                    "Sensitivity to volatility",
                    "Time decay",
                    "Sensitivity to interest rates",
                ],
            }
            pd.DataFrame(hdg_data).to_excel(writer, sheet_name="Hedging", index=False)

            # Add hedge recommendation
            hedge_rec = pd.DataFrame({
                "Hedge Recommendation": [
                    f"Action: {hdg.get('hedge_action', 'N/A')}",
                    f"Cost: ${hdg.get('hedge_cost', 0):,.0f}",
                    f"Delta Reduction: {hdg.get('delta_reduction', 0):.1%}",
                    f"Vega Reduction: {hdg.get('vega_reduction', 0):.1%}",
                ]
            })
            hedge_rec.to_excel(writer, sheet_name="Hedge_Recommendation", index=False)

        # Sheet 5: Behavior
        if beh:
            beh_data = {
                "Field": [
                    "Moneyness",
                    "Base Lapse Rate",
                    "Dynamic Lapse Rate",
                    "Annual Withdrawal Rate",
                    "Annual Withdrawal ($)",
                    "Life Expectancy (Years)",
                ],
                "Value": [
                    f"{beh.get('moneyness', 0):.3f}",
                    f"{beh.get('base_lapse_rate', 0):.2%}",
                    f"{beh.get('dynamic_lapse_rate', 0):.2%}",
                    f"{beh.get('annual_withdrawal_rate', 0):.2%}",
                    f"${beh.get('annual_withdrawal_dollars', 0):,.0f}",
                    f"{beh.get('life_expectancy_years', 0):.1f}",
                ],
            }
            pd.DataFrame(beh_data).to_excel(writer, sheet_name="Behavior", index=False)

        # Sheet 6: Scenarios (if available)
        scenarios_data = [
            {"ID": "001_itm", "Label": "In-The-Money", "Moneyness": 1.286, "CTE70": 58000, "Lapse": 0.03},
            {"ID": "002_otm", "Label": "Out-The-Money", "Moneyness": 0.800, "CTE70": 72000, "Lapse": 0.18},
            {"ID": "003_atm", "Label": "At-The-Money", "Moneyness": 1.000, "CTE70": 65000, "Lapse": 0.08},
            {"ID": "004_stress", "Label": "High Withdrawal", "Moneyness": 0.750, "CTE70": 85000, "Lapse": 0.22},
        ]
        pd.DataFrame(scenarios_data).to_excel(writer, sheet_name="Scenarios", index=False)

    return output.getvalue()


def export_scenario_comparison_excel(
    base_result: Dict[str, Any],
    stressed_result: Dict[str, Any],
) -> Optional[bytes]:
    """
    Export scenario builder comparison to Excel.

    Args:
        base_result: Base scenario results
        stressed_result: Stressed scenario results

    Returns:
        Excel file bytes
    """
    try:
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Comparison table
            comparison = pd.DataFrame({
                "Metric": [
                    "Account Value",
                    "CTE70 Reserve",
                    "Reserve Ratio",
                    "Moneyness",
                    "Dynamic Lapse Rate",
                    "Volatility",
                    "Interest Rate",
                ],
                "Base Case": [
                    f"${base_result.get('account_value', 0):,.0f}",
                    f"${base_result.get('cte70_reserve', 0):,.0f}",
                    f"{base_result.get('reserve_ratio', 0):.1%}",
                    f"{base_result.get('moneyness', 0):.3f}",
                    f"{base_result.get('dynamic_lapse_rate', 0):.2%}",
                    f"{base_result.get('volatility', 0.20):.0%}",
                    f"{base_result.get('interest_rate', 0.04):.2%}",
                ],
                "Stressed": [
                    f"${stressed_result.get('account_value', 0):,.0f}",
                    f"${stressed_result.get('cte70_reserve', 0):,.0f}",
                    f"{stressed_result.get('reserve_ratio', 0):.1%}",
                    f"{stressed_result.get('moneyness', 0):.3f}",
                    f"{stressed_result.get('dynamic_lapse_rate', 0):.2%}",
                    f"{stressed_result.get('volatility', 0.20):.0%}",
                    f"{stressed_result.get('interest_rate', 0.04):.2%}",
                ],
                "Delta": [
                    f"{((stressed_result.get('account_value', 0) / base_result.get('account_value', 1)) - 1) * 100:+.1f}%",
                    f"{((stressed_result.get('cte70_reserve', 0) / base_result.get('cte70_reserve', 1)) - 1) * 100:+.1f}%",
                    f"{((stressed_result.get('reserve_ratio', 0) / base_result.get('reserve_ratio', 1)) - 1) * 100:+.1f}%",
                    f"{((stressed_result.get('moneyness', 0) / base_result.get('moneyness', 1)) - 1) * 100:+.1f}%",
                    f"{((stressed_result.get('dynamic_lapse_rate', 0) / base_result.get('dynamic_lapse_rate', 1)) - 1) * 100:+.1f}%",
                    "—",
                    "—",
                ],
            })
            comparison.to_excel(writer, sheet_name="Comparison", index=False)

            # Stress parameters
            stress_params = pd.DataFrame({
                "Parameter": ["Equity Shock", "Rate Shock", "Vol Shock", "Lapse Multiplier"],
                "Value": [
                    f"{stressed_result.get('equity_shock_pct', 0):+.0f}%",
                    f"{stressed_result.get('rate_shock_bps', 0):+d} bps",
                    f"{stressed_result.get('vol_shock_pct', 0):+.0f}%",
                    f"{stressed_result.get('lapse_multiplier', 1.0):.1f}x",
                ],
            })
            stress_params.to_excel(writer, sheet_name="Stress_Parameters", index=False)

        return output.getvalue()

    except ImportError:
        return None
