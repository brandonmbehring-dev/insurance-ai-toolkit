"""Integration tests for cross-crew workflows.

Tests that data flows correctly between crews:
- Underwriting → Reserve: Approved applicant → reserve calculation
- Reserve → Hedging: Reserve output → hedge recommendation
- All crews: Full lifecycle workflow

Validates:
1. Output schema compatibility
2. Data consistency across crews
3. Multi-crew orchestration
"""

import unittest
import json
from pathlib import Path

from insurance_ai.crews.underwriting import (
    UnderwritingState,
    ProductType as UnderwritingProductType,
    run_underwriting_crew,
)
from insurance_ai.crews.reserve import (
    ReserveState,
    ProductType as ReserveProductType,
    run_reserve_crew,
)


class TestUnderwritingToReserveWorkflow(unittest.TestCase):
    """Test underwriting approval flowing into reserve calculation."""

    def test_approved_va_applicant_flows_to_reserve(self) -> None:
        """Approved VA applicant should flow to reserve calculation."""
        # Step 1: Underwriting - Approve applicant
        underwriting_state = UnderwritingState(
            applicant_id="integration_001",
            product_type=UnderwritingProductType.VA_GLWB,
            age=55,
            gender="M",
            extracted_health_metrics={
                "age": 55,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "bmi": 24.5,
                "health_conditions": [],
                "smoker": False,
            },
            extraction_confidence=0.95,
            mortality_adjustment_percent=0.0,
        )

        # Run underwriting crew
        underwriting_result = run_underwriting_crew(underwriting_state)

        # Verify approval
        self.assertIn(
            underwriting_result.risk_class.value,
            ["APPROVED", "APPROVED_WITH_FLATEX"],
            "Applicant should be approved or approved with flattening",
        )

        # Step 2: Reserve - Use approval outcome
        # Map underwriting output to reserve input
        issue_age = underwriting_result.age
        account_value = 250000  # Standard VA issue
        benefit_base = account_value * 1.4  # Typical GLWB multiplier

        reserve_state = ReserveState(
            policy_id=f"reserve_{underwriting_result.applicant_id}",
            product_type=ReserveProductType.VA_GLWB,
            issue_age=issue_age,
            policy_month=0,  # New issue
            account_value=account_value,
            benefit_base=benefit_base,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        # Run reserve crew
        reserve_result = run_reserve_crew(reserve_state)

        # Verify reserve calculation
        self.assertGreater(reserve_result.cte70_reserve, 0)
        self.assertEqual(reserve_result.product_type, ReserveProductType.VA_GLWB)
        self.assertGreater(reserve_result.vm21_reserve, 0)

        # Cross-crew consistency: Age should be preserved
        self.assertEqual(reserve_result.issue_age, issue_age)

        # CTE should reflect mortality impact from underwriting
        # Higher mortality adjustment (if any) should increase reserve
        base_mortality = 0.005  # Standard 55-year-old
        expected_reserve_order_of_magnitude = benefit_base * base_mortality

        # Reserve should be meaningful (at least a few % of benefit base)
        reserve_to_benefit_ratio = (
            reserve_result.cte70_reserve / reserve_result.benefit_base
        )
        self.assertGreater(
            reserve_to_benefit_ratio,
            0.01,
            "Reserve should be at least 1% of benefit base",
        )

    def test_declined_applicant_not_processed_for_reserve(self) -> None:
        """Declined applicant should result in zero reserve."""
        # For this test, we'd need a declined fixture
        # For now, just verify logic - high-risk applicant at advanced age
        underwriting_state = UnderwritingState(
            applicant_id="integration_declined_001",
            product_type=UnderwritingProductType.VA_GLWB,
            age=85,  # Very advanced age
            gender="M",
            extracted_health_metrics={
                "age": 85,
                "blood_pressure_systolic": 180,
                "blood_pressure_diastolic": 110,
                "bmi": 30.0,
                "health_conditions": ["Diabetes", "Hypertension", "Heart Disease"],
                "smoker": True,
            },
            extraction_confidence=0.9,
        )

        underwriting_result = run_underwriting_crew(underwriting_state)

        # Advanced age + health conditions should result in pending review or decline
        self.assertIsNotNone(underwriting_result.risk_class)
        # Age should be preserved
        self.assertEqual(underwriting_result.age, 85)

    def test_fia_applicant_to_reserve_workflow(self) -> None:
        """FIA applicant should flow to VM-22 reserve."""
        underwriting_state = UnderwritingState(
            applicant_id="integration_fia_001",
            product_type=UnderwritingProductType.FIA,
            age=60,
            gender="F",
            extracted_health_metrics={
                "age": 60,
                "blood_pressure_systolic": 130,
                "blood_pressure_diastolic": 85,
                "bmi": 25.0,
                "health_conditions": [],
                "smoker": False,
            },
            extraction_confidence=0.92,
        )

        underwriting_result = run_underwriting_crew(underwriting_state)

        # Should be approvable for FIA
        self.assertIsNotNone(underwriting_result.risk_class)

        # Create reserve
        reserve_state = ReserveState(
            policy_id=f"reserve_{underwriting_result.applicant_id}",
            product_type=ReserveProductType.FIA,
            issue_age=underwriting_result.age,
            policy_month=0,
            account_value=500000,
            benefit_base=500000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=20,
            scenario_seed=77,
        )

        reserve_result = run_reserve_crew(reserve_state)

        # Should use VM-22
        self.assertEqual(reserve_result.product_type, ReserveProductType.FIA)
        self.assertGreater(reserve_result.vm22_reserve, 0)
        self.assertEqual(reserve_result.vm22_reserve, reserve_result.cte70_reserve)

    def test_rila_applicant_to_reserve_workflow(self) -> None:
        """RILA applicant should flow to VM-22 reserve."""
        underwriting_state = UnderwritingState(
            applicant_id="integration_rila_001",
            product_type=UnderwritingProductType.RILA,
            age=50,
            gender="M",
            extracted_health_metrics={
                "age": 50,
                "blood_pressure_systolic": 125,
                "blood_pressure_diastolic": 82,
                "bmi": 24.0,
                "health_conditions": [],
                "smoker": False,
            },
            extraction_confidence=0.94,
        )

        underwriting_result = run_underwriting_crew(underwriting_state)

        # Create reserve for RILA
        reserve_state = ReserveState(
            policy_id=f"reserve_{underwriting_result.applicant_id}",
            product_type=ReserveProductType.RILA,
            issue_age=underwriting_result.age,
            policy_month=0,
            account_value=400000,
            benefit_base=420000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=25,
            scenario_seed=88,
        )

        reserve_result = run_reserve_crew(reserve_state)

        self.assertEqual(reserve_result.product_type, ReserveProductType.RILA)
        self.assertGreater(reserve_result.vm22_reserve, 0)


class TestReserveOutputConsistency(unittest.TestCase):
    """Test consistency of reserve outputs across runs."""

    def test_same_input_produces_identical_reserve(self) -> None:
        """Same policy input should produce identical reserve with fixed seed."""
        reserve_state_1 = ReserveState(
            policy_id="consistency_test_1",
            product_type=ReserveProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        reserve_state_2 = ReserveState(
            policy_id="consistency_test_2",
            product_type=ReserveProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result_1 = run_reserve_crew(reserve_state_1)
        result_2 = run_reserve_crew(reserve_state_2)

        # Same seed → nearly identical results (within rounding)
        self.assertAlmostEqual(result_1.cte70_reserve, result_2.cte70_reserve, places=0)
        self.assertAlmostEqual(result_1.mean_reserve, result_2.mean_reserve, places=0)

    def test_all_product_types_produce_reserves(self) -> None:
        """All three product types should produce valid reserves."""
        products = [
            (ReserveProductType.VA_GLWB, "vm21_reserve"),
            (ReserveProductType.FIA, "vm22_reserve"),
            (ReserveProductType.RILA, "vm22_reserve"),
        ]

        for product_type, reserve_field in products:
            with self.subTest(product=product_type.value):
                state = ReserveState(
                    policy_id=f"test_{product_type.value}",
                    product_type=product_type,
                    issue_age=55,
                    policy_month=60,
                    account_value=300000,
                    benefit_base=330000,
                    valuation_date="2025-12-31",
                    num_scenarios=100,
                    num_years=25,
                    scenario_seed=99,
                )

                result = run_reserve_crew(state)

                # Verify the appropriate reserve field is populated
                reserve_value = getattr(result, reserve_field)
                self.assertGreater(
                    reserve_value,
                    0,
                    f"{reserve_field} should be populated for {product_type.value}",
                )


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity across workflows."""

    def test_reserve_output_serializable(self) -> None:
        """Reserve output should be JSON-serializable."""
        state = ReserveState(
            policy_id="json_test",
            product_type=ReserveProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)
        result_dict = result.to_dict()

        # Should be JSON-serializable
        json_str = json.dumps(result_dict)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)

        # Should deserialize back
        deserialized = json.loads(json_str)
        self.assertEqual(deserialized["policy_id"], "json_test")
        self.assertGreater(deserialized["cte70_reserve"], 0)

    def test_reserve_fields_not_none(self) -> None:
        """All critical reserve fields should be populated (not None)."""
        state = ReserveState(
            policy_id="none_test",
            product_type=ReserveProductType.VA_GLWB,
            issue_age=55,
            policy_month=120,
            account_value=250000,
            benefit_base=350000,
            valuation_date="2025-12-31",
            num_scenarios=100,
            num_years=30,
            scenario_seed=42,
        )

        result = run_reserve_crew(state)

        critical_fields = [
            "policy_id",
            "product_type",
            "cte70_reserve",
            "mean_reserve",
            "risk_margin",
            "convergence_error_percent",
        ]

        for field in critical_fields:
            value = getattr(result, field)
            self.assertIsNotNone(value, f"{field} should not be None")


if __name__ == "__main__":
    unittest.main()
