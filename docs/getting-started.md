# Getting Started

## Installation

### Basic (CLI only)

```bash
pip install -e .
```

### With Streamlit Dashboard

```bash
pip install -e ".[web]"
```

### Full Installation

```bash
pip install -e ".[all]"
```

### Extras

| Extra | Purpose |
|-------|---------|
| `web` | Streamlit + Plotly dashboard |
| `viz` | Jupyter, matplotlib, seaborn |
| `pdf` | PDF extraction (pdf2image, tesseract) |
| `dev` | Testing, linting, type checking |
| `docs` | Sphinx documentation build |

## Execution Modes

### Offline Mode (Default)

No API keys required. Uses pre-recorded JSON fixtures for deterministic, reproducible results.

```bash
# CLI
insurance-ai underwriting synthetic_applicant_001

# Dashboard
INSURANCE_AI_MODE=offline streamlit run src/insurance_ai/web/app.py
```

### Online Mode

Requires Anthropic API key. Uses Claude Vision for PDF extraction and live inference.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
insurance-ai underwriting applicant.json --online
```

Optional: Set `FRED_API_KEY` for live treasury yields.

## Running the Dashboard

```bash
# Offline mode (recommended for first run)
INSURANCE_AI_MODE=offline streamlit run src/insurance_ai/web/app.py

# Online mode (requires API keys)
ANTHROPIC_API_KEY=sk-... streamlit run src/insurance_ai/web/app.py
```

The dashboard launches at `http://localhost:8501` with 6 pages:

1. **Dashboard** — Overview and navigation
2. **Underwriting** — Medical extraction and risk classification
3. **Reserves** — VM-21 CTE calculations and sensitivity
4. **Hedging** — Greeks analysis and hedge recommendations
5. **Behavior** — Dynamic lapse and withdrawal modeling
6. **Scenarios** — Stress testing and what-if analysis

## CLI Quick Reference

```bash
insurance-ai [--online|--offline] [--debug] COMMAND [OPTIONS]

Commands:
  underwriting    Medical extraction & risk classification
  reserve         VM-21/VM-22 regulatory reserves
  hedging         Greeks & hedge recommendations
  behavior        Dynamic lapse & withdrawal modeling
  status          Toolkit configuration info
```

## Next Steps

- {doc}`user-guide/crews-overview` — Understand the 4-crew architecture
- {doc}`user-guide/web-ui` — Dashboard walkthrough
- {doc}`user-guide/fixtures` — How offline mode works
- {doc}`architecture` — System design and decisions
