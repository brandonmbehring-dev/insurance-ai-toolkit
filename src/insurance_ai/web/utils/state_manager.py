"""
Streamlit session state management and crew orchestration.

Implements hybrid sequential execution:
1. Underwriting (always first) → gates downstream
2. Reserve + Behavior (parallel if UW approves)
3. Hedging (optional, if Reserve succeeds)

Handles errors gracefully with warnings instead of crashes.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import streamlit as st
except ImportError:
    # Allow module to be imported outside Streamlit context
    st = None

logger = logging.getLogger(__name__)


# ===== SESSION STATE INITIALIZATION =====

def initialize_session_state() -> None:
    """
    Initialize empty session state on app startup.

    This function is idempotent - safe to call multiple times.
    """
    if st is None:
        return

    # State tracking
    if "workflow_status" not in st.session_state:
        st.session_state.workflow_status = "idle"  # idle, running, completed, error
    if "selected_scenario" not in st.session_state:
        st.session_state.selected_scenario = "001_itm"
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = "offline"
    if "execution_timestamp" not in st.session_state:
        st.session_state.execution_timestamp = None

    # Crew results (None = not yet executed)
    if "underwriting_result" not in st.session_state:
        st.session_state.underwriting_result = None
    if "reserve_result" not in st.session_state:
        st.session_state.reserve_result = None
    if "behavior_result" not in st.session_state:
        st.session_state.behavior_result = None
    if "hedging_result" not in st.session_state:
        st.session_state.hedging_result = None

    # Crew execution status (success, failed, skipped, None)
    if "underwriting_status" not in st.session_state:
        st.session_state.underwriting_status = None
    if "reserve_status" not in st.session_state:
        st.session_state.reserve_status = None
    if "behavior_status" not in st.session_state:
        st.session_state.behavior_status = None
    if "hedging_status" not in st.session_state:
        st.session_state.hedging_status = None

    # Approval decision
    if "underwriting_approval" not in st.session_state:
        st.session_state.underwriting_approval = None

    # Error tracking
    if "execution_errors" not in st.session_state:
        st.session_state.execution_errors = []

    # Fixture data
    if "current_fixture" not in st.session_state:
        st.session_state.current_fixture = None

    # Track last scenario for reset detection
    if "last_scenario" not in st.session_state:
        st.session_state.last_scenario = None


# ===== SCENARIO CHANGE DETECTION =====

def check_scenario_changed() -> bool:
    """
    Detect if user changed scenario and reset state if so.

    Returns:
        True if scenario changed (state was reset), False otherwise
    """
    if st is None:
        return False

    current_scenario = st.session_state.selected_scenario
    last_scenario = st.session_state.get("last_scenario")

    if last_scenario is None:
        # First time setting it
        st.session_state.last_scenario = current_scenario
        return False

    if current_scenario != last_scenario:
        # Scenario changed, reset results
        logger.info(f"Scenario changed from {last_scenario} to {current_scenario}, resetting state")

        st.session_state.underwriting_result = None
        st.session_state.reserve_result = None
        st.session_state.behavior_result = None
        st.session_state.hedging_result = None

        st.session_state.underwriting_status = None
        st.session_state.reserve_status = None
        st.session_state.behavior_status = None
        st.session_state.hedging_status = None

        st.session_state.underwriting_approval = None
        st.session_state.workflow_status = "idle"
        st.session_state.execution_errors = []
        st.session_state.last_scenario = current_scenario

        return True

    return False


# ===== FIXTURE LOADING =====

@st.cache_resource(show_spinner=False)
def load_all_fixtures() -> dict:
    """
    Load all enriched behavior fixtures (cached).

    Returns:
        Dictionary mapping scenario_id → fixture_data
    """
    from ..config import get_behavior_fixtures_dir

    fixtures = {}
    behavior_dir = get_behavior_fixtures_dir()

    for fixture_file in sorted(behavior_dir.glob("behavior_va_*.enriched.json")):
        scenario_id = fixture_file.stem.replace("behavior_va_", "").replace(".enriched", "")
        try:
            with open(fixture_file) as f:
                fixtures[scenario_id] = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load fixture {fixture_file}: {e}")

    return fixtures


def load_scenario_fixture(scenario_id: str) -> dict:
    """
    Load a specific scenario fixture.

    Args:
        scenario_id: Scenario identifier (e.g., "001_itm")

    Returns:
        Fixture dictionary

    Raises:
        ValueError if scenario not found
    """
    all_fixtures = load_all_fixtures()

    if scenario_id not in all_fixtures:
        raise ValueError(
            f"Scenario '{scenario_id}' not found. "
            f"Available: {list(all_fixtures.keys())}"
        )

    return all_fixtures[scenario_id]


# ===== CREW EXECUTION (MOCK IMPLEMENTATIONS) =====

def run_underwriting_crew(fixture: dict, mode: str = "offline") -> dict:
    """
    Run Underwriting Crew (mock for now).

    In full implementation, this would call the actual LangGraph crew.

    Args:
        fixture: Fixture data from scenario
        mode: "offline" or "online"

    Returns:
        UnderwritingState result dictionary

    Raises:
        Exception if crew fails
    """
    # For offline mode, return approval from fixture
    if mode == "offline":
        return {
            "policy_id": fixture.get("policy_id", "unknown"),
            "approval_decision": "APPROVE",  # Simplified for demo
            "confidence_score": 0.95,
            "risk_class": "Standard",
        }

    # Online mode would call Claude Vision + extraction logic
    raise NotImplementedError("Online mode not yet implemented")


def run_reserve_crew(
    underwriting_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Reserve Crew (mock for now).

    Args:
        underwriting_result: Output from Underwriting
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        ReserveState result dictionary
    """
    if mode == "offline" and fixture:
        # Return reserve metrics from fixture
        return {
            "policy_id": fixture.get("policy_id", "unknown"),
            "account_value": fixture.get("account_value", 0),
            "benefit_base": fixture.get("benefit_base", 0),
            "cte70_reserve": fixture.get("account_value", 0) * 0.1,  # Simplified
            "avg_reserve": fixture.get("account_value", 0) * 0.08,
            "num_scenarios": fixture.get("num_scenarios", 100),
        }

    raise NotImplementedError("Online mode not yet implemented")


def run_behavior_crew(
    underwriting_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Behavior Crew (mock for now).

    Args:
        underwriting_result: Output from Underwriting
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        BehaviorState result dictionary
    """
    if mode == "offline" and fixture:
        return {
            "policy_id": fixture.get("policy_id", "unknown"),
            "moneyness": fixture.get("moneyness", 1.0),
            "dynamic_lapse_rate": fixture.get("dynamic_lapse_rate", 0.06),
            "probability_in_force": fixture.get("probability_in_force_at_maturity", 0.90),
            "reserve_impact": fixture.get("reserve_impact_from_behavior", 0),
        }

    raise NotImplementedError("Online mode not yet implemented")


def run_hedging_crew(
    reserve_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Hedging Crew (mock for now).

    Args:
        reserve_result: Output from Reserve
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        HedgingState result dictionary
    """
    if mode == "offline":
        return {
            "portfolio_value": reserve_result.get("account_value", 0),
            "delta": -0.65,
            "gamma": 0.002,
            "vega": 0.15,
            "hedge_recommendation": "Buy put spreads",
            "hedge_cost": reserve_result.get("account_value", 0) * 0.005,
        }

    raise NotImplementedError("Online mode not yet implemented")


# ===== MAIN ORCHESTRATION FUNCTION =====

def run_workflow(scenario_id: str, mode: str = "offline") -> None:
    """
    Execute the full workflow: UW → (Reserve + Behavior parallel) → Hedging.

    Decision 1 (Hybrid Sequential):
    - Underwriting always first (gates downstream)
    - Reserve + Behavior run in parallel (no dependency)
    - Hedging runs last (if Reserve succeeds)

    Decision 4 (Graceful Degradation):
    - Captures errors with crew name + timestamp
    - Continues with other crews if one fails
    - Skips dependent crews if critical crew fails

    Updates st.session_state with all results and status.

    Args:
        scenario_id: Scenario identifier (e.g., "001_itm")
        mode: "offline" or "online" (default: "offline")
    """
    if st is None:
        logger.error("Streamlit context not available")
        return

    # Load fixture
    try:
        fixture = load_scenario_fixture(scenario_id)
        st.session_state.current_fixture = fixture
    except Exception as e:
        logger.error(f"Failed to load fixture: {e}")
        st.session_state.workflow_status = "error"
        st.session_state.execution_errors.append({
            "crew": "fixture_loader",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        return

    # Set status to running
    st.session_state.workflow_status = "running"
    st.session_state.execution_errors = []

    # ===== 1. RUN UNDERWRITING =====

    try:
        uw_result = run_underwriting_crew(fixture, mode)
        st.session_state.underwriting_result = uw_result
        st.session_state.underwriting_status = "success"
        st.session_state.underwriting_approval = (
            uw_result.get("approval_decision") == "APPROVE"
        )
        logger.info(f"Underwriting: {st.session_state.underwriting_approval}")

    except Exception as e:
        logger.error(f"Underwriting crew failed: {e}")
        st.session_state.underwriting_status = "failed"
        st.session_state.underwriting_approval = False
        st.session_state.execution_errors.append({
            "crew": "underwriting",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        st.session_state.workflow_status = "error"
        # Early exit - underwriting gates everything
        st.session_state.reserve_status = "skipped"
        st.session_state.behavior_status = "skipped"
        st.session_state.hedging_status = "skipped"
        return

    # ===== 2. CHECK APPROVAL GATE =====

    if not st.session_state.underwriting_approval:
        logger.info("Underwriting declined - skipping downstream crews")
        st.session_state.reserve_status = "skipped"
        st.session_state.behavior_status = "skipped"
        st.session_state.hedging_status = "skipped"
        st.session_state.workflow_status = "completed"
        return

    # ===== 3. RUN RESERVE + BEHAVIOR PARALLEL =====

    def run_reserve_wrapper() -> tuple[str, dict, str]:
        """Run Reserve and return (crew_name, result, status)."""
        try:
            result = run_reserve_crew(st.session_state.underwriting_result, mode, fixture)
            return ("reserve", result, "success")
        except Exception as e:
            logger.error(f"Reserve crew failed: {e}")
            return ("reserve", None, f"failed: {str(e)}")

    def run_behavior_wrapper() -> tuple[str, dict, str]:
        """Run Behavior and return (crew_name, result, status)."""
        try:
            result = run_behavior_crew(st.session_state.underwriting_result, mode, fixture)
            return ("behavior", result, "success")
        except Exception as e:
            logger.error(f"Behavior crew failed: {e}")
            return ("behavior", None, f"failed: {str(e)}")

    # Execute in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        reserve_future = executor.submit(run_reserve_wrapper)
        behavior_future = executor.submit(run_behavior_wrapper)

        # Collect results
        for future in as_completed([reserve_future, behavior_future]):
            crew_name, result, status = future.result()

            if crew_name == "reserve":
                if status == "success":
                    st.session_state.reserve_result = result
                    st.session_state.reserve_status = "success"
                else:
                    st.session_state.reserve_status = "failed"
                    st.session_state.execution_errors.append({
                        "crew": "reserve",
                        "error": status.replace("failed: ", ""),
                        "timestamp": datetime.now().isoformat(),
                    })
            elif crew_name == "behavior":
                if status == "success":
                    st.session_state.behavior_result = result
                    st.session_state.behavior_status = "success"
                else:
                    st.session_state.behavior_status = "failed"
                    st.session_state.execution_errors.append({
                        "crew": "behavior",
                        "error": status.replace("failed: ", ""),
                        "timestamp": datetime.now().isoformat(),
                    })

    # ===== 4. RUN HEDGING (if Reserve succeeded) =====

    if st.session_state.reserve_status == "success":
        try:
            hedge_result = run_hedging_crew(st.session_state.reserve_result, mode, fixture)
            st.session_state.hedging_result = hedge_result
            st.session_state.hedging_status = "success"
        except Exception as e:
            logger.error(f"Hedging crew failed: {e}")
            st.session_state.hedging_status = "failed"
            st.session_state.execution_errors.append({
                "crew": "hedging",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
    else:
        # Reserve failed, skip hedging
        st.session_state.hedging_status = "skipped"

    # ===== 5. FINALIZE =====

    st.session_state.workflow_status = "completed"
    st.session_state.execution_timestamp = datetime.now()
    logger.info(f"Workflow completed: {st.session_state.workflow_status}")


# ===== WORKFLOW STATUS HELPERS =====

def get_workflow_status() -> str:
    """Get current workflow status."""
    if st is None:
        return "unknown"
    return st.session_state.get("workflow_status", "idle")


def is_workflow_running() -> bool:
    """Check if workflow is currently running."""
    return get_workflow_status() == "running"


def is_workflow_completed() -> bool:
    """Check if workflow has completed."""
    return get_workflow_status() == "completed"


def has_errors() -> bool:
    """Check if workflow encountered any errors."""
    if st is None:
        return False
    return len(st.session_state.get("execution_errors", [])) > 0


def get_crew_status(crew_name: str) -> Optional[str]:
    """
    Get status of a specific crew.

    Args:
        crew_name: "underwriting", "reserve", "behavior", or "hedging"

    Returns:
        Status: "success", "failed", "skipped", or None
    """
    if st is None:
        return None

    status_key = f"{crew_name}_status"
    return st.session_state.get(status_key)


def get_crew_result(crew_name: str) -> Optional[dict]:
    """
    Get result of a specific crew.

    Args:
        crew_name: "underwriting", "reserve", "behavior", or "hedging"

    Returns:
        Result dictionary or None
    """
    if st is None:
        return None

    result_key = f"{crew_name}_result"
    return st.session_state.get(result_key)
