"""
Configuration for Streamlit web UI.

Supports both offline (fixtures) and online (API) modes.
All settings read from environment variables with sensible defaults.

Environment variables:
- INSURANCE_AI_MODE: "offline" or "online" (default: "offline")
- INSURANCE_AI_FIXTURES_DIR: path to fixtures directory (default: "tests/fixtures/")
- ANTHROPIC_API_KEY: required for online mode
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional


class ExecutionMode(Enum):
    """Execution modes for the toolkit."""
    OFFLINE = "offline"
    ONLINE = "online"

    def __str__(self) -> str:
        return self.value


# ===== ENVIRONMENT CONFIGURATION =====

# Default directories (relative to repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
FIXTURES_DIR = Path(os.getenv(
    "INSURANCE_AI_FIXTURES_DIR",
    str(REPO_ROOT / "tests" / "fixtures")
))

# Execution mode
MODE_STR = os.getenv("INSURANCE_AI_MODE", "offline").lower()
if MODE_STR not in ["offline", "online"]:
    raise ValueError(f"INSURANCE_AI_MODE must be 'offline' or 'online', got {MODE_STR}")
EXECUTION_MODE = ExecutionMode(MODE_STR)

# API Keys
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)


# ===== VALIDATION =====

def validate_offline_mode() -> bool:
    """
    Validate offline mode is properly configured.

    Returns:
        True if fixtures directory exists

    Raises:
        ValueError if fixtures don't exist
    """
    if not FIXTURES_DIR.exists():
        raise ValueError(
            f"Offline mode requires fixtures directory at {FIXTURES_DIR}. "
            f"Fixtures not found. Set INSURANCE_AI_FIXTURES_DIR to override."
        )
    return True


def validate_online_mode() -> bool:
    """
    Validate online mode has required API keys.

    Returns:
        True if ANTHROPIC_API_KEY is set

    Raises:
        ValueError if API key missing
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "Online mode requires ANTHROPIC_API_KEY environment variable. "
            "Set it with: export ANTHROPIC_API_KEY=sk-..."
        )
    return True


def validate_mode(mode: Optional[ExecutionMode] = None) -> bool:
    """
    Validate current mode has required configuration.

    Args:
        mode: Mode to validate (defaults to EXECUTION_MODE)

    Returns:
        True if mode is valid

    Raises:
        ValueError if mode is not properly configured
    """
    if mode is None:
        mode = EXECUTION_MODE

    if mode == ExecutionMode.OFFLINE:
        return validate_offline_mode()
    else:
        return validate_online_mode()


# ===== FIXTURE PATHS =====

def get_behavior_fixtures_dir() -> Path:
    """Get path to behavior fixtures directory."""
    behavior_dir = FIXTURES_DIR / "behavior"
    if not behavior_dir.exists():
        raise ValueError(f"Behavior fixtures directory not found at {behavior_dir}")
    return behavior_dir


def get_enriched_fixture_path(scenario_id: str) -> Path:
    """
    Get path to enriched fixture for a scenario.

    Args:
        scenario_id: Scenario identifier (e.g., "base_case", "high_risk")

    Returns:
        Path to enriched fixture JSON file

    Raises:
        ValueError if fixture doesn't exist
    """
    behavior_dir = get_behavior_fixtures_dir()
    fixture_path = behavior_dir / f"behavior_va_{scenario_id}.enriched.json"

    if not fixture_path.exists():
        # Try without enriched suffix (fallback for non-enriched fixtures)
        fallback_path = behavior_dir / f"behavior_va_{scenario_id}.json"
        if fallback_path.exists():
            return fallback_path
        raise ValueError(f"Fixture not found: {fixture_path}")

    return fixture_path


def list_available_scenarios() -> list[str]:
    """
    List all available scenario IDs.

    Returns:
        List of scenario IDs (e.g., ["base_case", "high_risk", ...])
    """
    behavior_dir = get_behavior_fixtures_dir()
    scenario_ids = []

    for fixture_file in sorted(behavior_dir.glob("behavior_va_*.enriched.json")):
        # Extract scenario ID from filename: behavior_va_XXX.enriched.json → XXX
        scenario_id = fixture_file.stem.replace("behavior_va_", "").replace(".enriched", "")
        scenario_ids.append(scenario_id)

    # Fallback to non-enriched if enriched not found
    if not scenario_ids:
        for fixture_file in sorted(behavior_dir.glob("behavior_va_*.json")):
            if ".enriched" not in fixture_file.name:
                scenario_id = fixture_file.stem.replace("behavior_va_", "")
                scenario_ids.append(scenario_id)

    return scenario_ids


# ===== GUARDIAN BRANDING =====

class GuardianTheme:
    """Guardian Life Insurance branding colors and styling."""

    # Primary colors
    PRIMARY_BLUE = "#003DA5"        # Guardian blue
    SECONDARY_BLUE = "#0056CC"      # Lighter blue
    ACCENT_GOLD = "#D4A574"         # Accent color

    # Semantic colors
    SUCCESS = "#4CAF50"             # Green
    WARNING = "#FFC107"             # Yellow/Orange
    ERROR = "#F44336"               # Red
    INFO = "#2196F3"                # Light blue

    # Neutrals
    TEXT_DARK = "#333333"           # Dark gray
    TEXT_LIGHT = "#666666"          # Medium gray
    BACKGROUND = "#FFFFFF"          # White
    BORDER = "#E0E0E0"              # Light gray

    # Fonts
    FONT_FAMILY = "Segoe UI, sans-serif"
    HEADING_FONT = "Arial, sans-serif"

    # Logo & Assets
    LOGO_PATH = "https://www.guardianlife.com/assets/images/guardian-logo.png"


# ===== STREAMLIT THEME CONFIG =====

STREAMLIT_CONFIG = {
    "client": {
        "toolbarMode": "viewer",
        "showErrorDetails": False,
    },
    "theme": {
        "primaryColor": GuardianTheme.PRIMARY_BLUE,
        "backgroundColor": GuardianTheme.BACKGROUND,
        "secondaryBackgroundColor": "#F5F5F5",
        "textColor": GuardianTheme.TEXT_DARK,
        "font": GuardianTheme.FONT_FAMILY,
    },
}


# ===== DEMO SCENARIO METADATA =====

SCENARIO_METADATA = {
    "itm": {
        "label": "💰 In-The-Money (ITM)",
        "description": "Account value 28.6% above benefit base. High lapse risk but growth potential.",
        "key_insight": "Moneyness 1.286 - client benefits from strong market performance",
    },
    "otm": {
        "label": "🔽 Out-The-Money (OTM)",
        "description": "Account value 20% below benefit base. Lower lapse risk, protection valuable.",
        "key_insight": "Moneyness 0.8 - guarantee provides meaningful downside protection",
    },
    "atm": {
        "label": "⚖️ At-The-Money (ATM)",
        "description": "Account value equals benefit base. Baseline lapse scenario.",
        "key_insight": "Moneyness 1.0 - neutral positioning, balanced risk/reward",
    },
    "high_withdrawal": {
        "label": "📉 High Withdrawal Stress",
        "description": "Aggressive withdrawal rate of 8.3% annually. Sustainability risk.",
        "key_insight": "Annual withdrawal $25K vs $300K account - needs aggressive growth",
    },
}


# ===== VALIDATION ON IMPORT =====

try:
    validate_mode()
except ValueError as e:
    # Log warning but don't crash - UI will handle
    print(f"⚠️  Configuration warning: {e}")


if __name__ == "__main__":
    # Print configuration summary
    print("=" * 60)
    print("InsuranceAI Toolkit - Streamlit Configuration")
    print("=" * 60)
    print(f"Execution mode:        {EXECUTION_MODE}")
    print(f"Fixtures directory:    {FIXTURES_DIR}")
    print(f"Offline mode available: {validate_offline_mode() if EXECUTION_MODE == ExecutionMode.OFFLINE else 'N/A'}")
    print(f"Online mode available:  {validate_online_mode() if EXECUTION_MODE == ExecutionMode.ONLINE else 'N/A (missing API key)'}")
    print(f"\nAvailable scenarios:   {list_available_scenarios()}")
    print("=" * 60)
