# InsuranceAI Toolkit: Annuity Product Lifecycle Automation

**Agentic AI system for automating Variable Annuity (VA), Fixed Index Annuity (FIA), and Registered Index-Linked Annuity (RILA) workflows with guaranteed living benefits.**

![Status](https://img.shields.io/badge/status-prototype-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

Insurance companies spend thousands of hours annually on manual annuity operations:

1. **New Business Origination** – Medical PDFs → manual extraction → weeks of underwriting delays
2. **Ongoing Liability Management** – Regulatory scenarios (VM-20/VM-21) → manual calculations → weeks of reserve analysis
3. **Embedded Option Risk** – Volatility surfaces shift → manual Greeks → delayed hedge decisions
4. **Policyholder Behavior** – Rate environments change → static lapse curves miss dynamics → understated reserves

**InsuranceAI Toolkit automates all four phases** using specialized agentic crews with Claude AI, LLM reasoning, and deterministic offline mode for testing.

---

## Quick Start

### Installation

**Prerequisites:** Python 3.10+, Poppler (for PDF extraction)

```bash
# Install system dependencies
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Clone and install
git clone https://github.com/yourusername/insurance-ai-toolkit.git
cd insurance_ai_toolkit
pip install -e .
```

### Try the Demo (No API Keys Required)

```bash
# Run offline (uses pre-recorded fixtures)
insurance-ai underwriting

# View risk classification output
# Output: JSON with extracted health metrics, mortality class, VBT adjustments
```

All demos work in **offline mode by default** using synthetic fixtures. No API keys needed.

### Enable Online Mode (Optional)

```bash
# Run with Claude Vision API (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-... insurance-ai underwriting applicant.json --online
```

---

## The Four Crews

### 1️⃣ UnderwritingCrew – Medical Data Extraction & Risk Classification

Processes medical records (PDFs or structured data) to extract health metrics and assign mortality risk classes.

**Supported Products:** VA + GLWB, FIA, RILA

**Validation Criteria:**
- ✅ Field-level extraction accuracy: **>95%** on known fields
- ✅ Schema conformance: **100%** (Pydantic validation)
- ✅ Confidence thresholds: Flag extractions with confidence <0.7
- ✅ Idempotence: Same fixture → identical output

```bash
insurance-ai underwriting synthetic_applicant_001
# Output: Risk class, VBT adjustments, extracted health fields
```

### 2️⃣ ReserveCrew – Regulatory Reserve Calculations

Calculates Principle-Based Reserves (VM-21 for VAs, VM-22 for FIAs/RILAs) including CTE70 tail risk.

**Supported Products:** VA + GLWB/GMWB, FIA, RILA

**Validation Criteria:**
- ✅ CTE math invariants: **CTE70 ≥ mean** reserve (always true)
- ✅ Convergence: **<2%** error (n=1000 vs n=10000)
- ✅ Sensitivity monotonicity: Rate +50bps → reserve increases **≥5%**
- ✅ Determinism: Fixed seed → **8 decimal place** reproducibility

```bash
insurance-ai reserve synthetic_policy_001 --scenarios 100
# Output: CTE70 reserve, sensitivity analysis, VM-21 compliance
```

### 3️⃣ HedgingCrew – Volatility Calibration & Hedging

Calibrates volatility surfaces (SABR/Heston), calculates option Greeks, and recommends hedge strategies.

**Supported Products:** VA + GLWB, FIA, RILA

**Validation Criteria:**
- ✅ Greeks accuracy: **<0.1%** error vs Black-Scholes
- ✅ Hedge effectiveness: Portfolio delta reduction **>80%**
- ✅ SABR calibration: RMSE **<5%** on synthetic surfaces

```bash
insurance-ai hedging synthetic_portfolio_001
# Output: Greeks, SABR parameters, hedge recommendations, effectiveness
```

### 4️⃣ BehaviorCrew – Dynamic Lapse & Policyholder Modeling

Models dynamic policyholder behavior (surrenders, withdrawals) based on moneyness, rates, and market conditions.

**Supported Products:** VA + GLWB, FIA, RILA

**Validation Criteria:**
- ✅ Lapse monotonicity: **ITM < ATM < OTM** (≥20% difference)
- ✅ Impact sensibility: Rate shock +100bps → reserve increases ✅
- ✅ Path convergence: **<3%** error (n=1000 vs n=10000)

```bash
insurance-ai behavior synthetic_cohort_001
# Output: Dynamic lapse curves, withdrawal behavior, reserve impact
```

---

## Architecture

### Offline vs Online Mode

All tools work in **offline mode by default** with pre-recorded JSON fixtures:

```
Offline Mode (Default)          Online Mode (Opt-In)
├─ Uses JSON fixtures           ├─ Claude Vision API
├─ No API keys required         ├─ Real PDF extraction
├─ Deterministic (same seed)    ├─ Requires ANTHROPIC_API_KEY
├─ Fast (fixtures <100ms)       ├─ Full feature set
└─ Perfect for CI/demo          └─ Full accuracy
```

### Project Structure

```
insurance_ai_toolkit/
├── src/insurance_ai/
│   ├── __init__.py             # Package initialization
│   ├── config.py               # Offline/online mode, fixture loading
│   └── cli.py                  # CLI with 4 crew commands
├── tests/
│   ├── fixtures/               # Pre-recorded outputs
│   │   ├── underwriting/
│   │   ├── reserve/
│   │   ├── hedging/
│   │   └── behavior/
│   └── unit/                   # Unit tests
├── docs/
│   └── GLOSSARY.md             # Insurance terminology reference
├── pyproject.toml              # Dependencies, build config
└── README.md                   # This file
```

### Configuration

Set offline/online mode via environment variable or flag:

```bash
# Default: offline mode
insurance-ai underwriting

# Explicit offline
insurance-ai underwriting --offline

# Online mode (requires API key)
ANTHROPIC_API_KEY=sk-... insurance-ai underwriting --online
```

---

## Installation Details

### Dependencies

**Core dependencies:**
- `anthropic>=0.25.0` – Claude AI SDK
- `langgraph>=0.0.1` – Multi-agent orchestration
- `langchain>=0.1.0` – AI agent framework
- `pydantic>=2.0.0` – Data validation
- `click>=8.1.0` – CLI interface

**Optional extras:**
- `[dev]` – pytest, black, ruff, mypy for development
- `[viz]` – jupyter, matplotlib, seaborn for notebooks
- `[pdf]` – pdf2image, pillow, pytesseract for PDF extraction
- `[all]` – All extras

### Install for Development

```bash
git clone https://github.com/yourusername/insurance-ai-toolkit
cd insurance_ai_toolkit

# Install in editable mode with dev dependencies
pip install -e ".[dev,viz]"

# Run tests
pytest tests/ -v

# Check code quality
black --check src/
ruff check src/
mypy src/
```

---

## Validation & Testing

Each crew includes outcome-based validation against known benchmarks:

### Test Coverage

- **UnderwritingCrew:** Field extraction accuracy, schema conformance, confidence thresholds
- **ReserveCrew:** CTE invariants, convergence checks, sensitivity monotonicity
- **HedgingCrew:** Greeks accuracy, hedge effectiveness, calibration quality
- **BehaviorCrew:** Lapse monotonicity, impact sensibility, path convergence

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/insurance_ai --cov-report=html

# Run specific crew tests
pytest tests/unit/test_underwriting_crew.py -v
```

---

## Disclaimers

### ⚠️ PROTOTYPE STATUS

This is a **portfolio-grade prototype** demonstrating agentic AI applied to insurance actuarial workflows. Not for production regulatory filing without professional actuarial review.

### UnderwritingCrew
Uses **synthetic medical data only**. Not medical advice. No PHI (Protected Health Information).

### ReserveCrew
Demonstrates **regulatory calculation concepts** (VM-21/VM-22). **NOT FOR PRODUCTION REGULATORY FILING.** Use NAIC-prescribed methods with qualified actuaries.

### HedgingCrew
**Educational demonstration only.** Not investment advice. Hedge recommendations are illustrative.

### BehaviorCrew
**Illustrative behavioral modeling only.** Not for product pricing or reserve certification.

---

## Supported Products

| Crew | VA + GLWB | FIA | RILA | Features |
|------|-----------|-----|------|----------|
| Underwriting | ✅ | ✅ | ✅ | Medical extraction, mortality classification |
| Reserve | ✅ | ✅ | ✅ | VM-21/VM-22, CTE70, scenario analysis |
| Hedging | ✅ | ✅ | ✅ | Greeks, SABR calibration, hedge recs |
| Behavior | ✅ | ✅ | ✅ | Dynamic lapse, withdrawal modeling |

---

## Roadmap

### ✅ v0.1.0 (Current)
- Offline mode with JSON fixtures
- CLI for all 4 crews
- Schema validation (Pydantic)
- Outcome-based validation metrics

### 🚀 v0.2.0 (Planned)
- Claude Vision API integration for PDFs
- Full online mode validation
- Jupyter notebooks for each crew (01_underwriting_crew_demo.ipynb, etc.)
- Multi-product examples (VA/FIA/RILA scenarios)

### 🔮 Future
- Streamlit web UI
- Real-world market data integration
- Production deployment patterns
- PyPI publishing

---

## Contributing

Contributions welcome! Focus areas:
- Additional fixture scenarios
- Crew implementations
- Integration tests
- Documentation improvements

See `ARCHITECTURE.md` for design decisions and `GLOSSARY.md` for insurance terminology.

---

## License

MIT License – See LICENSE file

---

## Questions?

- **Offline mode not working?** Check `tests/fixtures/` directory structure
- **API key issues?** Ensure `ANTHROPIC_API_KEY` is set for online mode
- **Installation issues?** Verify Poppler installed and Python 3.10+

For detailed design decisions, see:
- `docs/GLOSSARY.md` – Insurance & actuarial terminology
- `docs/ARCHITECTURE.md` – System design (coming soon)
- `docs/plans/InsuranceAI_Toolkit_8Week_Plan.md` – 8-week implementation roadmap

---

**Last Updated:** 2025-12-15
**Status:** Portfolio-grade prototype
**Maintained By:** Brandon Behring
