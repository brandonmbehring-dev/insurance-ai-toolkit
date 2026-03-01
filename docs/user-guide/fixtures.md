# Offline Mode & Fixtures

The toolkit supports deterministic offline operation using pre-recorded JSON fixtures, enabling fast testing, CI/CD, and demos without API keys.

## How It Works

In offline mode (`INSURANCE_AI_MODE=offline`, the default), each crew loads pre-recorded JSON outputs instead of calling Claude or external APIs.

```
Online Mode:  Input → Claude API → Processing → Output
Offline Mode: Input → Fixture Load → Identical Output
```

## Fixture Location

Fixtures are stored in `tests/fixtures/` organized by crew:

```
tests/fixtures/
├── underwriting/
│   └── synthetic_applicant_001.json
├── reserve/
│   └── synthetic_policy_001.json
├── hedging/
│   └── synthetic_portfolio_001.json
└── behavior/
    └── synthetic_cohort_001.json
```

## Benefits

| Benefit | Description |
|---------|-------------|
| **No API costs** | Zero Claude API calls |
| **Deterministic** | Same input → identical output every time |
| **Fast** | < 100ms fixture load vs seconds for API calls |
| **CI/CD ready** | Tests run without secrets |
| **Demo friendly** | Consistent, polished results for presentations |
| **Reproducible** | Same seed → identical Monte Carlo paths |

## Adding Custom Fixtures

1. Run the crew in online mode with `--output`:
   ```bash
   ANTHROPIC_API_KEY=sk-... insurance-ai reserve policy.json --online --output new_fixture.json
   ```
2. Move the output to `tests/fixtures/<crew>/`
3. Reference by fixture ID in CLI or tests

## Testing with Fixtures

All unit tests use offline mode via the `INSURANCE_AI_MODE=offline` environment variable:

```python
@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.setenv("INSURANCE_AI_MODE", "offline")
```
