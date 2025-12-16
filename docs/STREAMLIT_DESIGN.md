# Streamlit Web UI Architecture Design

## Overview

This document specifies the architectural design for the InsuranceAI Toolkit Streamlit web UI, including state management, crew orchestration, error handling, and configuration strategy.

---

## 1. Execution Model: Hybrid Sequential

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interaction Layer                        │
│  Sidebar: Scenario selector + Run button + Mode toggle          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    User clicks "Run"
                         │
        ┌────────────────▼────────────────┐
        │   1. Underwriting Crew         │
        │   (Extract → Classify → Approve)
        │   ~1-2 seconds                  │
        └────────────────┬────────────────┘
                         │
                    Check approval
                         │
            ┌────────────┴────────────┐
            │                         │
    ❌ DECLINED              ✅ APPROVED
            │                         │
      Skip downstream           Continue
            │                         │
            │              ┌──────────┴──────────┐
            │              │                     │
            │        2A. Reserve Crew     2B. Behavior Crew
            │        (Scenarios → CTE)    (Lapse → Paths)
            │        ~1-2s parallel      ~1-2s parallel
            │              │                     │
            │              └──────────┬──────────┘
            │                         │
            │              (Optional) 3. Hedging Crew
            │              (Greeks → Hedge)
            │              ~1-2 seconds
            │                         │
            └─────────────┬───────────┘
                          │
              ┌───────────▼──────────┐
              │   Dashboard Display  │
              │   - Workflow status  │
              │   - KPI metrics      │
              │   - Charts           │
              └──────────────────────┘
```

### Execution Strategy

1. **Underwriting always first**
   - Gates all downstream processing
   - If approval decision is "DECLINE", skip Reserve/Behavior/Hedging
   - If approval is "APPROVE", continue to parallel phase

2. **Reserve + Behavior run in parallel** (Decision 1: Hybrid Sequential)
   - No dependency between them
   - Both consume Underwriting output
   - Faster than sequential (2s vs 4s)
   - Both complete before Hedging starts

3. **Hedging last** (optional)
   - Consumes Reserve output (Greeks depend on reserve amount)
   - Skipped if Reserve fails

4. **Total execution time**
   - Success path: ~4-5 seconds (1-2s per crew + overhead)
   - Failure path: ~1-2 seconds (early exit)

---

## 2. Session State Structure

### Root State: `st.session_state`

```python
st.session_state = {
    # ===== USER INPUTS =====
    "selected_scenario": str,          # e.g., "base_case", "high_risk"
    "selected_mode": str,              # "offline" or "online"

    # ===== EXECUTION CONTROL =====
    "workflow_status": str,            # "idle", "running", "completed", "error"
    "execution_timestamp": datetime,   # When workflow last ran

    # ===== CREW RESULTS =====
    "underwriting_result": dict,       # UnderwritingState output (or None if declined)
    "underwriting_status": str,        # "success", "failed", "skipped"
    "underwriting_approval": bool,     # True = approved, False = declined

    "reserve_result": dict,            # ReserveState output (or None)
    "reserve_status": str,             # "success", "failed", "skipped"

    "behavior_result": dict,           # BehaviorState output (or None)
    "behavior_status": str,            # "success", "failed", "skipped"

    "hedging_result": dict,            # HedgingState output (or None)
    "hedging_status": str,             # "success", "failed", "skipped"

    # ===== ERROR TRACKING =====
    "execution_errors": list[dict],    # [{crew: str, error: str, timestamp: datetime}]

    # ===== FIXTURES =====
    "current_fixture": dict,           # Full loaded fixture data
}
```

### State Initialization

```python
def initialize_session_state():
    """Initialize empty session state on app startup."""
    if "workflow_status" not in st.session_state:
        st.session_state.selected_scenario = "base_case"
        st.session_state.selected_mode = "offline"
        st.session_state.workflow_status = "idle"
        st.session_state.execution_errors = []

        # Result dicts
        st.session_state.underwriting_result = None
        st.session_state.reserve_result = None
        st.session_state.behavior_result = None
        st.session_state.hedging_result = None

        # Status tracking
        st.session_state.underwriting_status = None
        st.session_state.reserve_status = None
        st.session_state.behavior_status = None
        st.session_state.hedging_status = None
```

---

## 3. State Orchestration: Execution Flow

### Core Orchestration Function

Located in: `src/insurance_ai/web/utils/state_manager.py`

```python
def run_workflow(
    scenario_id: str,
    mode: str = "offline"
) -> None:
    """
    Execute the full workflow: UW → (Reserve + Behavior parallel) → Hedging.

    Updates st.session_state with results.

    Args:
        scenario_id: Identifier for the scenario fixture (e.g., "base_case")
        mode: "offline" (fixtures) or "online" (Claude API)
    """
    # 1. Set status to running
    st.session_state.workflow_status = "running"
    st.session_state.execution_errors = []

    # 2. Load fixture
    fixture = load_fixture(scenario_id, mode)
    st.session_state.current_fixture = fixture

    # 3. Run Underwriting
    try:
        uw_result = run_underwriting_crew(fixture, mode)
        st.session_state.underwriting_result = uw_result
        st.session_state.underwriting_status = "success"
        st.session_state.underwriting_approval = uw_result.get("approval_decision") == "APPROVE"
    except Exception as e:
        st.session_state.underwriting_status = "failed"
        st.session_state.execution_errors.append({
            "crew": "underwriting",
            "error": str(e),
            "timestamp": datetime.now()
        })
        st.session_state.workflow_status = "error"
        return  # Early exit

    # 4. Check approval gate
    if not st.session_state.underwriting_approval:
        st.session_state.reserve_status = "skipped"
        st.session_state.behavior_status = "skipped"
        st.session_state.hedging_status = "skipped"
        st.session_state.workflow_status = "completed"
        return  # Early exit

    # 5. Run Reserve + Behavior in parallel
    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            reserve_future = executor.submit(
                run_reserve_crew,
                st.session_state.underwriting_result,
                mode
            )
            behavior_future = executor.submit(
                run_behavior_crew,
                st.session_state.underwriting_result,
                mode
            )

            # Collect results
            st.session_state.reserve_result = reserve_future.result()
            st.session_state.reserve_status = "success"

            st.session_state.behavior_result = behavior_future.result()
            st.session_state.behavior_status = "success"
    except Exception as e:
        # Graceful degradation: capture error but continue
        crew_name = str(e).split(":")[0]
        st.session_state.execution_errors.append({
            "crew": crew_name,
            "error": str(e),
            "timestamp": datetime.now()
        })
        if "reserve" in str(e).lower():
            st.session_state.reserve_status = "failed"
        else:
            st.session_state.behavior_status = "failed"

    # 6. Run Hedging (optional, if reserves calculated)
    if st.session_state.reserve_status == "success":
        try:
            st.session_state.hedging_result = run_hedging_crew(
                st.session_state.reserve_result,
                mode
            )
            st.session_state.hedging_status = "success"
        except Exception as e:
            st.session_state.hedging_status = "failed"
            st.session_state.execution_errors.append({
                "crew": "hedging",
                "error": str(e),
                "timestamp": datetime.now()
            })
    else:
        st.session_state.hedging_status = "skipped"

    # 7. Mark workflow complete
    st.session_state.workflow_status = "completed"
    st.session_state.execution_timestamp = datetime.now()
```

---

## 4. Error Handling: Graceful Degradation

### Strategy (Decision 4)

When a crew fails:
1. **Capture error message** with crew name and timestamp
2. **Skip that crew** (mark status as "failed")
3. **Continue with other crews** (if possible)
4. **Display warning banners** on dashboard (not red errors, but yellow warnings)

### Error Display in Dashboard

```python
def display_workflow_status():
    """Display workflow status with color-coded crew states."""

    if st.session_state.workflow_status == "idle":
        st.info("Select a scenario and click 'Run' to begin")
        return

    # Status indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        uw_status = st.session_state.underwriting_status
        if uw_status == "success":
            st.success("✅ Underwriting")
        elif uw_status == "failed":
            st.error("❌ Underwriting")
        elif uw_status == "skipped":
            st.info("⏭️ Underwriting")

    with col2:
        res_status = st.session_state.reserve_status
        if res_status == "success":
            st.success("✅ Reserves")
        elif res_status == "failed":
            st.warning("⚠️ Reserves (failed)")
        elif res_status == "skipped":
            st.info("⏭️ Reserves")

    # ... similar for col3 (behavior), col4 (hedging)

    # Display error messages if any
    if st.session_state.execution_errors:
        st.warning("⚠️ Some crews encountered issues:")
        for error_record in st.session_state.execution_errors:
            st.caption(f"**{error_record['crew']}**: {error_record['error']}")
```

### When to Skip vs. Fail

| Crew | Condition | Action |
|------|-----------|--------|
| Underwriting | Error | FAIL - halt workflow (decision gate) |
| Underwriting | Declined | SKIP - all downstream (policy approved) |
| Reserve | Error | FAIL - skip Hedging, continue Behavior |
| Behavior | Error | FAIL - skip to Hedging |
| Hedging | Error | FAIL - no downstream, display warning |

---

## 5. Mode Switching: Offline ↔ Online

### Configuration Strategy (Decision 5)

Located in: `src/insurance_ai/web/config.py`

```python
import os
from enum import Enum

class ExecutionMode(Enum):
    OFFLINE = "offline"
    ONLINE = "online"

# Read from environment, default to offline
EXECUTION_MODE = os.getenv("INSURANCE_AI_MODE", "offline")
FIXTURES_DIR = os.getenv("INSURANCE_AI_FIXTURES_DIR", "tests/fixtures/")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)

def get_execution_mode() -> ExecutionMode:
    """Get current mode from env or st.session_state."""
    if "selected_mode" in st.session_state:
        return ExecutionMode(st.session_state.selected_mode)
    return ExecutionMode(EXECUTION_MODE)

def validate_mode(mode: str) -> bool:
    """Validate and ensure mode has required config."""
    if mode == "online":
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "Online mode requires ANTHROPIC_API_KEY env var. "
                "Set it with: export ANTHROPIC_API_KEY=sk-..."
            )
        return True
    return True  # Offline always available
```

### Sidebar Mode Toggle

```python
def display_mode_selector():
    """Display mode selector in sidebar."""
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("📊 Offline", use_container_width=True):
            st.session_state.selected_mode = "offline"
            st.rerun()

    with col2:
        if st.button("🌐 Online", use_container_width=True):
            try:
                validate_mode("online")
                st.session_state.selected_mode = "online"
                st.rerun()
            except ValueError as e:
                st.error(f"Cannot switch to online: {e}")

    # Display current mode
    mode = st.session_state.get("selected_mode", "offline")
    st.sidebar.info(f"**Current Mode**: {mode.upper()}")
```

### Mode-Specific Behavior

| Component | Offline | Online |
|-----------|---------|--------|
| Fixtures | Load from JSON files | Fetch real data (Claude Vision, market APIs) |
| Scenarios | Pre-loaded 4 scenarios | User can upload PDFs, specify policies |
| Execution time | <1s (pre-computed) | 5-10s (API calls) |
| API keys | None required | ANTHROPIC_API_KEY required |
| Data persistence | Session state only | Can save to database |

---

## 6. Fixture Loading & Caching

### Fixture Loading

```python
@st.cache_resource
def load_all_scenarios():
    """Load all scenario fixtures (cached at app startup)."""
    fixtures_dir = Path(FIXTURES_DIR) / "behavior"
    scenarios = {}

    for fixture_file in fixtures_dir.glob("behavior_va_*.enriched.json"):
        with open(fixture_file) as f:
            scenario_id = fixture_file.stem.replace("behavior_va_", "").replace(".enriched", "")
            scenarios[scenario_id] = json.load(f)

    return scenarios

def get_scenario_fixture(scenario_id: str) -> dict:
    """Get a specific scenario fixture."""
    all_scenarios = load_all_scenarios()
    if scenario_id not in all_scenarios:
        raise ValueError(f"Scenario {scenario_id} not found")
    return all_scenarios[scenario_id]
```

### Caching Strategy

- `@st.cache_resource` for fixture loading (one-time at app startup)
- Session state for workflow results (cleared when scenario changes)
- Memoization for chart generation (Plotly is expensive)

---

## 7. State Reset & Cleanup

### Trigger Conditions

```python
def check_scenario_changed():
    """Reset state if user selects different scenario."""
    if "last_scenario" not in st.session_state:
        st.session_state.last_scenario = st.session_state.selected_scenario
        return False

    if st.session_state.selected_scenario != st.session_state.last_scenario:
        # Scenario changed, reset results
        st.session_state.underwriting_result = None
        st.session_state.reserve_result = None
        st.session_state.behavior_result = None
        st.session_state.hedging_result = None
        st.session_state.workflow_status = "idle"
        st.session_state.execution_errors = []

        st.session_state.last_scenario = st.session_state.selected_scenario
        return True

    return False
```

---

## 8. Session State Diagram

```
User loads page
    │
    ├─→ initialize_session_state()
    │
    └─→ st.session_state ready
        │
        ├─→ Sidebar rendered
        │   ├─ Scenario selector
        │   ├─ Mode toggle (Offline/Online)
        │   └─ Run button
        │
        ├─→ Dashboard page loads
        │   └─ check_scenario_changed()
        │       └─ Reset state if scenario changed
        │
        └─→ User clicks "Run"
            │
            ├─→ run_workflow(scenario_id, mode)
            │   │
            │   ├─→ Load fixture
            │   │
            │   ├─→ Run Underwriting
            │   │   └─ Store result in st.session_state
            │   │
            │   ├─→ Check approval → Gate
            │   │   │
            │   │   ├─ DECLINE → Skip downstream
            │   │   └─ APPROVE → Continue
            │   │
            │   ├─→ (Reserve || Behavior) parallel
            │   │   ├─→ Run Reserve → Store result
            │   │   └─→ Run Behavior → Store result
            │   │
            │   ├─→ Run Hedging (if Reserve success)
            │   │   └─→ Store result
            │   │
            │   └─→ Set workflow_status = "completed"
            │
            └─→ Dashboard rerenders
                └─ Display all results from st.session_state
```

---

## 9. Critical Assumptions

1. **Enriched fixtures exist** as `behavior_va_*.enriched.json` with pre-computed paths
2. **Crew functions are deterministic** when given same seed (reproducible results)
3. **Session state persists** across page navigation (Streamlit default behavior)
4. **Error messages are < 200 chars** (fit in warning banners)
5. **No crews modify fixture data** (all read-only)

---

## 10. Testing Strategy

**Unit tests** for state_manager functions:
```python
def test_workflow_gates_on_underwriting_decline():
    """Verify downstream crews skip if underwriting declines."""
    # Mock underwriting result with decision="DECLINE"
    # Run workflow
    # Assert reserve_status == "skipped"

def test_reserve_failure_skips_hedging():
    """Verify graceful degradation when reserve fails."""
    # Mock reserve crew to raise error
    # Run workflow
    # Assert hedging_status == "skipped"
    # Assert error recorded in execution_errors
```

**Integration tests** using `streamlit.testing.v1.AppTest`:
```python
def test_full_workflow_completes():
    """End-to-end test: scenario selection → run → dashboard."""
    at = AppTest.from_file("app.py").run()
    at.sidebar.selectbox[0].select("base_case")
    at.button("Run Workflow").click()
    # Wait for completion
    assert at.session_state.workflow_status == "completed"
```

---

## Summary

| Component | Design | Rationale |
|-----------|--------|-----------|
| **Execution** | Hybrid Sequential (UW → RB+BH → Hedging) | Realistic, fast, gates clear |
| **State** | Session state dict with crew results + status | Simple, works with Streamlit |
| **Errors** | Graceful degradation + yellow warnings | Transparent, doesn't crash demo |
| **Config** | Env vars + defaults (no .env file needed) | Zero friction for Guardian |
| **Caching** | `@st.cache_resource` for fixtures | Fast page loads |
| **Reset** | Trigger on scenario change | Clean state between tests |

This design enables Phase 1 implementation of 10 core files (~1,800 lines) with clear state flow and error handling.
