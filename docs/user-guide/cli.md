# CLI Reference

The `insurance-ai` CLI provides 5 commands for running crews from the terminal.

## Global Options

```bash
insurance-ai [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--online` | Use Claude API (requires `ANTHROPIC_API_KEY`) |
| `--offline` | Use fixtures (default) |
| `--debug` | Enable debug logging |
| `--help` | Show help |

## Commands

### `underwriting` — Medical Extraction & Risk Classification

```bash
insurance-ai underwriting [INPUT_FILE] [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `INPUT_FILE` | STR | `synthetic_applicant_001` | Input file or fixture ID |
| `--product` | ENUM | `VA_with_GLWB` | Product type: `VA_with_GLWB`, `FIA`, `RILA` |
| `--output` | PATH | — | Save results to JSON |

Runs the 4-agent underwriting crew: Extraction → Validation → Mortality → Approval.

### `reserve` — VM-21/VM-22 Reserves

```bash
insurance-ai reserve [INPUT_FILE] [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `INPUT_FILE` | STR | `synthetic_policy_001` | Input file or fixture ID |
| `--scenarios` | INT | 100 | Number of Monte Carlo scenarios |
| `--output` | PATH | — | Save results to JSON |

Runs the 5-agent reserve crew: Scenario Generation → Cash Flow → CTE → Sensitivity → Convergence.

### `hedging` — Greeks & Hedge Recommendations

```bash
insurance-ai hedging [INPUT_FILE] [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `INPUT_FILE` | STR | `synthetic_portfolio_001` | Input file or fixture ID |
| `--output` | PATH | — | Save results to JSON |

Calculates Black-Scholes Greeks, SABR calibration, and hedge effectiveness.

### `behavior` — Dynamic Lapse & Withdrawal Modeling

```bash
insurance-ai behavior [INPUT_FILE] [OPTIONS]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `INPUT_FILE` | STR | `synthetic_cohort_001` | Input file or fixture ID |
| `--output` | PATH | — | Save results to JSON |

Runs the 4-agent behavior crew: Lapse Modeling → Withdrawal Planning → Path Simulation → Sensitivity.

### `status` — Toolkit Status

```bash
insurance-ai status
```

Shows current configuration, available fixtures, and API key status.

## Examples

```bash
# Quick offline run
insurance-ai underwriting

# Full reserve calculation with 1000 scenarios
insurance-ai reserve synthetic_policy_001 --scenarios 1000 --output reserves.json

# Online mode with live Claude API
ANTHROPIC_API_KEY=sk-ant-... insurance-ai underwriting applicant.pdf --online
```
