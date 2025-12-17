"""
Web UI Components for InsuranceAI Toolkit.

Reusable Streamlit components for metrics, charts, forms, and exports.
"""

from .export import (
    export_all_crews_csv,
    export_behavior_csv,
    export_hedging_csv,
    export_reserves_csv,
    export_scenarios_csv,
    export_underwriting_csv,
    render_all_exports_section,
    render_crew_export_section,
    render_download_button,
)
from .pdf_report import (
    generate_markdown_report,
    generate_pdf_report,
    render_report_download_section,
)

__all__ = [
    # Export functions
    "export_underwriting_csv",
    "export_reserves_csv",
    "export_hedging_csv",
    "export_behavior_csv",
    "export_scenarios_csv",
    "export_all_crews_csv",
    "render_download_button",
    "render_crew_export_section",
    "render_all_exports_section",
    # Report functions
    "generate_markdown_report",
    "generate_pdf_report",
    "render_report_download_section",
]
