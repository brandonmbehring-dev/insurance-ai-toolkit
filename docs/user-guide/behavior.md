# Behavior Crew

Dynamic policyholder behavior modeling — lapse rates, withdrawal patterns, and reserve impact.

## Workflow

```
Lapse Modeling → Withdrawal Planning → Path Simulation → Sensitivity
```

### Agent 1: Lapse Modeling

Calculates dynamic lapse rates based on guarantee moneyness:

| Moneyness | Lapse Rate | Rationale |
|-----------|-----------|-----------|
| In-the-money (ITM) | Low | Policyholders retain valuable guarantees |
| At-the-money (ATM) | Medium | Neutral incentive |
| Out-of-the-money (OTM) | High | Guarantee has less value |

**Key invariant**: ITM lapse < ATM lapse < OTM lapse, with ≥ 20% difference between categories.

### Agent 2: Withdrawal Planning

Models withdrawal behavior under two strategies:
- **Static** — Fixed annual withdrawal amount
- **Dynamic ITM** — Withdrawal rate increases when guarantee is in-the-money

### Agent 3: Path Simulation

Monte Carlo simulation of 1000 lapse and withdrawal paths:
- Simulates policyholder cohort over projection horizon
- Accounts for mortality, lapse, and withdrawal interactions
- Produces distribution of remaining policyholders and cash flows

### Agent 4: Sensitivity Analysis

Rate shock impact on behavior and reserves:
- Interest rate sensitivity on lapse rates
- Withdrawal rate sensitivity
- Path convergence validation (< 3% error)

## State Schema

```python
class BehaviorState:
    cohort_data: dict
    lapse_assumptions: LapseAssumption     # base_rate, itm/atm/otm multipliers
    withdrawal_assumptions: dict
    simulated_lapse_paths: list[list[float]]
    simulated_withdrawal_paths: list[WithdrawalPath]
    reserve_impact: float                   # Dollar impact on reserves
    rate_sensitivity: dict[str, float]
```

## CLI Usage

```bash
insurance-ai behavior synthetic_cohort_001
insurance-ai behavior --output behavior_results.json
```
