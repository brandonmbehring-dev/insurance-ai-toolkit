"""
Unit tests for Plotly chart components.

Tests individual chart functions for:
- Correct figure generation
- Proper data structure
- Guardian color theme application
- Performance with large datasets

Run with:
    pytest tests/unit/test_chart_functions.py -v
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import Plotly, but make it optional
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


@pytest.mark.skipif(not HAS_PLOTLY, reason="Plotly not installed (install with: pip install -e '.[web]')")
class TestChartFunctions:
    """Tests for chart rendering functions."""

    def test_cte70_histogram_basic(self):
        """Test CTE70 histogram with basic data."""
        from insurance_ai.web.components.charts import plot_cte70_histogram

        simulated_values = [50000 + i * 100 for i in range(100)]
        fig = plot_cte70_histogram(
            simulated_values=simulated_values,
            cte70_value=65000,
            mean_value=60000,
        )

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1  # At least histogram trace
        assert fig.layout.title.text == "CTE70 Reserve Distribution"

    def test_cte70_histogram_with_custom_title(self):
        """Test CTE70 histogram with custom title."""
        from insurance_ai.web.components.charts import plot_cte70_histogram

        simulated_values = list(range(50000, 70000, 100))
        custom_title = "Custom CTE70 Title"
        fig = plot_cte70_histogram(
            simulated_values=simulated_values,
            cte70_value=60000,
            mean_value=58000,
            title=custom_title,
        )

        assert fig.layout.title.text == custom_title

    def test_sensitivity_tornado_structure(self):
        """Test tornado chart has correct structure."""
        from insurance_ai.web.components.charts import plot_sensitivity_tornado

        drivers = {
            "Rate": (60000, 70000),
            "Vol": (62000, 68000),
            "Lapse": (61000, 69000),
            "Withdrawal": (61500, 68500),
            "Expense": (62500, 67500),
        }
        fig = plot_sensitivity_tornado(drivers, baseline=65000)

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Two traces: low and high impacts
        assert fig.layout.title.text == "Reserve Sensitivity Analysis"

    def test_lapse_curve_renders(self):
        """Test lapse curve chart renders correctly."""
        from insurance_ai.web.components.charts import plot_lapse_curve

        moneyness_values = list(np.linspace(0.5, 1.8, 30))
        lapse_rates = [0.15, 0.12, 0.10, 0.08, 0.05, 0.03, 0.02] + [0.02] * 23

        fig = plot_lapse_curve(
            moneyness_values=moneyness_values,
            lapse_rates=lapse_rates,
            current_moneyness=1.0,
        )

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Curve + current point marker

    def test_lapse_curve_without_current_point(self):
        """Test lapse curve without current moneyness marker."""
        from insurance_ai.web.components.charts import plot_lapse_curve

        moneyness_values = [0.5, 0.75, 1.0, 1.25, 1.5]
        lapse_rates = [0.15, 0.10, 0.08, 0.05, 0.03]

        fig = plot_lapse_curve(
            moneyness_values=moneyness_values,
            lapse_rates=lapse_rates,
            current_moneyness=None,
        )

        assert fig is not None
        # Should have at least the curve trace
        assert len(fig.data) >= 1

    def test_convergence_graph_stability(self):
        """Test convergence graph shows CTE70 stability."""
        from insurance_ai.web.components.charts import plot_convergence

        scenario_counts = [100, 500, 1000, 5000, 10000]
        cte70_values = [65000, 64800, 64600, 64550, 64500]

        fig = plot_convergence(scenario_counts, cte70_values)

        assert fig is not None
        assert isinstance(fig, go.Figure)
        # Should have main line + convergence band
        assert len(fig.data) >= 2

    def test_convergence_graph_with_single_point(self):
        """Test convergence graph with single data point."""
        from insurance_ai.web.components.charts import plot_convergence

        fig = plot_convergence([100], [65000])

        assert fig is not None
        assert isinstance(fig, go.Figure)

    def test_greek_heatmap_delta(self):
        """Test Greeks heatmap for Delta."""
        from insurance_ai.web.components.charts import plot_greek_heatmap

        prices = list(range(-20, 21, 5))
        vols = list(range(10, 31, 5))
        greek_matrix = np.random.rand(len(prices), len(vols))

        fig = plot_greek_heatmap(
            underlying_prices=prices,
            volatilities=vols,
            greek_matrix=greek_matrix,
            greek_name="Delta",
        )

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_greek_heatmap_vega(self):
        """Test Greeks heatmap for Vega."""
        from insurance_ai.web.components.charts import plot_greek_heatmap

        prices = list(range(-20, 21, 5))
        vols = list(range(10, 31, 5))
        greek_matrix = np.random.rand(len(prices), len(vols)) * 1000

        fig = plot_greek_heatmap(
            underlying_prices=prices,
            volatilities=vols,
            greek_matrix=greek_matrix,
            greek_name="Vega",
        )

        assert fig is not None
        assert "Vega" in fig.layout.title.text

    def test_scenario_comparison_box_plot(self):
        """Test scenario comparison box plot."""
        from insurance_ai.web.components.charts import plot_scenario_comparison

        scenarios = {
            "Scenario 1": [60000, 62000, 64000, 66000, 68000],
            "Scenario 2": [61000, 63000, 65000, 67000, 69000],
            "Scenario 3": [59000, 61000, 63000, 65000, 67000],
        }
        fig = plot_scenario_comparison(scenarios)

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 3  # One box plot per scenario

    def test_scenario_comparison_single_scenario(self):
        """Test scenario comparison with single scenario."""
        from insurance_ai.web.components.charts import plot_scenario_comparison

        scenarios = {"Only Scenario": [60000, 65000, 70000]}
        fig = plot_scenario_comparison(scenarios)

        assert fig is not None
        assert len(fig.data) == 1

    def test_payoff_diagram_hedging(self):
        """Test payoff diagram comparing unhedged vs hedged."""
        from insurance_ai.web.components.charts import plot_payoff_diagram

        prices = list(range(80, 121))
        unhedged_pnl = [p - 100 for p in prices]
        hedged_pnl = [max(p - 100, -5) for p in prices]

        fig = plot_payoff_diagram(
            underlying_prices=prices,
            unhedged_pnl=unhedged_pnl,
            hedged_pnl=hedged_pnl,
        )

        assert fig is not None
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 2  # Unhedged + hedged lines
        assert fig.layout.title.text == "P&L Payoff Diagram"

    def test_payoff_diagram_custom_title(self):
        """Test payoff diagram with custom title."""
        from insurance_ai.web.components.charts import plot_payoff_diagram

        prices = [90, 100, 110]
        unhedged = [-10, 0, 10]
        hedged = [-5, 0, 8]

        fig = plot_payoff_diagram(
            underlying_prices=prices,
            unhedged_pnl=unhedged,
            hedged_pnl=hedged,
            title="Custom Payoff Title",
        )

        assert fig.layout.title.text == "Custom Payoff Title"


@pytest.mark.skipif(not HAS_PLOTLY, reason="Plotly not installed")
class TestGuardianBranding:
    """Tests for Guardian color scheme consistency."""

    def test_guardian_colors_defined(self):
        """Test that all Guardian colors are defined."""
        from insurance_ai.web.components.charts import get_guardian_colors

        colors = get_guardian_colors()

        assert isinstance(colors, dict)
        assert "primary" in colors
        assert "secondary" in colors
        assert "accent" in colors
        assert "success" in colors
        assert "warning" in colors
        assert "error" in colors

    def test_colors_are_valid_hex(self):
        """Test that all colors are valid hex codes."""
        from insurance_ai.web.components.charts import get_guardian_colors
        import re

        colors = get_guardian_colors()
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")

        for color_name, color_value in colors.items():
            assert hex_pattern.match(color_value), f"{color_name} is not valid hex: {color_value}"

    def test_primary_color_is_guardian_blue(self):
        """Test that primary color is Guardian's blue."""
        from insurance_ai.web.components.charts import get_guardian_colors

        colors = get_guardian_colors()
        # Guardian's primary blue
        assert colors["primary"] == "#003DA5"


@pytest.mark.skipif(not HAS_PLOTLY, reason="Plotly not installed")
class TestChartPerformance:
    """Performance tests for chart rendering."""

    def test_cte70_histogram_with_large_dataset(self):
        """Test CTE70 histogram performance with large dataset."""
        from insurance_ai.web.components.charts import plot_cte70_histogram

        # Generate 10,000 simulated values
        simulated_values = np.random.normal(65000, 5000, 10000).tolist()

        fig = plot_cte70_histogram(
            simulated_values=simulated_values,
            cte70_value=65000,
            mean_value=65000,
        )

        assert fig is not None
        assert len(fig.data) >= 1

    def test_scenario_comparison_many_scenarios(self):
        """Test box plot with many scenarios."""
        from insurance_ai.web.components.charts import plot_scenario_comparison

        # Create 10 scenarios
        scenarios = {
            f"Scenario {i}": np.random.normal(65000, 5000, 100).tolist()
            for i in range(10)
        }

        fig = plot_scenario_comparison(scenarios)

        assert fig is not None
        assert len(fig.data) == 10

    def test_greek_heatmap_high_resolution(self):
        """Test Greeks heatmap with high resolution grid."""
        from insurance_ai.web.components.charts import plot_greek_heatmap

        # 50x50 matrix
        prices = list(range(-25, 26))
        vols = list(range(5, 55))
        greek_matrix = np.random.rand(len(prices), len(vols))

        fig = plot_greek_heatmap(
            underlying_prices=prices,
            volatilities=vols,
            greek_matrix=greek_matrix,
        )

        assert fig is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
