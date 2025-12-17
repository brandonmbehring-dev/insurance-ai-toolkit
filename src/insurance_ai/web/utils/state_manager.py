"""
Streamlit session state management and crew orchestration.

Implements hybrid sequential execution:
1. Underwriting (always first) → gates downstream
2. Reserve + Behavior (sequential if UW approves)
3. Hedging (optional, if Reserve succeeds)

Now uses REAL LangGraph crews instead of mock implementations (v0.2.0).
Handles errors gracefully with warnings instead of crashes.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import streamlit as st
except ImportError:
    # Allow module to be imported outside Streamlit context
    st = None

# Real crew imports (v0.2.0)
from insurance_ai.crews.underwriting import (
    UnderwritingState,
    run_underwriting_crew as real_underwriting_crew,
    ProductType as UWProductType,
    RiskClass,
)
from insurance_ai.crews.reserve import (
    ReserveState,
    run_reserve_crew as real_reserve_crew,
    ProductType as RSProductType,
)
from insurance_ai.crews.behavior import (
    BehaviorState,
    run_behavior_crew as real_behavior_crew,
)
from insurance_ai.crews.hedging import (
    HedgingState,
    run_hedging_crew as real_hedging_crew,
)

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

def _cache_decorator(func):
    """Apply Streamlit cache decorator only when in Streamlit context."""
    if st is not None:
        return st.cache_resource(show_spinner=False)(func)
    return func


@_cache_decorator
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


# ===== FIXTURE-TO-STATE CONVERSION FUNCTIONS =====

def fixture_to_underwriting_state(fixture: dict) -> UnderwritingState:
    """
    Convert fixture dict to UnderwritingState for real crew execution.

    Args:
        fixture: Fixture data from scenario JSON

    Returns:
        UnderwritingState ready for crew execution
    """
    return UnderwritingState(
        applicant_id=fixture.get("policy_id", "unknown"),
        product_type=UWProductType.VA_GLWB,
        age=fixture.get("issue_age", 55),
        gender=fixture.get("gender", "M"),
    )


def fixture_to_reserve_state(fixture: dict) -> ReserveState:
    """
    Convert fixture dict to ReserveState for real crew execution.

    Args:
        fixture: Fixture data from scenario JSON

    Returns:
        ReserveState ready for crew execution
    """
    return ReserveState(
        policy_id=fixture.get("policy_id", "unknown"),
        product_type=RSProductType.VA_GLWB,
        issue_age=fixture.get("issue_age", 55),
        policy_month=fixture.get("policy_month", 0),
        account_value=fixture.get("account_value", 100000),
        benefit_base=fixture.get("benefit_base", 100000),
        valuation_date=fixture.get("valuation_date", "2025-01-01"),
        num_scenarios=100,  # Keep low for demo speed
    )


def fixture_to_behavior_state(fixture: dict) -> BehaviorState:
    """
    Convert fixture dict to BehaviorState for real crew execution.

    Args:
        fixture: Fixture data from scenario JSON

    Returns:
        BehaviorState ready for crew execution
    """
    return BehaviorState(
        policy_id=fixture.get("policy_id", "unknown"),
        portfolio_name=fixture.get("portfolio_name", "Demo Portfolio"),
        valuation_date=fixture.get("valuation_date", "2025-01-01"),
        account_value=fixture.get("account_value", 100000),
        benefit_base=fixture.get("benefit_base", 100000),
        annual_withdrawal_amount=fixture.get("annual_withdrawal_amount", 5000),
        time_to_maturity_years=fixture.get("time_to_maturity_years", 15),
        risk_free_rate=fixture.get("risk_free_rate", 0.03),
        market_volatility=fixture.get("market_volatility", 0.18),
        base_lapse_rate=fixture.get("base_lapse_rate", 0.06),
        num_scenarios=100,  # Keep low for demo speed
    )


def fixture_to_hedging_state(fixture: dict) -> HedgingState:
    """
    Convert fixture dict to HedgingState for real crew execution.

    Args:
        fixture: Fixture data from scenario JSON

    Returns:
        HedgingState ready for crew execution
    """
    return HedgingState(
        policy_id=fixture.get("policy_id", "unknown"),
        portfolio_name=fixture.get("portfolio_name", "Demo Portfolio"),
        valuation_date=fixture.get("valuation_date", "2025-01-01"),
        underlying_spot_price=fixture.get("underlying_spot_price", 100.0),
        liability_value=fixture.get("account_value", 100000),  # Use AV as liability proxy
        time_to_maturity_years=fixture.get("time_to_maturity_years", 15),
        implied_volatility_atm=fixture.get("market_volatility", 0.18),
    )


# ===== CREW EXECUTION (REAL IMPLEMENTATIONS v0.2.0) =====

def run_underwriting_crew(fixture: dict, mode: str = "offline") -> dict:
    """
    Run Underwriting Crew (REAL implementation v0.2.0).

    Executes the actual LangGraph crew for mortality risk classification.

    Args:
        fixture: Fixture data from scenario
        mode: "offline" or "online"

    Returns:
        Result dictionary with underwriting decision

    Raises:
        Exception if crew fails
    """
    if mode == "offline":
        # Convert fixture to state
        state = fixture_to_underwriting_state(fixture)
        logger.info(f"Running real Underwriting crew for {state.applicant_id}")

        # Run real crew
        result_state = real_underwriting_crew(state)

        # Convert result to UI dict format
        return {
            "policy_id": result_state.applicant_id,
            "approval_decision": result_state.risk_class.value,
            "confidence_score": result_state.confidence_score,
            "risk_class": result_state.vbt_mortality_class or "Standard",
            "underwriting_notes": result_state.underwriting_notes,
            "extraction_confidence": result_state.extraction_confidence,
            "mortality_adjustment_percent": result_state.mortality_adjustment_percent,
            "processing_method": result_state.processing_method,
        }

    # Online mode would call Claude Vision + extraction logic
    raise NotImplementedError("Online mode not yet implemented")


def run_reserve_crew(
    underwriting_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Reserve Crew (REAL implementation v0.2.0).

    Executes the actual LangGraph crew for VM-21/CTE70 reserve calculation.

    Args:
        underwriting_result: Output from Underwriting
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        Result dictionary with reserve calculations
    """
    if mode == "offline" and fixture:
        # Convert fixture to state
        state = fixture_to_reserve_state(fixture)
        logger.info(f"Running real Reserve crew for {state.policy_id}")

        # Run real crew
        result_state = real_reserve_crew(state)

        # Return full result dictionary from state
        result = result_state.to_dict()
        # Add backward-compatible keys for UI
        result["avg_reserve"] = result_state.mean_reserve
        return result

    raise NotImplementedError("Online mode not yet implemented")


def run_behavior_crew(
    underwriting_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Behavior Crew (REAL implementation v0.2.0).

    Executes the actual LangGraph crew for dynamic lapse/withdrawal modeling.

    Args:
        underwriting_result: Output from Underwriting
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        Result dictionary with behavior modeling
    """
    if mode == "offline" and fixture:
        # Convert fixture to state
        state = fixture_to_behavior_state(fixture)
        logger.info(f"Running real Behavior crew for {state.policy_id}")

        # Run real crew
        result_state = real_behavior_crew(state)

        # Return full result dictionary from state
        result = result_state.to_dict()
        # Add backward-compatible keys for UI
        result["probability_in_force"] = result_state.probability_in_force_at_maturity
        result["reserve_impact"] = result_state.reserve_impact_from_behavior
        return result

    raise NotImplementedError("Online mode not yet implemented")


def run_hedging_crew(
    reserve_result: dict,
    mode: str = "offline",
    fixture: Optional[dict] = None,
) -> dict:
    """
    Run Hedging Crew (REAL implementation v0.2.0).

    Executes the actual LangGraph crew for Greeks and hedge recommendations.

    Args:
        reserve_result: Output from Reserve
        mode: "offline" or "online"
        fixture: Full fixture data (for offline mode)

    Returns:
        Result dictionary with hedging analysis
    """
    if mode == "offline" and fixture:
        # Convert fixture to state
        state = fixture_to_hedging_state(fixture)
        logger.info(f"Running real Hedging crew for {state.policy_id}")

        # Run real crew
        result_state = real_hedging_crew(state)

        # Return full result dictionary from state
        result = result_state.to_dict()
        # Add backward-compatible keys for UI
        result["portfolio_value"] = result_state.liability_value
        result["delta"] = result_state.portfolio_delta
        result["gamma"] = result_state.liability_greeks.gamma
        result["vega"] = result_state.portfolio_vega
        result["hedge_recommendation"] = result_state.recommended_action.value
        result["hedge_cost"] = result_state.hedge_cost_bps * result_state.liability_value / 10000
        return result

    # Fallback for offline mode without fixture (shouldn't happen)
    if mode == "offline":
        return {
            "portfolio_value": reserve_result.get("account_value", 0),
            "delta": -0.65,
            "gamma": 0.002,
            "vega": 0.15,
            "hedge_recommendation": "hold",
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
            uw_result.get("approval_decision", "").startswith("APPROVED")
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

    # ===== 3. RUN RESERVE + BEHAVIOR (SEQUENTIAL) =====
    # Note: Originally parallel with ThreadPoolExecutor, but Streamlit Cloud
    # doesn't support st.session_state access from background threads.
    # Sequential execution is simpler and works reliably on all platforms.

    # Run Reserve Crew
    try:
        reserve_result = run_reserve_crew(
            st.session_state.underwriting_result, mode, fixture
        )
        st.session_state.reserve_result = reserve_result
        st.session_state.reserve_status = "success"
        logger.info("Reserve crew completed successfully")
    except Exception as e:
        logger.error(f"Reserve crew failed: {e}")
        st.session_state.reserve_status = "failed"
        st.session_state.execution_errors.append({
            "crew": "reserve",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })

    # Run Behavior Crew
    try:
        behavior_result = run_behavior_crew(
            st.session_state.underwriting_result, mode, fixture
        )
        st.session_state.behavior_result = behavior_result
        st.session_state.behavior_status = "success"
        logger.info("Behavior crew completed successfully")
    except Exception as e:
        logger.error(f"Behavior crew failed: {e}")
        st.session_state.behavior_status = "failed"
        st.session_state.execution_errors.append({
            "crew": "behavior",
            "error": str(e),
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
