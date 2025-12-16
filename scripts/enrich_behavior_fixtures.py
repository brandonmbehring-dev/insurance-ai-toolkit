#!/usr/bin/env python3
"""
Enrich behavior fixtures with pre-computed Monte Carlo paths.

This script loads all behavior fixtures and populates the `simulated_account_values`
field by running simulate_behavioral_paths() with the fixture parameters.

Output: saves enriched fixtures as behavior_va_*.enriched.json
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from insurance_ai.crews.behavior.tools import simulate_behavioral_paths


def enrich_fixture(fixture_path: Path) -> dict:
    """
    Load a fixture, enrich it with simulated paths, and return the enriched data.

    Args:
        fixture_path: Path to the JSON fixture file

    Returns:
        Enriched fixture dictionary with simulated_account_values populated
    """
    # Load fixture
    with open(fixture_path, "r") as f:
        fixture = json.load(f)

    print(f"Processing: {fixture_path.name}")
    print(f"  Moneyness: {fixture['moneyness']:.3f}")
    print(f"  Scenarios: {fixture['num_scenarios']}")
    print(f"  Time to maturity: {fixture['time_to_maturity_years']} years")

    # Extract parameters for simulate_behavioral_paths
    initial_account_value = fixture["account_value"]
    benefit_base = fixture["benefit_base"]
    annual_withdrawal = fixture["annual_withdrawal_amount"]
    base_lapse = fixture["base_lapse_rate"]
    num_years = int(fixture["time_to_maturity_years"])
    num_scenarios = fixture["num_scenarios"]
    risk_free_rate = fixture["risk_free_rate"]
    market_vol = fixture["market_volatility"]
    seed = fixture["scenario_seed"]

    # Simulate paths
    print(f"  Running {num_scenarios} scenarios with seed={seed}...")
    account_paths, in_force_flags = simulate_behavioral_paths(
        initial_account_value=initial_account_value,
        benefit_base=benefit_base,
        annual_withdrawal=annual_withdrawal,
        base_lapse=base_lapse,
        num_years=num_years,
        num_scenarios=num_scenarios,
        risk_free_rate=risk_free_rate,
        market_vol=market_vol,
        seed=seed,
    )

    # Populate fixture with simulated values
    fixture["simulated_account_values"] = account_paths

    # Also compute probability_in_force (count surviving scenarios)
    in_force_count = sum(in_force_flags)
    fixture["probability_in_force_at_maturity"] = in_force_count / num_scenarios

    print(f"  ✅ Enriched: {len(account_paths)} paths generated")
    print(f"  In-force probability: {fixture['probability_in_force_at_maturity']:.1%}")

    return fixture


def main():
    """Enrich all behavior fixtures."""
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "behavior"

    # Find all behavior_va_*.json files (not enriched versions)
    fixture_files = sorted([
        f for f in fixture_dir.glob("behavior_va_*.json")
        if ".enriched" not in f.name
    ])

    if not fixture_files:
        print("❌ No behavior fixtures found!")
        return 1

    print(f"Found {len(fixture_files)} fixtures to enrich\n")

    enriched_count = 0
    for fixture_path in fixture_files:
        try:
            enriched_fixture = enrich_fixture(fixture_path)

            # Save enriched version
            enriched_path = fixture_path.parent / f"{fixture_path.stem}.enriched.json"
            with open(enriched_path, "w") as f:
                json.dump(enriched_fixture, f, indent=2)

            print(f"  Saved: {enriched_path.name}\n")
            enriched_count += 1

        except Exception as e:
            print(f"❌ Error processing {fixture_path.name}: {e}\n")
            return 1

    print(f"✅ Successfully enriched {enriched_count}/{len(fixture_files)} fixtures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
