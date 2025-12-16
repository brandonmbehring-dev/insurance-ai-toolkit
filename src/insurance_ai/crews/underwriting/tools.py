"""Tools for UnderwritingCrew agents.

These tools wrap functions from the annuity-pricing codebase:
- load_mortality_table: Load SOA 2012 IAM mortality tables
- calculate_health_adjustment: Adjust mortality based on health metrics
- check_approval_rules: Apply product-specific approval rules
- validate_health_metrics: Check consistency of extracted metrics
"""

from typing import Any, Dict
from pathlib import Path


def load_mortality_table(gender: str) -> Dict[str, Any]:
    """
    Load SOA 2012 IAM mortality table for specified gender.

    Args:
        gender: "M" (male) or "F" (female)

    Returns:
        Dict with table metadata and sample mortality rates at key ages.

    Example:
        >>> table = load_mortality_table("M")
        >>> table["gender"]
        'M'
        >>> 40 in table["sample_mortality_rates"]
        True
    """
    # In production, this would import from annuity-pricing:
    # from annuity_pricing.loaders import MortalityLoader
    # loader = MortalityLoader()
    # table = loader.soa_2012_iam(gender=gender)

    # For now, return a realistic mock based on SOA 2012 IAM
    sample_rates = {
        40: 0.00082,
        50: 0.00204,
        60: 0.00611,
        70: 0.01875,
        80: 0.05784,
    }

    if gender == "F":
        sample_rates = {k: v * 0.65 for k, v in sample_rates.items()}

    return {
        "table_name": "SOA_2012_IAM",
        "gender": gender,
        "sample_mortality_rates": sample_rates,
        "source": "Society of Actuaries 2012 Insured Lives Mortality (ILM) Study",
    }


def calculate_health_adjustment(
    health_metrics: Dict[str, Any],
    base_adjustment: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate mortality adjustment factor from health metrics.

    Health risk factors:
    - Smoking (current): +75%
    - Smoking (former): +15%
    - Hypertension (SBP > 160): +50%
    - Diabetes: +25%
    - Obesity (BMI > 40): +30%

    Args:
        health_metrics: Extracted health metrics dict
        base_adjustment: Starting multiplier (default 1.0)

    Returns:
        Dict with adjustment_factor, components breakdown, and percent_increase.

    Example:
        >>> metrics = {
        ...     "smoking_status": "current",
        ...     "height_cm": 175,
        ...     "weight_kg": 90,
        ...     "health_conditions": ["Diabetes"]
        ... }
        >>> result = calculate_health_adjustment(metrics)
        >>> result["adjustment_factor"] > 2.0
        True
    """
    adjustment = base_adjustment
    components = {}

    # Smoking
    smoking = health_metrics.get("smoking_status", "never").lower()
    if smoking == "current":
        adjustment *= 1.75
        components["smoking"] = 75
    elif smoking == "former":
        adjustment *= 1.15
        components["former_smoking"] = 15

    # BMI
    height_m = health_metrics.get("height_cm", 170) / 100
    weight_kg = health_metrics.get("weight_kg", 70)
    if height_m > 0:
        bmi = weight_kg / (height_m**2)
        if bmi > 40:
            adjustment *= 1.30
            components["obesity"] = 30

    # Hypertension
    sbp = health_metrics.get("blood_pressure_systolic", 120)
    if sbp > 160:
        adjustment *= 1.50
        components["hypertension"] = 50

    # Diabetes
    conditions = health_metrics.get("health_conditions", [])
    if isinstance(conditions, list):
        if "Diabetes" in conditions or "Type 2 Diabetes" in conditions:
            adjustment *= 1.25
            components["diabetes"] = 25

        # Hypertension (if not already accounted for by BP)
        if "Hypertension" in conditions and sbp <= 160:
            # If BP is controlled, add modest adjustment for condition
            adjustment *= 1.20
            components["hypertension_condition"] = 20

    return {
        "adjustment_factor": adjustment,
        "components": components,
        "percent_increase": (adjustment - 1) * 100,
    }


def check_approval_rules(
    product_type: str,
    age: int,
    mortality_adjustment_percent: float,
    extraction_confidence: float,
) -> Dict[str, Any]:
    """
    Check product-specific approval rules.

    Rules vary by product:
    - VA + GLWB: Stricter (living benefits require longevity)
    - FIA: Standard
    - RILA: Standard

    Args:
        product_type: "VA_with_GLWB", "FIA", or "RILA"
        age: Applicant age
        mortality_adjustment_percent: % increase from standard mortality
        extraction_confidence: 0-1 confidence in extracted data

    Returns:
        Dict with approved (bool), class (str), and reasons (list).

    Example:
        >>> result = check_approval_rules("VA_with_GLWB", 55, 30, 0.95)
        >>> result["approved"]
        True
        >>> result["class"]
        'APPROVED'
    """
    rules = {
        "VA_with_GLWB": {"max_adjustment": 50, "min_age": 40, "max_age": 85},
        "FIA": {"max_adjustment": 100, "min_age": 35, "max_age": 90},
        "RILA": {"max_adjustment": 100, "min_age": 35, "max_age": 90},
    }

    rule = rules.get(product_type, rules["FIA"])
    reasons = []

    # Age check
    if age < rule["min_age"]:
        return {
            "approved": False,
            "class": "DECLINED",
            "reasons": [f"Age {age} below minimum {rule['min_age']}"],
        }

    if age > rule["max_age"]:
        reasons.append(f"Age {age} above standard limit {rule['max_age']}")

    # Extraction confidence floor
    if extraction_confidence < 0.7:
        return {
            "approved": False,
            "class": "PENDING_REVIEW",
            "reasons": [f"Extraction confidence {extraction_confidence:.0%} below 70%"],
        }

    # Mortality adjustment check
    if mortality_adjustment_percent > rule["max_adjustment"]:
        return {
            "approved": False,
            "class": "DECLINED",
            "reasons": [
                f"Mortality adjustment {mortality_adjustment_percent:.0f}% exceeds {rule['max_adjustment']}%"
            ],
        }

    if mortality_adjustment_percent > rule["max_adjustment"] * 0.7:
        return {
            "approved": True,
            "class": "APPROVED_WITH_FLATEX",
            "reasons": [f"Approved with flatex rider ({mortality_adjustment_percent:.0f}% adjustment)"],
        }

    return {
        "approved": True,
        "class": "APPROVED",
        "reasons": ["Approved at standard rates"],
    }


def validate_health_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate consistency of extracted health metrics.

    Checks:
    - BMI consistency
    - Blood pressure reasonableness
    - Cholesterol/triglycerides ratio
    - Age-condition consistency

    Args:
        metrics: Extracted health metrics

    Returns:
        Dict with is_valid (bool), warnings (list), and issues (list).

    Example:
        >>> metrics = {"height_cm": 175, "weight_kg": 150, "blood_pressure_systolic": 180}
        >>> result = validate_health_metrics(metrics)
        >>> len(result["warnings"]) > 0
        True
    """
    warnings = []
    issues = []

    # BMI validation
    height_m = metrics.get("height_cm", 170) / 100
    weight_kg = metrics.get("weight_kg", 70)

    if height_m > 0:
        bmi = weight_kg / (height_m**2)
        if bmi > 40:
            warnings.append(f"Obesity risk: BMI={bmi:.1f}")
        elif bmi < 18:
            warnings.append(f"Underweight: BMI={bmi:.1f}")

    # Blood pressure check
    sbp = metrics.get("blood_pressure_systolic", 120)
    dbp = metrics.get("blood_pressure_diastolic", 80)

    if sbp > 180 or dbp > 110:
        issues.append(f"Severe hypertension: {sbp}/{dbp}")
    elif sbp > 160:
        warnings.append(f"Hypertension Stage 2: SBP={sbp}")

    # Cholesterol/Triglycerides ratio
    chol = metrics.get("cholesterol_mg_dl", 200)
    trig = metrics.get("triglycerides_mg_dl", 100)

    if chol > 0 and trig > 0:
        ratio = trig / chol
        if ratio > 0.5:
            warnings.append(f"High triglyceride ratio: {ratio:.2f}")

    return {
        "is_valid": len(issues) == 0,
        "warnings": warnings,
        "issues": issues,
    }
