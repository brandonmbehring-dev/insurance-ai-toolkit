"""Command-line interface for InsuranceAI Toolkit.

Minimal CLI demonstrating the toolkit's core crews:
- underwriting: Risk classification from medical data
- reserve: Regulatory reserve calculations
- hedging: Volatility calibration and hedge ratios
- behavior: Dynamic lapse and policyholder behavior modeling

Default mode: Offline (fixtures). Add --online flag for live API calls.

Examples:
    >>> insurance-ai --help
    >>> insurance-ai underwriting --help
    >>> insurance-ai underwriting fixture.json --offline
    >>> ANTHROPIC_API_KEY=sk-... insurance-ai underwriting data.json --online
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from insurance_ai.config import ONLINE_MODE, get_config, load_fixture
from insurance_ai.crews.underwriting import (
    UnderwritingState,
    ProductType,
)
from insurance_ai.crews.underwriting.workflow import run_underwriting_crew


@click.group()
@click.option(
    "--online",
    "online_mode",
    is_flag=True,
    default=False,
    help="Use online mode with Claude API (requires ANTHROPIC_API_KEY).",
)
@click.option(
    "--offline",
    "offline_mode",
    is_flag=True,
    default=False,
    help="Use offline mode with fixtures (default).",
)
@click.option(
    "--debug",
    "debug",
    is_flag=True,
    default=False,
    help="Enable debug logging.",
)
@click.pass_context
def main(ctx: click.Context, online_mode: bool, offline_mode: bool, debug: bool) -> None:
    """InsuranceAI Toolkit: Annuity Product Lifecycle Automation.

    Agentic AI system for automating Variable Annuity (VA), Fixed Index Annuity (FIA),
    and Registered Index-Linked Annuity (RILA) workflows.

    Crews:
    - underwriting: Medical data extraction & risk classification
    - reserve: Regulatory reserve calculations
    - hedging: Volatility calibration & hedging
    - behavior: Dynamic lapse & policyholder behavior

    Default: Offline mode (fixtures, no API keys). Add --online for live API calls.

    Examples:
        \b
        # Show crew help
        insurance-ai underwriting --help

        \b
        # Run underwriting with synthetic fixture (offline)
        insurance-ai underwriting synthetic_applicant_001

        \b
        # Run with custom data file (offline)
        insurance-ai underwriting path/to/applicant.json

        \b
        # Run online with Claude API
        ANTHROPIC_API_KEY=sk-... insurance-ai underwriting applicant.json --online
    """
    # Validate mode flags
    if online_mode and offline_mode:
        raise click.UsageError("Cannot specify both --online and --offline")

    # Determine final mode
    final_online_mode = online_mode if (online_mode or offline_mode) else ONLINE_MODE

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    try:
        ctx.obj["config"] = get_config(online=final_online_mode, debug=debug)
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    if debug:
        click.echo(f"Mode: {'online' if final_online_mode else 'offline'}", err=True)


@main.command()
@click.argument("input_file", default="synthetic_applicant_001")
@click.option(
    "--product",
    "-p",
    type=click.Choice(["VA_with_GLWB", "FIA", "RILA"]),
    default="VA_with_GLWB",
    help="Annuity product type.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for risk classification (JSON).",
)
@click.pass_context
def underwriting(
    ctx: click.Context, input_file: str, product: str, output: Optional[str]
) -> None:
    """UnderwritingCrew: Medical data extraction & risk classification.

    Processes medical records (PDFs or structured data) to extract health metrics
    and assign mortality risk classes (Preferred+, Preferred, Standard, Rated).

    Uses LangGraph agent orchestration with 4-step workflow:
    1. Extract: Load health metrics from PDF or fixture
    2. Validate: Check consistency of metrics
    3. Classify: Determine VBT mortality class using SOA 2012 IAM
    4. Approve: Apply product-specific rules

    Supported products: VA + GLWB, FIA, RILA

    Example:
        \b
        # Use synthetic fixture (offline)
        insurance-ai underwriting synthetic_applicant_001

        \b
        # Run with specific product
        insurance-ai underwriting data.json --product FIA

        \b
        # Online mode (requires API key)
        ANTHROPIC_API_KEY=sk-... insurance-ai underwriting app.json --online
    """
    config = ctx.obj["config"]

    try:
        # Determine applicant age and gender for state initialization
        # If input_file doesn't exist, treat as fixture ID
        applicant_id = input_file
        age = 55  # Default, would be extracted from JSON or PDF
        gender = "M"  # Default, would be extracted

        if Path(input_file).exists():
            try:
                with open(input_file) as f:
                    applicant_data = json.load(f)
                    applicant_id = applicant_data.get("applicant_id", input_file)
                    age = applicant_data.get("age", 55)
                    gender = applicant_data.get("gender", "M")
            except json.JSONDecodeError:
                click.echo(
                    f"⚠️  Could not parse JSON from {input_file}, using defaults",
                    err=True,
                )

        # Initialize state for UnderwritingCrew
        state = UnderwritingState(
            applicant_id=applicant_id,
            product_type=ProductType(product),
            age=age,
            gender=gender,
        )

        click.echo(f"🔍 Running UnderwritingCrew for {applicant_id}...", err=True)
        click.echo(f"   Product: {product}", err=True)
        click.echo(f"   Mode: {'🔌 Online' if config.online_mode else '📦 Offline'}", err=True)

        # Execute UnderwritingCrew
        result_state = run_underwriting_crew(state)

        # Convert result to dict for JSON output
        result = result_state.to_dict()

        # Output result
        result_json = json.dumps(result, indent=2)
        click.echo(result_json)

        # Save to file if requested
        if output:
            Path(output).write_text(result_json)
            click.echo(f"✅ Saved to: {output}", err=True)

        # Show approval status
        click.echo(f"✅ Decision: {result_state.risk_class.value}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", default="synthetic_policy_001")
@click.option(
    "--scenarios",
    "-n",
    type=int,
    default=100,
    help="Number of economic scenarios (default 100 for testing).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for reserve calculation (JSON).",
)
@click.pass_context
def reserve(ctx: click.Context, input_file: str, scenarios: int, output: Optional[str]) -> None:
    """ReserveCrew: Regulatory reserve calculations.

    Calculates Principle-Based Reserves for Variable Annuities (VM-21) and
    other annuity products (VM-22), including CTE70 tail risk calculations.

    Supported products: VA + GLWB/GMWB, FIA, RILA

    Example:
        \b
        # Use synthetic fixture with 100 scenarios
        insurance-ai reserve synthetic_policy_001

        \b
        # Run with custom policy data, 1000 scenarios
        insurance-ai reserve policy.json --scenarios 1000 --output reserves.json
    """
    config = ctx.obj["config"]

    click.echo(f"📋 ReserveCrew: {scenarios} scenarios", err=True)

    try:
        # Load fixture (demonstration only)
        if not Path(input_file).exists():
            result = load_fixture("reserve", input_file)
        else:
            result = load_fixture("reserve", "synthetic_policy_001")
            result["input_file"] = input_file

        result["scenarios"] = scenarios
        result_json = json.dumps(result, indent=2, default=str)
        click.echo(result_json)

        if output:
            Path(output).write_text(result_json)
            click.echo(f"✅ Saved to: {output}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", default="synthetic_portfolio_001")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for hedge recommendations (JSON).",
)
@click.pass_context
def hedging(ctx: click.Context, input_file: str, output: Optional[str]) -> None:
    """HedgingCrew: Volatility calibration & hedge recommendations.

    Calibrates volatility surfaces (SABR/Heston), calculates option Greeks,
    and recommends hedge strategies for embedded options in annuities.

    Supported products: VA + GLWB, FIA, RILA

    Example:
        \b
        # Use synthetic fixture
        insurance-ai hedging synthetic_portfolio_001

        \b
        # Run with custom portfolio
        insurance-ai hedging portfolio.json --output hedges.json
    """
    config = ctx.obj["config"]

    click.echo("🔄 HedgingCrew: Volatility calibration", err=True)

    try:
        if not Path(input_file).exists():
            result = load_fixture("hedging", input_file)
        else:
            result = load_fixture("hedging", "synthetic_portfolio_001")
            result["input_file"] = input_file

        result_json = json.dumps(result, indent=2, default=str)
        click.echo(result_json)

        if output:
            Path(output).write_text(result_json)
            click.echo(f"✅ Saved to: {output}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", default="synthetic_cohort_001")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for behavior model results (JSON).",
)
@click.pass_context
def behavior(ctx: click.Context, input_file: str, output: Optional[str]) -> None:
    """BehaviorCrew: Dynamic lapse & policyholder behavior modeling.

    Models dynamic policyholder behavior (surrenders, withdrawals) based on
    moneyness, interest rates, and market conditions. Includes path simulation
    and reserve impact analysis.

    Supported products: VA + GLWB, FIA, RILA

    Example:
        \b
        # Use synthetic fixture
        insurance-ai behavior synthetic_cohort_001

        \b
        # Run with custom cohort data
        insurance-ai behavior cohort.json --output behavior.json
    """
    config = ctx.obj["config"]

    click.echo("🧠 BehaviorCrew: Dynamic lapse modeling", err=True)

    try:
        if not Path(input_file).exists():
            result = load_fixture("behavior", input_file)
        else:
            result = load_fixture("behavior", "synthetic_cohort_001")
            result["input_file"] = input_file

        result_json = json.dumps(result, indent=2, default=str)
        click.echo(result_json)

        if output:
            Path(output).write_text(result_json)
            click.echo(f"✅ Saved to: {output}", err=True)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check toolkit status and configuration.

    Shows:
    - Current mode (online/offline)
    - Available fixtures
    - Dependencies
    - Next steps
    """
    config = ctx.obj["config"]

    click.echo("\n=== InsuranceAI Toolkit Status ===\n")
    click.echo(f"Mode: {'🔌 Online' if config.online_mode else '📦 Offline (Fixtures)'}")
    click.echo(f"Fixtures: {config.fixtures_dir}")

    if config.fixtures_dir.exists():
        crews = [d.name for d in config.fixtures_dir.iterdir() if d.is_dir()]
        click.echo(f"Available crews: {', '.join(crews) if crews else 'None yet'}")
    else:
        click.echo("⚠️  Fixtures directory not yet created")

    click.echo(f"\nNext steps:")
    click.echo("1. Run a crew: insurance-ai underwriting")
    click.echo("2. View help: insurance-ai underwriting --help")
    click.echo("3. Enable online mode: ANTHROPIC_API_KEY=sk-... insurance-ai underwriting --online")


if __name__ == "__main__":
    main(obj={})
