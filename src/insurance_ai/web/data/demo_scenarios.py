"""
Demo scenarios for Guardian Life Insurance demonstration.

Provides metadata and loading for 4 pre-computed scenarios covering
different moneyness (ITM/OTM/ATM) and withdrawal stress cases.
"""

from enum import Enum


class ScenarioType(Enum):
    """Scenario types by moneyness."""
    ITM = "in_the_money"       # Account > Benefit
    OTM = "out_the_money"       # Account < Benefit
    ATM = "at_the_money"        # Account ≈ Benefit
    STRESS = "stress_test"      # High withdrawal rate


# Scenario metadata
SCENARIOS = {
    "001_itm": {
        "type": ScenarioType.ITM,
        "label": "💰 In-The-Money (ITM)",
        "description": "Account value 28.6% above benefit base",
        "key_insight": "High account value → low lapse risk, but growth potential capped",
        "moneyness": 1.286,
        "account_value": 450000,
        "benefit_base": 350000,
        "annual_withdrawal": 17500,
        "time_to_maturity_years": 15,
        "reserve_expectation": "Lower reserves (account above guarantee)",
        "lapse_expectation": "Low lapse rates (less valuable guarantee)",
    },
    "002_otm": {
        "type": ScenarioType.OTM,
        "label": "🔽 Out-The-Money (OTM)",
        "description": "Account value 20% below benefit base",
        "key_insight": "Guarantee provides meaningful downside protection",
        "moneyness": 0.800,
        "account_value": 280000,
        "benefit_base": 350000,
        "annual_withdrawal": 14000,
        "time_to_maturity_years": 12,
        "reserve_expectation": "Higher reserves (account below guarantee)",
        "lapse_expectation": "High lapse rates (guarantee valuable)",
    },
    "003_atm": {
        "type": ScenarioType.ATM,
        "label": "⚖️ At-The-Money (ATM)",
        "description": "Account value equals benefit base",
        "key_insight": "Neutral positioning, balanced risk/reward",
        "moneyness": 1.000,
        "account_value": 350000,
        "benefit_base": 350000,
        "annual_withdrawal": 17500,
        "time_to_maturity_years": 20,
        "reserve_expectation": "Medium reserves (account at guarantee)",
        "lapse_expectation": "Medium lapse rates (base scenario)",
    },
    "004_high_withdrawal": {
        "type": ScenarioType.STRESS,
        "label": "📉 High Withdrawal Stress",
        "description": "Aggressive withdrawal rate of 8.3% annually",
        "key_insight": "Annual withdrawal $25K vs $300K account—needs strong growth",
        "moneyness": 0.750,
        "account_value": 300000,
        "benefit_base": 400000,
        "annual_withdrawal": 25000,
        "time_to_maturity_years": 10,
        "reserve_expectation": "High reserves (sustainability risk)",
        "lapse_expectation": "Highest lapse rates (account underwater)",
    },
}


def get_scenario(scenario_id: str) -> dict:
    """
    Get scenario metadata by ID.

    Args:
        scenario_id: Scenario identifier (e.g., "001_itm")

    Returns:
        Scenario metadata dictionary

    Raises:
        ValueError if scenario not found
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(
            f"Scenario '{scenario_id}' not found. "
            f"Available scenarios: {list(SCENARIOS.keys())}"
        )
    return SCENARIOS[scenario_id]


def list_scenarios() -> list[str]:
    """List all available scenario IDs."""
    return list(SCENARIOS.keys())


def list_scenarios_with_labels() -> dict[str, str]:
    """List scenarios as {id: label} mapping."""
    return {sid: data["label"] for sid, data in SCENARIOS.items()}


def get_scenario_type(scenario_id: str) -> ScenarioType:
    """Get scenario type (ITM/OTM/ATM/STRESS)."""
    return SCENARIOS[scenario_id]["type"]


# ===== COMPARISON HELPERS =====

def compare_scenarios(*scenario_ids: str) -> list[dict]:
    """
    Compare multiple scenarios side-by-side.

    Args:
        *scenario_ids: Variable number of scenario IDs

    Returns:
        List of scenario comparison data
    """
    comparison = []
    for sid in scenario_ids:
        scenario = get_scenario(sid)
        comparison.append({
            "id": sid,
            "label": scenario["label"],
            "moneyness": scenario["moneyness"],
            "account_value": scenario["account_value"],
            "withdrawal_rate": (
                scenario["annual_withdrawal"] / scenario["account_value"]
            ),
            "key_insight": scenario["key_insight"],
        })
    return comparison


def describe_scenario(scenario_id: str) -> str:
    """
    Get a human-readable description of a scenario.

    Useful for UI tooltips and help text.
    """
    scenario = get_scenario(scenario_id)
    return f"""
    **{scenario['label']}**

    {scenario['description']}

    **Key Metrics:**
    - Moneyness: {scenario['moneyness']:.3f}
    - Account Value: ${scenario['account_value']:,}
    - Benefit Base: ${scenario['benefit_base']:,}
    - Annual Withdrawal: ${scenario['annual_withdrawal']:,}
    - Time to Maturity: {scenario['time_to_maturity_years']} years

    **Key Insight:**
    {scenario['key_insight']}

    **Expected Reserve Impact:**
    {scenario['reserve_expectation']}

    **Expected Lapse Behavior:**
    {scenario['lapse_expectation']}
    """


if __name__ == "__main__":
    # Print scenario summary
    print("=" * 70)
    print("InsuranceAI Toolkit - Demo Scenarios")
    print("=" * 70)

    for scenario_id in list_scenarios():
        scenario = get_scenario(scenario_id)
        print(f"\n{scenario['label']}")
        print("-" * 70)
        print(f"ID: {scenario_id}")
        print(f"Moneyness: {scenario['moneyness']:.3f}")
        print(f"Account Value: ${scenario['account_value']:,}")
        print(f"Benefit Base: ${scenario['benefit_base']:,}")
        print(f"Annual Withdrawal: ${scenario['annual_withdrawal']:,} "
              f"({scenario['annual_withdrawal']/scenario['account_value']:.1%})")
        print(f"Time to Maturity: {scenario['time_to_maturity_years']} years")
        print(f"\nInsight: {scenario['key_insight']}")

    print("\n" + "=" * 70)
