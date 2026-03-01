# Insurance AI Toolkit

**Agentic AI for annuity product lifecycle automation — underwriting, reserves, hedging, and policyholder behavior.**

The Insurance AI Toolkit uses multi-agent orchestration (LangGraph + Claude) to automate complex actuarial workflows for Variable Annuities (VA), Fixed Indexed Annuities (FIA), and Registered Index-Linked Annuities (RILA).

## Key Features

::::{grid} 2
:gutter: 3

:::{grid-item-card} 4-Crew Architecture
:link: user-guide/crews-overview
:link-type: doc

Underwriting, Reserves, Hedging, and Behavior crews — each with specialized AI agents orchestrated via LangGraph state graphs.
:::

:::{grid-item-card} Offline/Online Modes
:link: user-guide/fixtures
:link-type: doc

Run with deterministic fixtures (no API keys needed) or live Claude API. Fixtures enable fast CI/CD testing and reproducible demos.
:::

:::{grid-item-card} Streamlit Dashboard
:link: user-guide/web-ui
:link-type: doc

Interactive 6-page web UI with Guardian branding, Plotly charts, scenario comparison, and PDF export.
:::

:::{grid-item-card} CLI Interface
:link: user-guide/cli
:link-type: doc

5 Click commands for running any crew from the terminal. Supports both offline and online modes.
:::
::::

## Quick Start

```bash
# Install
pip install -e ".[web]"

# Run Streamlit dashboard (offline mode — no API keys needed)
INSURANCE_AI_MODE=offline streamlit run src/insurance_ai/web/app.py

# Or use the CLI
insurance-ai underwriting synthetic_applicant_001
insurance-ai reserve synthetic_policy_001 --scenarios 1000
```

```{toctree}
:maxdepth: 2
:caption: Getting Started

getting-started
```

```{toctree}
:maxdepth: 2
:caption: User Guide

user-guide/cli
user-guide/web-ui
user-guide/crews-overview
user-guide/underwriting
user-guide/reserves
user-guide/hedging
user-guide/behavior
user-guide/scenarios
user-guide/fixtures
```

```{toctree}
:maxdepth: 2
:caption: Reference

architecture
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
api/config
api/underwriting
api/reserves
api/hedging
api/behavior
api/data
api/web-components
```

```{toctree}
:maxdepth: 1
:caption: Project

changelog
glossary
```
