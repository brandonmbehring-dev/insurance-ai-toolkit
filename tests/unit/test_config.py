"""Unit tests for config module."""

import os
import pytest
from pathlib import Path

from insurance_ai.config import ONLINE_MODE, Config, get_config, load_fixture


class TestConfig:
    """Test configuration management."""

    def test_config_offline_mode_default(self) -> None:
        """Test that offline mode is default."""
        config = get_config()
        assert not config.online_mode
        assert config.anthropic_api_key is None

    def test_config_online_mode_with_key(self) -> None:
        """Test online mode with API key."""
        os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
        try:
            config = get_config(online=True)
            assert config.online_mode
            assert config.anthropic_api_key == "sk-test-key"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_online_mode_requires_key(self) -> None:
        """Test that online mode without key raises error."""
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ValueError, match="Online mode requires ANTHROPIC_API_KEY"):
            get_config(online=True)

    def test_config_explicit_offline_override(self) -> None:
        """Test explicit offline flag overrides env var."""
        os.environ["INSURANCE_AI_MODE"] = "online"
        try:
            config = get_config(online=False)
            assert not config.online_mode
        finally:
            os.environ.pop("INSURANCE_AI_MODE", None)


class TestFixtureLoading:
    """Test fixture loading functionality."""

    def test_load_fixture_underwriting(self) -> None:
        """Test loading underwriting fixture."""
        fixture = load_fixture("underwriting", "synthetic_applicant_001")
        assert "applicant_id" in fixture
        assert fixture["applicant_id"] == "synthetic_001"
        assert "risk_classification" in fixture
        assert fixture["confidence_score"] > 0.8

    def test_load_fixture_reserve(self) -> None:
        """Test loading reserve fixture."""
        fixture = load_fixture("reserve", "synthetic_policy_001")
        assert "policy_id" in fixture
        assert "reserve_calculations" in fixture
        assert fixture["reserve_calculations"]["cte70_reserve"] > 0

    def test_load_fixture_hedging(self) -> None:
        """Test loading hedging fixture."""
        fixture = load_fixture("hedging", "synthetic_portfolio_001")
        assert "portfolio_id" in fixture
        assert "portfolio_greeks" in fixture
        assert fixture["portfolio_greeks"]["delta"] > 0

    def test_load_fixture_behavior(self) -> None:
        """Test loading behavior fixture."""
        fixture = load_fixture("behavior", "synthetic_cohort_001")
        assert "cohort_id" in fixture
        assert "lapse_rates_by_moneyness" in fixture
        assert "itm" in fixture["lapse_rates_by_moneyness"]

    def test_load_fixture_not_found(self) -> None:
        """Test that missing fixture raises error."""
        with pytest.raises(FileNotFoundError):
            load_fixture("underwriting", "nonexistent_fixture")

    def test_load_fixture_invalid_json(self) -> None:
        """Test that invalid JSON raises error."""
        # This would require creating a malformed JSON file,
        # skipping for now
        pass


class TestSchema:
    """Test schema validation."""

    def test_config_schema_validation(self) -> None:
        """Test that config validates correctly."""
        config = Config(
            online_mode=False,
            anthropic_api_key=None,
            fixtures_dir=Path("tests/fixtures"),
            debug=False,
        )
        assert config.validate() is True

    def test_fixture_data_integrity(self) -> None:
        """Test that loaded fixtures have correct structure."""
        fixture = load_fixture("underwriting", "synthetic_applicant_001")

        # Check required fields
        required_fields = [
            "applicant_id",
            "age",
            "gender",
            "product_type",
            "risk_classification",
            "confidence_score",
        ]
        for field in required_fields:
            assert field in fixture, f"Missing required field: {field}"

        # Check types
        assert isinstance(fixture["applicant_id"], str)
        assert isinstance(fixture["age"], int)
        assert isinstance(fixture["confidence_score"], float)
        assert 0 <= fixture["confidence_score"] <= 1
