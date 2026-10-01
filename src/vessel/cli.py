import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from vessel.artifacts import atomic_json
from vessel.auditing import record_audit
from vessel.datasets import dataset_digest, load_dataset, save_dataset, validate_dataset
from vessel.models import (
    Adjudication,
    Bundle,
    GoldRecord,
    Review,
    RunManifest,
    SearchResponse,
)
from vessel.reporting import compare_reports, generate_report
from vessel.runner import run as execute_run

app = typer.Typer(no_args_is_help=True, help="Independent visual-evidence evaluation.")


def fail(message: str):
    typer.echo(message, err=True)
    raise typer.Exit(1)


@app.command()
def doctor(config: Path | None = None):
    """Check local configuration without showing secrets or making API requests."""
    import os

    load_dotenv(Path.cwd() / ".env", override=False)
    typer.echo("Configuration only: no API requests; credentials and connectivity unverified.")
    for name in (
        "EVIDENCE8_BASE_URL",
        "EVIDENCE8_API_KEY",
        "KEENABLE_API_KEY",
        "EXA_API_KEY",
        "SERPER_API_KEY",
    ):
        state = "set" if os.getenv(name, "").strip() else "not set"
        if name == "EVIDENCE8_API_KEY" and state == "not set":
            state = "not set (optional for the documented local API)"
        typer.echo(f"{name}: {state}")
    if config:
        import yaml

        from vessel.runner import load_config, providers_for

        try:
            settings = load_config(config)
            providers = providers_for(settings, None)
        except (ValueError, OSError, yaml.YAMLError):
            fail("Could not read configuration; check YAML against the RunConfig schema.")
        typer.echo(
            f"Budget: ${settings.max_cost_usd:.4f}; maximum requests: {settings.max_requests}"
        )
        for setting in settings.providers:
            provider = providers[setting.name]
            if setting.name == "keenable_evidence8":
                configured = (
                    provider.search_provider.configured()
                    and provider.evidence_provider.configured()
                )
                ceilings = (
                    provider.search_provider.config.request_cost_ceiling_usd,
                    provider.evidence_provider.config.request_cost_ceiling_usd,
                )
            else:
                configured = provider.configured()
                ceilings = (setting.request_cost_ceiling_usd,)
            state = "configured" if configured else "missing configuration"
            if any(c is None for c in ceilings):
                state += "; skipped until request cost ceilings are configured"
            elif any(c > settings.max_cost_usd for c in ceilings):
                state += "; spending cap cannot cover one request"
            typer.echo(f"{setting.name}: {state}")


@app.command()
def validate(dataset: Path, release: bool = False):
    """Validate records; --release enforces independently reviewed Core-100 gates."""
    try:
        records = load_dataset(dataset)
        issues = validate_dataset(records, release)
    except (ValueError, OSError) as error:
        fail(str(error))
    if issues:
        fail("\n".join(issues))
    typer.echo(f"Valid: {len(records)} records; digest {dataset_digest(records)}")


@app.command()
def run(
    dataset: Path, config: Path, output: Path, fixture: Path | None = None, resume: bool = False
):
    """Run configured providers or explicitly synthetic development fixtures."""
    load_dotenv(Path.cwd() / ".env", override=False)
    try:
        manifest = execute_run(dataset, config, output, fixture, resume)
        generate_report(output)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo(f"{manifest.status}: {output / 'report.json'}")
    typer.echo(f"Requests: {manifest.requests}; reserved cost: ${manifest.reserved_cost_usd:.4f}")
    if manifest.status != "complete":
        raise typer.Exit(2)


@app.command()
def report(run_dir: Path, output: Path | None = None, adjudications: Path | None = None):
    """Rescore archived receipts without provider requests."""
    try:
        judgments = (
            [Adjudication.model_validate(row) for row in json.loads(adjudications.read_text())]
            if adjudications
            else []
        )
        result = generate_report(run_dir, output, judgments)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo(result["notice"])
    for provider, scores in result["summary"].items():
        typer.echo(
            f"{provider}: Full Support@{max(scores, key=int)} = "
            f"{scores[max(scores, key=int)]['full_support']:.1%}"
        )


@app.command()
def replay(run_dir: Path, output: Path | None = None):
    """Verify receipt integrity and reproduce scores from an existing archive."""
    report(run_dir, output, None)


@app.command()
def compare(first: Path, second: Path, output: Path):
    """Compare complete reports with matching data and protocol configuration."""
    try:
        comparisons = compare_reports(json.loads(first.read_text()), json.loads(second.read_text()))
        atomic_json(output, comparisons)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo(str(output))


@app.command()
def review(
    dataset: Path,
    query_id: str,
    reviewer: Annotated[str, typer.Option(help="Actual human reviewer identity")],
    role: Annotated[str, typer.Option(help="author or independent")],
    notes: Annotated[str, typer.Option(help="Primary-source validation and review notes")],
    decision: str = "approved",
):
    """Record a human decision bound to the current record digest; never auto-approve."""
    try:
        records = load_dataset(dataset)
        record = next((r for r in records if r.query_id == query_id), None)
        if record is None:
            raise ValueError("query ID not found")
        record.reviews.append(
            Review(
                reviewer=reviewer,
                role=role,
                decision=decision,
                notes=notes,
                content_sha256=record.content_digest(),
                reviewed_at=datetime.now(UTC),
            )
        )
        save_dataset(dataset, records)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo(f"Recorded {role} review; current independent approval: {record.reviewed()}")


@app.command()
def audit(
    run_dir: Path,
    reviewer: Annotated[str, typer.Option(help="Actual human auditor identity")],
    notes: Annotated[str, typer.Option(help="Failure and provenance audit notes")],
):
    """Record an actual human audit bound to every archived receipt."""
    try:
        record_audit(run_dir, reviewer, notes)
        generate_report(run_dir)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo("Recorded a digest-bound human audit.")


@app.command()
def schemas(output: Path = Path("schemas")):
    """Export versioned JSON schemas for records, responses and reports."""
    for model in (GoldRecord, Bundle, SearchResponse, RunManifest, Adjudication):
        atomic_json(output / f"{model.__name__}.schema.json", model.model_json_schema())
    typer.echo(str(output))


@app.command()
def export(run_dir: Path, output: Path, public_release: bool = False):
    """Export the explorer report. --public-release rejects unmet release gates."""
    try:
        result = generate_report(run_dir)
        if public_release:
            records = [
                GoldRecord.model_validate(r)
                for r in json.loads((run_dir / "dataset.json").read_text())
            ]
            issues = validate_dataset(records, release=True)
            if dataset_digest(records) != result["manifest"]["dataset_sha256"]:
                issues.append("archived dataset digest mismatch")
            if not result["manifest"]["publication_eligible"]:
                issues.append("run is not publication eligible")
            if issues:
                raise ValueError("Publication rejected:\n" + "\n".join(issues))
        atomic_json(output, result)
    except (ValueError, OSError) as error:
        fail(str(error))
    typer.echo(f"Exported {result['notice']}: {output}")


if __name__ == "__main__":
    app()
