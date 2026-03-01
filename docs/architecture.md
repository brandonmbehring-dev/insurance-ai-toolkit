# Architecture

## System Overview

```
                    ┌──────────────┐
                    │   CLI / Web  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │ Config  │  │  Data  │  │  Web   │
         │ (mode)  │  │ (FRED) │  │(Strlit)│
         └────┬────┘  └───┬────┘  └───┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────▼────────────┐
              │    LangGraph Crews      │
              │  ┌────┐ ┌────┐ ┌────┐  │
              │  │ UW │ │ RES│ │HEDG│  │
              │  └────┘ └────┘ └────┘  │
              │          ┌────┐        │
              │          │BEHV│        │
              │          └────┘        │
              └────────────────────────┘
```

## Directory Structure

```
src/insurance_ai/
├── config.py              # Mode management (offline/online)
├── cli.py                 # Click CLI (5 commands)
├── data/
│   ├── fred_client.py     # FRED API with caching
│   └── market_data.py     # Market data aggregation
├── crews/
│   ├── underwriting/      # 4 agents: extract → validate → mortality → approve
│   ├── reserve/           # 5 agents: scenarios → cashflow → CTE → sensitivity → convergence
│   ├── hedging/           # Greeks, SABR, hedge recommendations
│   └── behavior/          # 4 agents: lapse → withdrawal → simulation → sensitivity
└── web/
    ├── app.py             # Streamlit entry point
    ├── config.py          # Theme, execution mode
    ├── components/        # 11 reusable UI components
    ├── pages/             # 6 Streamlit pages
    ├── data/              # Demo scenarios, constants
    └── utils/             # State management, formatters
```

## Key Design Decisions

### LangGraph State Graphs

Each crew is a `StateGraph` with typed state that flows through a linear agent pipeline. This provides:
- Clear data flow (each agent reads and extends state)
- Easy debugging (inspect state between agents)
- Deterministic execution order

### Offline/Online Duality

The `Config` class manages execution mode:
- **Offline**: Loads pre-recorded JSON fixtures (deterministic, fast, no API costs)
- **Online**: Calls Claude API for inference and FRED API for market data

This duality enables:
- CI/CD testing without secrets
- Fast demos with polished results
- Production use with live data

### Fixture-Driven Testing

Tests use `INSURANCE_AI_MODE=offline` to load fixtures instead of calling APIs. This makes tests:
- Fast (< 100ms per test)
- Deterministic (no network variability)
- Free (no API costs)

### Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| CLI (`cli.py`) | User interaction, argument parsing |
| Config (`config.py`) | Mode management, fixture loading |
| Crews (`crews/`) | Business logic, AI agent orchestration |
| Data (`data/`) | External data access (FRED, market data) |
| Web (`web/`) | Dashboard UI, charts, export |

## Technology Stack

| Component | Technology |
|-----------|-----------|
| AI Orchestration | LangGraph (StateGraph) |
| LLM | Claude (via Anthropic SDK) |
| Data Validation | Pydantic |
| CLI | Click |
| Web UI | Streamlit |
| Charts | Plotly |
| Market Data | FRED API |
| Testing | pytest with offline fixtures |
