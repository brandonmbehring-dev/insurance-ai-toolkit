# Crew Architecture

The toolkit organizes work into 4 specialized crews, each implemented as a LangGraph `StateGraph` with multiple AI agents.

## Design Pattern

All crews follow the same LangGraph pattern:

```python
StateGraph(state_schema=CrewState)
  .add_node("agent_1", agent_1_function)
  .add_node("agent_2", agent_2_function)
  .add_edge("agent_1", "agent_2")
  .add_edge("agent_2", END)
  .compile()
  .invoke(initial_state)
```

Each agent function takes the crew state, performs its work (using tools or Claude), and returns the updated state. Agents are connected in a linear pipeline.

## The 4 Crews

### 1. Underwriting Crew (4 agents)

**Purpose**: Medical record extraction and risk classification.

```
Extraction → Validation → Mortality → Approval
```

- **Extraction** — Parse health metrics from PDF/fixture
- **Validation** — Check data consistency and completeness
- **Mortality** — Apply SOA 2012 IAM, map to VBT risk class
- **Approval** — Evaluate product-specific rules, issue decision

**Output**: Risk class, approval decision (APPROVE/DENY), confidence score (0.7–0.99)

### 2. Reserve Crew (5 agents)

**Purpose**: VM-21/VM-22 regulatory reserve calculations.

```
Scenario Generation → Cash Flow → CTE Calculation → Sensitivity → Convergence
```

- **Scenario Generation** — GBM equity paths + Vasicek rate paths (seed-deterministic)
- **Cash Flow Projection** — Liability projections across all scenarios
- **CTE Calculation** — CTE70, CTE90, percentiles, risk margin
- **Sensitivity Analysis** — Shock analysis (rates ±50bps, vol ±5%, lapse ±2%)
- **Convergence Validation** — Verify < 2% error between n=1000 vs n=10000

**Validation invariants**: CTE70 ≥ Mean (by definition), convergence < 2%, sensitivity monotonicity.

### 3. Hedging Crew

**Purpose**: Greeks calculation and hedge recommendations.

- Black-Scholes analytical Greeks (delta, gamma, vega, theta, rho)
- SABR volatility surface calibration
- Portfolio hedge effectiveness > 80%
- Instrument recommendations (puts, swaptions, etc.)

### 4. Behavior Crew (4 agents)

**Purpose**: Dynamic policyholder behavior modeling.

```
Lapse Modeling → Withdrawal Planning → Path Simulation → Sensitivity
```

- **Lapse Modeling** — Dynamic lapse rates based on moneyness (ITM < ATM < OTM)
- **Withdrawal Planning** — Model withdrawal behavior (static vs. dynamic ITM)
- **Path Simulation** — Monte Carlo simulation of 1000 lapse + withdrawal paths
- **Sensitivity Analysis** — Rate shock impact, path convergence < 3%

**Key relationship**: Lapse rate monotonicity — ITM lapse < ATM lapse < OTM lapse (≥ 20% difference).

## State Management

Each crew uses a typed state dataclass (via Pydantic or Python dataclasses) that flows through all agents. The state accumulates results — each agent adds its output fields while preserving upstream state.

See the individual crew pages for detailed state schemas:

- {doc}`underwriting`
- {doc}`reserves`
- {doc}`hedging`
- {doc}`behavior`
