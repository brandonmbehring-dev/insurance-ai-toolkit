# Glossary

```{glossary}
CTE (Conditional Tail Expectation)
    Average of the worst X% of outcomes. CTE70 = average of worst 30%. The regulatory standard for variable annuity reserves under VM-21.

Crew
    A LangGraph StateGraph containing multiple specialized AI agents. The toolkit has 4 crews: Underwriting, Reserve, Hedging, Behavior.

Delta (Δ)
    Rate of change of option value with respect to the underlying asset price. ∂V/∂S.

FIA (Fixed Indexed Annuity)
    Annuity product with returns linked to a market index, with downside protection and a cap/participation rate.

FRED
    Federal Reserve Economic Data. API providing treasury yields, federal funds rate, and economic indicators.

Gamma (Γ)
    Rate of change of delta with respect to the underlying asset price. ∂²V/∂S².

GBM (Geometric Brownian Motion)
    Stochastic process used to model equity price paths in Monte Carlo simulation.

GLWB (Guaranteed Lifetime Withdrawal Benefit)
    Rider on variable annuities guaranteeing a minimum withdrawal amount for life regardless of account performance.

Greeks
    Measures of option sensitivity to market parameters: Delta, Gamma, Vega, Theta, Rho.

ITM (In-the-Money)
    When the guarantee value exceeds the account value. Policyholders are less likely to lapse when ITM.

LangGraph
    Framework for building multi-agent AI workflows as state graphs. Each node is an agent function, edges define execution order.

Moneyness
    Ratio of account value to benefit base. Determines whether a guarantee is ITM, ATM, or OTM.

OTM (Out-of-the-Money)
    When the account value exceeds the guarantee value. Higher lapse rates expected.

RILA (Registered Index-Linked Annuity)
    Annuity with market-linked returns and a buffer or floor protecting against a portion of losses.

Rho (ρ)
    Sensitivity of option value to interest rate changes. ∂V/∂r.

SABR
    Stochastic Alpha Beta Rho model for implied volatility surface calibration.

Theta (Θ)
    Rate of time decay of option value. ∂V/∂t.

VA (Variable Annuity)
    Insurance product with account value invested in sub-accounts (mutual funds), often with guaranteed living/death benefits.

Vasicek Model
    Mean-reverting stochastic model for interest rates: dr = a(b-r)dt + σdW.

VBT (Valuation Basic Table)
    SOA mortality table used for life insurance and annuity pricing.

Vega (ν)
    Sensitivity of option value to implied volatility changes. ∂V/∂σ.

VM-21
    NAIC Valuation Manual section 21. Defines reserve requirements for variable annuities with guarantees.

VM-22
    NAIC Valuation Manual section 22. Defines reserve requirements for fixed annuities.
```
