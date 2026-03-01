# Underwriting Crew

Medical record extraction, risk classification, and approval decisions.

## Workflow

```
Extraction → Validation → Mortality → Approval
```

### Agent 1: Extraction

Parses health metrics from medical records (PDF in online mode, JSON fixtures in offline mode).

Extracts: age, gender, height, weight, BMI, blood pressure, cholesterol, medications, conditions.

### Agent 2: Validation

Checks data consistency and completeness:
- Required fields present
- Values in physiologically valid ranges
- Cross-field consistency (e.g., BMI matches height/weight)

### Agent 3: Mortality

Applies SOA 2012 Individual Annuity Mortality table:
- Calculates health adjustment factor from extracted metrics
- Maps to VBT risk class: Preferred Plus, Preferred, Standard, or Rated
- Produces mortality rate adjustment

### Agent 4: Approval

Evaluates product-specific underwriting rules:
- Product type constraints (VA with GLWB, FIA, RILA)
- Age limits, risk class thresholds
- Issues final decision: APPROVE or DENY
- Generates confidence score (0.7–0.99)

## State Schema

```python
class UnderwritingState:
    applicant_id: str
    product_type: ProductType      # VA_with_GLWB, FIA, RILA
    age: int
    gender: str
    health_metrics: dict           # Extracted medical data
    risk_class: RiskClass          # Preferred+, Preferred, Standard, Rated
    approval_decision: str         # APPROVE or DENY
    confidence: float              # 0.7–0.99
```

## CLI Usage

```bash
# Offline (fixture)
insurance-ai underwriting synthetic_applicant_001

# Online (PDF extraction via Claude Vision)
ANTHROPIC_API_KEY=sk-... insurance-ai underwriting applicant.pdf --online

# Specify product type
insurance-ai underwriting --product FIA
```

## Validation Metrics

- Extraction accuracy: > 95% field-level match
- Schema conformance: 100% (all required fields populated)
- Confidence calibration: flagged when < 0.7
