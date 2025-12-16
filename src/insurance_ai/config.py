"""Configuration and offline/online mode management.

Default: Offline mode with fixtures (deterministic, no API keys required)
Online mode: Requires ANTHROPIC_API_KEY, uses Claude Vision and market APIs
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Determine mode from environment: defaults to offline
ONLINE_MODE: bool = os.getenv("INSURANCE_AI_MODE", "offline").lower() == "online"

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


@dataclass
class Config:
    """Application configuration."""

    online_mode: bool
    anthropic_api_key: Optional[str]
    fixtures_dir: Path
    debug: bool = False

    def validate(self) -> bool:
        """Validate configuration.

        Raises:
            ValueError: If online mode selected but API key not provided.

        Returns:
            True if configuration is valid.
        """
        if self.online_mode and not self.anthropic_api_key:
            raise ValueError(
                "Online mode requires ANTHROPIC_API_KEY environment variable. "
                "Use offline mode (default) for deterministic testing without API keys."
            )
        return True


def get_config(online: Optional[bool] = None, debug: bool = False) -> Config:
    """Get application configuration.

    Args:
        online: Override INSURANCE_AI_MODE environment variable.
                None = use env var (defaults to offline)
        debug: Enable debug logging.

    Returns:
        Config instance with validated settings.

    Raises:
        ValueError: If online mode requested but API key not available.

    Examples:
        >>> # Offline mode (default)
        >>> config = get_config()
        >>> assert not config.online_mode
        >>> assert config.fixtures_dir.exists()

        >>> # Online mode with API key
        >>> import os
        >>> os.environ["ANTHROPIC_API_KEY"] = "sk-..."
        >>> config = get_config(online=True)
        >>> assert config.online_mode
        >>> assert config.anthropic_api_key
    """
    # Determine mode: explicit arg > env var > default (offline)
    if online is None:
        online = ONLINE_MODE

    # Get API key if online mode
    api_key = None
    if online:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    config = Config(
        online_mode=online,
        anthropic_api_key=api_key,
        fixtures_dir=FIXTURES_DIR,
        debug=debug,
    )

    config.validate()
    return config


def load_fixture(crew_name: str, fixture_id: str) -> dict:
    """Load a pre-recorded fixture for deterministic testing.

    Fixtures are JSON files containing recorded tool outputs.
    Allows tests and demos to run without API calls or external dependencies.

    Args:
        crew_name: Crew identifier (e.g., "underwriting", "reserve")
        fixture_id: Fixture identifier (e.g., "applicant_001")

    Returns:
        Fixture data as dict.

    Raises:
        FileNotFoundError: If fixture file not found.
        ValueError: If fixture file is invalid JSON.

    Examples:
        >>> fixture = load_fixture("underwriting", "applicant_001")
        >>> assert "risk_classification" in fixture
        >>> assert fixture["confidence"] > 0.8
    """
    import json

    fixture_path = FIXTURES_DIR / crew_name / f"{fixture_id}.json"

    if not fixture_path.exists():
        available = (
            list((FIXTURES_DIR / crew_name).glob("*.json"))
            if (FIXTURES_DIR / crew_name).exists()
            else []
        )
        raise FileNotFoundError(
            f"Fixture not found: {fixture_path}\n"
            f"Available fixtures in {crew_name}: {[f.stem for f in available]}"
        )

    try:
        with open(fixture_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in fixture {fixture_path}: {e}") from e


class MockClaudeClient:
    """Mock Claude client for offline mode testing.

    Loads pre-recorded responses from fixtures instead of making API calls.
    """

    def __init__(self, fixtures_dir: Path = FIXTURES_DIR):
        """Initialize mock client.

        Args:
            fixtures_dir: Directory containing fixture JSON files.
        """
        self.fixtures_dir = fixtures_dir

    def extract_medical_record(self, pdf_content: bytes, confidence_threshold: float = 0.7) -> dict:
        """Mock medical record extraction.

        In offline mode, loads pre-recorded extraction results.

        Args:
            pdf_content: PDF bytes (ignored in offline mode)
            confidence_threshold: Minimum confidence for fields

        Returns:
            Risk classification with extracted fields
        """
        # In a real implementation, this would load from a fixture
        # For now, return a demo structure
        return {
            "applicant_id": "synthetic_001",
            "age": 55,
            "gender": "M",
            "tobacco": False,
            "extracted_fields": {
                "bp_systolic": "130 mmHg",
                "bp_diastolic": "85 mmHg",
                "cholesterol": "190 mg/dL",
                "hdl": "50 mg/dL",
                "ldl": "120 mg/dL",
            },
            "confidence": 0.92,
            "mortality_class": "Standard",
        }

    def close(self) -> None:
        """Close the mock client (no-op)."""
        pass
