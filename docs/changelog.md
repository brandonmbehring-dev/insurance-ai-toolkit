# Changelog

## v0.1.0 (2026-02)

Initial release.

### Features

- **4-crew architecture** — Underwriting, Reserves, Hedging, Behavior crews with LangGraph orchestration
- **13 AI agents** across 4 crews (4 + 5 + 2 + 4)
- **Offline/Online duality** — Deterministic fixtures or live Claude API
- **Streamlit dashboard** — 6-page interactive web UI with Guardian branding
- **CLI interface** — 5 Click commands for terminal-based operation
- **VM-21 reserve calculations** — CTE70, CTE90, Monte Carlo, sensitivity analysis
- **Black-Scholes Greeks** — Delta, gamma, vega, theta, rho with SABR calibration
- **Dynamic behavior modeling** — Moneyness-based lapse rates, withdrawal simulation
- **Stress testing** — 6 preset scenarios + custom what-if builder
- **Export** — CSV, Excel, PDF report generation
- **FRED integration** — Live treasury yields and market data
- **Fixture-driven testing** — 56+ tests, all runnable without API keys
