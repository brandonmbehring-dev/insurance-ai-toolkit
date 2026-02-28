# Architecture

## System Overview

InsuranceAI Toolkit is an agentic AI system built on LangGraph that automates Variable Annuity (VA), Fixed Index Annuity (FIA), and RILA workflows. It operates in two modes:

- **Offline mode** (default): Deterministic fixtures, no API keys required
- **Online mode**: Claude Vision + market APIs for production use

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                      │
│  Dashboard │ Underwriting │ Reserves │ Hedging │ Behavior│
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Crew Orchestrator                      │
│              (LangGraph State Machine)                   │
└──┬──────────┬──────────┬──────────┬─────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌───────┐ ┌────────┐
│Under-│ │Reserve │ │Hedging│ │Behavior│
│write │ │  Crew  │ │ Crew  │ │  Crew  │
└──────┘ └────────┘ └───────┘ └────────┘
```

## Crews

Each crew is a self-contained LangGraph workflow with specialized agents:

| Crew | Purpose | Key Calculations |
|------|---------|-----------------|
| **Underwriting** | Medical PDF extraction, risk classification | Mortality loading, preferred class |
| **Reserve** | Regulatory liability calculation | VM-21, CTE70, stochastic scenarios |
| **Hedging** | Greek computation, hedge recommendations | Delta, gamma, vega, rho |
| **Behavior** | Policyholder behavior modeling | Dynamic lapse, withdrawal utilization |

### Offline vs Online Mode

```python
# Offline (default): Uses deterministic fixtures
INSURANCE_AI_MODE=offline  # or unset

# Online: Uses Claude Vision for PDF extraction, live market data
INSURANCE_AI_MODE=online
ANTHROPIC_API_KEY=sk-...
```

Offline mode reads from `tests/fixtures/` — identical outputs every run, no API costs.

## Directory Structure

```
src/insurance_ai/
├── config.py              # Mode management (offline/online)
├── cli.py                 # CLI entry point
├── crews/                 # LangGraph crew implementations
│   ├── underwriting/      # Medical extraction, risk scoring
│   ├── reserve/           # VM-21 CTE70 calculations
│   ├── hedging/           # Greeks, hedge strategy
│   └── behavior/          # Lapse, withdrawal modeling
├── data/                  # Data models and schemas
└── web/                   # Streamlit application
    ├── app.py             # Main app entry
    ├── components/        # Shared UI components
    └── pages/             # Per-crew pages
```

## Fixture System

Every crew has corresponding test fixtures in `tests/fixtures/`:

```
tests/fixtures/
├── underwriting/          # Sample medical PDFs, risk outputs
├── reserve/               # CTE70 scenarios, VM-21 results
├── hedging/               # Greek calculations, market data
└── behavior/              # Lapse curves, withdrawal patterns
```

Fixtures enable:
- **Deterministic testing** — No API variability
- **Fast iteration** — No network round-trips
- **CI/CD compatibility** — No secrets required
- **Demo mode** — Live Streamlit app with no API keys

## Technology Stack

- **Orchestration**: LangGraph (state machine workflows)
- **LLM**: Anthropic Claude (online mode)
- **Web UI**: Streamlit
- **PDF Processing**: Claude Vision (online) / fixtures (offline)
- **Testing**: pytest with fixture-based validation
