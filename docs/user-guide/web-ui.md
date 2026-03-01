# Streamlit Dashboard

The Insurance AI Toolkit includes a full Streamlit web application with 6 interactive pages, Plotly charts, and Guardian branding.

## Launching

```bash
# Offline mode (default — no API keys)
INSURANCE_AI_MODE=offline streamlit run src/insurance_ai/web/app.py

# Online mode
ANTHROPIC_API_KEY=sk-... streamlit run src/insurance_ai/web/app.py
```

Dashboard opens at `http://localhost:8501`.

## Pages

### 1. Dashboard (Landing)

Overview page with navigation cards and system status. Shows execution mode (offline/online) and available crews.

### 2. Underwriting

- Medical record extraction from PDF or fixture
- Risk classification with confidence scores
- VBT mortality class mapping
- Approval decision with rationale

### 3. Reserves

- VM-21 CTE70/CTE90 calculations
- Monte Carlo scenario generation (GBM equity + Vasicek rates)
- CTE histogram visualization
- Sensitivity tornado chart (rates, volatility, lapse, withdrawal)
- Convergence analysis plot

### 4. Hedging

- Black-Scholes Greeks (delta, gamma, vega, theta, rho)
- Greeks heatmap across strike/maturity grid
- SABR volatility surface calibration
- Payoff diagrams
- Hedge recommendations with effectiveness scores

### 5. Behavior

- Dynamic lapse curves by moneyness (ITM < ATM < OTM)
- Withdrawal path modeling (static vs. dynamic ITM strategies)
- Reserve impact quantification
- Rate sensitivity analysis

### 6. Scenarios

- Preset stress scenarios: 2008 Crisis, March 2020, Rising Rates, etc.
- Custom what-if builder with parameter sliders
- Side-by-side scenario comparison
- Impact on reserves and hedging effectiveness

## Components

The dashboard uses reusable components in `web/components/`:

| Component | Purpose |
|-----------|---------|
| `charts.py` | 12+ Plotly chart functions with Guardian branding |
| `metrics.py` | KPI cards and formatted metric displays |
| `forms.py` | Input controls (sliders, selects, number inputs) |
| `warnings.py` | Error handling, status badges, alerts |
| `market_data.py` | FRED yield curve sidebar display |
| `bulk_upload.py` | CSV batch upload and processing |
| `export.py` | CSV/Excel/PDF export buttons |
| `pdf_report.py` | PDF report generation |
| `scenario_builder.py` | Interactive scenario parameter builder |

## Configuration

### Theme

Guardian branding configured in `.streamlit/config.toml` and `web/config.py`:

- Primary Blue: `#003DA5`
- Accent Gold: `#B8860B`
- Dark/light mode support

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INSURANCE_AI_MODE` | `offline` | `offline` or `online` |
| `ANTHROPIC_API_KEY` | — | Required for online mode |
| `FRED_API_KEY` | — | Optional, for live treasury yields |
