# Contributing to InsuranceAI Toolkit

Thank you for your interest in contributing! This project automates annuity product lifecycle workflows using agentic AI.

## Development Setup

```bash
git clone https://github.com/brandon-behring/insurance_ai_toolkit.git
cd insurance_ai_toolkit
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run tests (offline mode, no API keys needed)
pytest tests/ -v
```

### System Dependencies

- **Python 3.10+**
- **Poppler** (for PDF processing): `sudo apt-get install poppler-utils`

## Running the Web UI

```bash
streamlit run src/insurance_ai/web/app.py
```

The app runs in **offline mode** by default, using deterministic fixtures from `tests/fixtures/`.

## Code Style

- **Formatter**: Black with 100-character line length
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

## Testing

All tests run against fixture data by default (no API keys required):

```bash
# Full suite
pytest tests/ -v

# Specific crew
pytest tests/test_reserve.py -v
```

### Adding Test Fixtures

Place new fixtures in `tests/fixtures/<crew>/` following the existing patterns. Fixtures should be deterministic and representative of real-world data.

## Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Write tests** for new functionality
3. **Ensure all tests pass**: `pytest tests/ -v`
4. **Submit PR** with a clear description

## Focus Areas

We especially welcome contributions in:
- Additional fixture scenarios for edge cases
- New crew implementations
- Integration tests
- Documentation improvements
- Notebook tutorials

## Questions?

Open an issue for questions about architecture, insurance domain concepts, or implementation approach.
