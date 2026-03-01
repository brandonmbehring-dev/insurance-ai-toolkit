# Reserve Crew

VM-21/VM-22 regulatory reserve calculations using Monte Carlo simulation.

## Workflow

```
Scenario Generation → Cash Flow → CTE Calculation → Sensitivity → Convergence
```

### Agent 1: Scenario Generation

Generates economic scenarios using stochastic models:
- **Equity paths**: Geometric Brownian Motion (GBM)
- **Interest rate paths**: Vasicek mean-reverting model
- Seed-deterministic for reproducibility (default seed: 42)

### Agent 2: Cash Flow Projection

Projects liability cash flows across all scenarios:
- Year-by-year projections
- Mortality, lapse, and expense assumptions applied
- Net cash flows per scenario per year

### Agent 3: CTE Calculation

Computes regulatory reserve measures:
- **CTE70** — Conditional Tail Expectation at 70th percentile (VM-21 standard)
- **CTE90** — Conditional Tail Expectation at 90th percentile
- Percentile distribution (p10, p25, p50, p75, p90)
- Risk margin calculation

### Agent 4: Sensitivity Analysis

Shock analysis across key parameters:
- Interest rates: ±50 basis points
- Equity volatility: ±5%
- Lapse rates: ±2%
- Withdrawal rates: ±1%

Validates monotonicity: rate increase of +50bps → reserve increase ≥ 5%.

### Agent 5: Convergence Validation

Verifies Monte Carlo convergence:
- Compares n=1000 vs n=10000 scenario results
- Convergence error must be < 2%
- Outputs required scenario count for target precision

## Validation Invariants

| Invariant | Condition |
|-----------|-----------|
| CTE dominance | CTE70 ≥ Mean (always true by definition) |
| Convergence | Error < 2% between n=1000 and n=10000 |
| Sensitivity monotonicity | Rate +50bps → reserve ≥ 5% increase |

## CLI Usage

```bash
# Default (100 scenarios)
insurance-ai reserve synthetic_policy_001

# Production (1000 scenarios)
insurance-ai reserve synthetic_policy_001 --scenarios 1000 --output reserves.json
```
