# Hedging Crew

Greeks calculation, volatility calibration, and hedge recommendations for annuity guarantees.

## Capabilities

### Greeks Calculation

Analytical Black-Scholes Greeks for the guarantee portfolio:

| Greek | Measures | Formula Basis |
|-------|----------|---------------|
| Delta (Δ) | Price sensitivity to underlying | ∂V/∂S |
| Gamma (Γ) | Delta sensitivity to underlying | ∂²V/∂S² |
| Vega (ν) | Price sensitivity to volatility | ∂V/∂σ |
| Theta (Θ) | Time decay | ∂V/∂t |
| Rho (ρ) | Interest rate sensitivity | ∂V/∂r |

### SABR Calibration

SABR stochastic volatility model calibration for implied volatility surface:
- Fits α (initial vol), β (CEV exponent), ρ (correlation), ν (vol of vol)
- Target: RMSE < 5% across strike/maturity grid

### Hedge Recommendations

Generates instrument-level hedge recommendations:
- Instrument types: call options, put options, swaptions, futures
- Actions: buy, sell, hold
- Quantity and rationale for each recommendation
- Portfolio-level hedge effectiveness target: > 80% delta reduction

## Dashboard Visualizations

- Greeks heatmap across strike/maturity grid
- Payoff diagrams for recommended instruments
- Hedge effectiveness waterfall chart
- SABR volatility surface 3D plot

## CLI Usage

```bash
insurance-ai hedging synthetic_portfolio_001
insurance-ai hedging --output hedge_results.json
```
