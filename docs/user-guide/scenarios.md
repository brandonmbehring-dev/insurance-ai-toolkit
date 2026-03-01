# Stress Testing & Scenarios

The Scenarios page provides what-if analysis and stress testing using preset and custom economic scenarios.

## Preset Scenarios

| Scenario | Description |
|----------|-------------|
| **2008 Financial Crisis** | Equity -40%, rates -200bps, vol +15% |
| **March 2020** | Equity -30%, rates -150bps, vol +25% |
| **Rising Rates** | Rates +200bps, equity flat, vol +5% |
| **ITM Stress** | Equity -25%, low rates, high lapse |
| **ATM Baseline** | Current market conditions |
| **OTM Recovery** | Equity +20%, rates +100bps |

## Custom Scenarios

The scenario builder allows setting custom parameters:

- Equity return shock (%)
- Interest rate shift (bps)
- Volatility adjustment (%)
- Lapse rate multiplier
- Withdrawal rate adjustment

## Comparison View

Side-by-side comparison of any two scenarios showing:
- Reserve impact (CTE70 change)
- Greeks change
- Lapse and withdrawal path differences
- Hedge effectiveness under stress

## Dashboard Usage

Navigate to the **Scenarios** page in the Streamlit dashboard:

1. Select a preset scenario or build custom parameters
2. Run the scenario (applies shocks to all 4 crews)
3. Compare against baseline or another scenario
4. Export results to PDF or Excel
