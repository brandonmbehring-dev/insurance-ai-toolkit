"""
Bulk Policy Upload Component for Streamlit UI.

Provides CSV upload functionality for batch policy processing:
- Upload CSV with policy cohort data
- Validate schema and data types
- Process multiple policies through all crews
- Display aggregate statistics and individual results
- Export cohort summary

Usage:
    from insurance_ai.web.components.bulk_upload import (
        render_bulk_upload_section,
        process_policy_batch,
    )
"""

import io
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Expected columns for bulk upload
REQUIRED_COLUMNS = ["policy_id", "account_value", "benefit_base", "age"]
OPTIONAL_COLUMNS = ["gender", "risk_class", "product_type", "withdrawal_rate"]

# Example data for template
EXAMPLE_DATA = [
    {
        "policy_id": "POL001",
        "account_value": 450000,
        "benefit_base": 350000,
        "age": 62,
        "gender": "M",
        "risk_class": "PREFERRED",
        "product_type": "VA_GLWB",
        "withdrawal_rate": 0.04,
    },
    {
        "policy_id": "POL002",
        "account_value": 280000,
        "benefit_base": 350000,
        "age": 68,
        "gender": "F",
        "risk_class": "STANDARD",
        "product_type": "VA_GLWB",
        "withdrawal_rate": 0.05,
    },
    {
        "policy_id": "POL003",
        "account_value": 350000,
        "benefit_base": 350000,
        "age": 65,
        "gender": "M",
        "risk_class": "PREFERRED",
        "product_type": "FIA",
        "withdrawal_rate": 0.04,
    },
]


def validate_csv_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that uploaded CSV has required columns.

    Args:
        df: Pandas DataFrame from uploaded CSV

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    # Check for empty DataFrame
    if len(df) == 0:
        errors.append("CSV file is empty")

    # Validate data types for required columns
    if "account_value" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["account_value"]):
            errors.append("account_value must be numeric")

    if "benefit_base" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["benefit_base"]):
            errors.append("benefit_base must be numeric")

    if "age" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["age"]):
            errors.append("age must be numeric")
        elif df["age"].min() < 18 or df["age"].max() > 100:
            errors.append("age must be between 18 and 100")

    return len(errors) == 0, errors


def calculate_moneyness(account_value: float, benefit_base: float) -> float:
    """Calculate moneyness (Account Value / Benefit Base)."""
    if benefit_base <= 0:
        return 1.0
    return account_value / benefit_base


def calculate_dynamic_lapse_rate(moneyness: float, base_rate: float = 0.08) -> float:
    """
    Calculate dynamic lapse rate based on moneyness.

    ITM (moneyness > 1.1): Lower lapse (people keep valuable guarantees)
    ATM (0.9-1.1): Moderate lapse
    OTM (moneyness < 0.9): Higher lapse (guarantee less valuable)
    """
    if moneyness > 1.1:
        return max(0.02, base_rate * 0.4)  # ITM: 40% of base
    elif moneyness < 0.9:
        return min(0.25, base_rate * 2.5)  # OTM: 250% of base
    else:
        return base_rate  # ATM: base rate


def calculate_cte70_reserve(account_value: float, benefit_base: float, age: int) -> float:
    """
    Simplified CTE70 reserve calculation.

    In production, this would use Monte Carlo simulation.
    Here we use a deterministic approximation for demo purposes.
    """
    moneyness = calculate_moneyness(account_value, benefit_base)

    # Base reserve as fraction of benefit base
    if moneyness > 1.1:  # ITM
        base_factor = 0.12
    elif moneyness < 0.9:  # OTM
        base_factor = 0.22
    else:  # ATM
        base_factor = 0.17

    # Age adjustment (older = longer liability)
    age_factor = 1.0 + max(0, (age - 60)) * 0.02

    return benefit_base * base_factor * age_factor


def process_single_policy(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single policy through all analysis steps.

    Args:
        row: Dictionary with policy data

    Returns:
        Dictionary with all calculated metrics
    """
    account_value = float(row["account_value"])
    benefit_base = float(row["benefit_base"])
    age = int(row["age"])

    moneyness = calculate_moneyness(account_value, benefit_base)
    lapse_rate = calculate_dynamic_lapse_rate(moneyness)
    cte70 = calculate_cte70_reserve(account_value, benefit_base, age)

    # Determine approval decision
    if moneyness < 0.75 or lapse_rate > 0.20:
        approval = "DECLINE"
    elif moneyness < 0.85 or lapse_rate > 0.15:
        approval = "RATED"
    else:
        approval = "APPROVE"

    return {
        "policy_id": row["policy_id"],
        "account_value": account_value,
        "benefit_base": benefit_base,
        "age": age,
        "moneyness": round(moneyness, 3),
        "dynamic_lapse_rate": round(lapse_rate, 4),
        "cte70_reserve": round(cte70, 2),
        "reserve_ratio": round(cte70 / account_value, 4) if account_value > 0 else 0,
        "approval": approval,
        "risk_class": row.get("risk_class", "STANDARD"),
    }


def process_policy_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process entire policy cohort through analysis pipeline.

    Args:
        df: DataFrame with policy data

    Returns:
        DataFrame with all calculated metrics for each policy
    """
    results = []
    for _, row in df.iterrows():
        result = process_single_policy(row.to_dict())
        results.append(result)

    return pd.DataFrame(results)


def calculate_cohort_statistics(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate aggregate statistics for processed cohort.

    Args:
        results_df: DataFrame with processed policy results

    Returns:
        Dictionary with cohort-level statistics
    """
    total_policies = len(results_df)
    total_account_value = results_df["account_value"].sum()
    total_reserves = results_df["cte70_reserve"].sum()

    approval_counts = results_df["approval"].value_counts().to_dict()

    return {
        "total_policies": total_policies,
        "total_account_value": total_account_value,
        "total_reserves": total_reserves,
        "avg_moneyness": results_df["moneyness"].mean(),
        "avg_lapse_rate": results_df["dynamic_lapse_rate"].mean(),
        "avg_reserve_ratio": results_df["reserve_ratio"].mean(),
        "approval_rate": approval_counts.get("APPROVE", 0) / total_policies,
        "decline_rate": approval_counts.get("DECLINE", 0) / total_policies,
        "rated_rate": approval_counts.get("RATED", 0) / total_policies,
        "approved_count": approval_counts.get("APPROVE", 0),
        "declined_count": approval_counts.get("DECLINE", 0),
        "rated_count": approval_counts.get("RATED", 0),
    }


def get_template_csv() -> bytes:
    """Generate template CSV file for download."""
    df = pd.DataFrame(EXAMPLE_DATA)
    return df.to_csv(index=False).encode("utf-8")


def render_bulk_upload_section() -> Optional[pd.DataFrame]:
    """
    Render bulk upload UI section with file upload, validation, and processing.

    Returns:
        Processed results DataFrame if available, None otherwise
    """
    st.markdown("## Bulk Policy Upload")
    st.markdown("""
    Upload a CSV file with policy cohort data to process multiple policies at once.
    Each policy will be analyzed through all crews (Underwriting, Reserve, Hedging, Behavior).
    """)

    # Template download
    with st.expander("CSV Template & Column Reference"):
        st.markdown("""
        **Required Columns:**
        | Column | Type | Description |
        |--------|------|-------------|
        | `policy_id` | string | Unique policy identifier |
        | `account_value` | numeric | Current account value ($) |
        | `benefit_base` | numeric | Guaranteed benefit base ($) |
        | `age` | integer | Policyholder age (18-100) |

        **Optional Columns:**
        | Column | Type | Description |
        |--------|------|-------------|
        | `gender` | string | M or F |
        | `risk_class` | string | PREFERRED, STANDARD, SUBSTANDARD |
        | `product_type` | string | VA_GLWB, FIA, RILA |
        | `withdrawal_rate` | numeric | Expected annual withdrawal rate |
        """)

        template_csv = get_template_csv()
        st.download_button(
            label="Download Template CSV",
            data=template_csv,
            file_name="policy_upload_template.csv",
            mime="text/csv",
        )

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file with policy data. See template above for format.",
    )

    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)

            # Validate schema
            is_valid, errors = validate_csv_schema(df)

            if not is_valid:
                st.error("CSV Validation Failed:")
                for error in errors:
                    st.error(f"  - {error}")
                return None

            # Show preview
            st.success(f"Uploaded {len(df)} policies")
            with st.expander("Preview Uploaded Data"):
                st.dataframe(df.head(10), use_container_width=True)

            # Process button
            if st.button("Process All Policies", type="primary", use_container_width=True):
                with st.spinner(f"Processing {len(df)} policies..."):
                    # Progress bar
                    progress_bar = st.progress(0)

                    results = []
                    for i, (_, row) in enumerate(df.iterrows()):
                        result = process_single_policy(row.to_dict())
                        results.append(result)
                        progress_bar.progress((i + 1) / len(df))

                    results_df = pd.DataFrame(results)
                    progress_bar.empty()

                # Store in session state
                st.session_state["bulk_results"] = results_df
                st.session_state["bulk_stats"] = calculate_cohort_statistics(results_df)

                st.success("Processing complete!")

        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            return None

    # Display results if available
    if "bulk_results" in st.session_state:
        results_df = st.session_state["bulk_results"]
        stats = st.session_state["bulk_stats"]

        st.markdown("---")
        st.markdown("## Cohort Analysis Results")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Policies", f"{stats['total_policies']:,}")
        with col2:
            st.metric("Total AV", f"${stats['total_account_value']:,.0f}")
        with col3:
            st.metric("Total Reserves", f"${stats['total_reserves']:,.0f}")
        with col4:
            st.metric("Avg Reserve Ratio", f"{stats['avg_reserve_ratio']:.1%}")

        # Approval breakdown
        st.markdown("### Approval Distribution")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Approved",
                stats["approved_count"],
                f"{stats['approval_rate']:.0%}",
            )
        with col2:
            st.metric(
                "Rated",
                stats["rated_count"],
                f"{stats['rated_rate']:.0%}",
            )
        with col3:
            st.metric(
                "Declined",
                stats["declined_count"],
                f"-{stats['decline_rate']:.0%}",
            )

        # Detailed results table
        st.markdown("### Policy Details")
        st.dataframe(
            results_df.style.format({
                "account_value": "${:,.0f}",
                "benefit_base": "${:,.0f}",
                "cte70_reserve": "${:,.0f}",
                "moneyness": "{:.3f}",
                "dynamic_lapse_rate": "{:.2%}",
                "reserve_ratio": "{:.2%}",
            }),
            use_container_width=True,
            height=400,
        )

        # Export options
        st.markdown("### Export Results")
        col1, col2 = st.columns(2)

        with col1:
            csv_data = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results (CSV)",
                data=csv_data,
                file_name="bulk_policy_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            # Excel export (requires openpyxl)
            try:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    results_df.to_excel(writer, sheet_name="Policy Results", index=False)
                    pd.DataFrame([stats]).to_excel(
                        writer, sheet_name="Summary Statistics", index=False
                    )
                excel_data = excel_buffer.getvalue()

                st.download_button(
                    label="Download Results (Excel)",
                    data=excel_data,
                    file_name="bulk_policy_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except ImportError:
                st.info("Excel export requires openpyxl. Install with: pip install openpyxl")

        return results_df

    return None


def render_bulk_upload_mini() -> None:
    """
    Render compact bulk upload widget for dashboard sidebar.

    Simplified version showing upload status and link to full page.
    """
    st.markdown("### Bulk Upload")

    if "bulk_results" in st.session_state:
        stats = st.session_state["bulk_stats"]
        st.success(f"{stats['total_policies']} policies processed")
        st.metric("Total Reserves", f"${stats['total_reserves']:,.0f}")
    else:
        st.info("No cohort uploaded yet")

    st.markdown("[Open Bulk Upload Page →](Bulk_Upload)")
