# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI entry point aligned to the canonical runtime flow."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any, Literal

import click
from pydantic import BaseModel, ConfigDict, Field, model_validator
import uvicorn

from agentic_proteins.domain.candidates import CandidateStore
from agentic_proteins.domain.candidates.schema import Candidate
from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.context import RunOutput, RunRequest
from agentic_proteins.runtime.control import compare_runs
from agentic_proteins.runtime.infra import RunConfig
from agentic_proteins.runtime.workspace import RunWorkspace


def _read_sequence(sequence: str | None, fasta: Path | None) -> str:
    """_read_sequence."""
    if sequence and fasta:
        raise ValueError("Provide either --sequence or --fasta, not both.")
    if fasta:
        text = fasta.read_text().strip().splitlines()
        seq = "".join(line.strip() for line in text if not line.startswith(">"))
        if not seq:
            raise ValueError("No sequence found in FASTA.")
        return seq
    if sequence:
        seq = sequence.strip()
        if not seq:
            raise ValueError("Empty sequence.")
        return seq
    raise ValueError("Provide --sequence or --fasta.")


class CliResult(BaseModel):
    """CliResult."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"] = Field(..., description="Result status.")
    command: str = Field(..., description="CLI command name.")
    payload: dict[str, Any] | list[Any] | str | None = Field(
        default=None, description="Command payload."
    )
    artifacts: dict[str, str] | None = Field(
        default=None, description="Artifact paths, when applicable."
    )
    error: str | None = Field(default=None, description="Error message.")

    @model_validator(mode="after")
    def _ensure_contract(self) -> CliResult:
        """_ensure_contract."""
        if self.status == "ok" and self.payload is None:
            raise ValueError("payload required for ok status")
        if self.status == "error" and not self.error:
            raise ValueError("error required for error status")
        return self


def _build_run_config(
    rounds: int,
    dry_run: bool,
    no_logs: bool,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
) -> RunConfig:
    """_build_run_config."""
    if rounds < 1:
        raise ValueError("--rounds must be >= 1")
    providers = {
        None: ["heuristic_proxy"],
        "esmfold": ["local_esmfold"],
        "local_esmfold": ["local_esmfold"],
        "rosettafold": ["local_rosettafold"],
        "local_rosettafold": ["local_rosettafold"],
        "openprotein": ["api_openprotein_esmfold"],
    }
    if provider not in providers:
        raise ValueError(
            "--provider must be one of: esmfold, local_esmfold, rosettafold, local_rosettafold, openprotein"
        )
    resource_limits = {"cpu_seconds": 0.0, "gpu_seconds": 0.0}
    if provider in {"esmfold", "rosettafold"}:
        resource_limits["gpu_seconds"] = 1.0
    return RunConfig(
        dry_run=dry_run,
        logging_enabled=not no_logs,
        loop_max_iterations=rounds,
        predictors_enabled=providers[provider],
        resource_limits=resource_limits,
        artifacts_dir=str(artifacts_dir) if artifacts_dir else None,
        execution_mode=execution_mode,
    )


def _validate_sequence(sequence: str) -> None:
    """_validate_sequence."""
    RunRequest.model_validate({"sequence": sequence})


def _run_sequence(base_dir: Path, sequence: str, config: RunConfig) -> dict:
    """_run_sequence."""
    manager = RunManager(base_dir, config)
    return manager.run(sequence)


def _resume_candidate(
    base_dir: Path,
    candidate_id: str,
    rounds: int,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
) -> dict:
    """_resume_candidate."""
    if rounds < 1:
        raise ValueError("--rounds must be >= 1")
    store = CandidateStore(RunWorkspace.for_run(base_dir, "noop").candidate_store_dir)
    candidate = store.get_candidate(candidate_id)
    config = _build_run_config(
        rounds,
        dry_run=False,
        no_logs=False,
        provider=provider,
        artifacts_dir=artifacts_dir,
        execution_mode=execution_mode,
    )
    manager = RunManager(base_dir, config)
    return manager.run_candidate(candidate)


def _compare_runs_payload(run_a: Path, run_b: Path) -> dict:
    """_compare_runs_payload."""
    return compare_runs(run_a, run_b)


def _inspect_candidate(base_dir: Path, candidate_id: str) -> Candidate:
    """_inspect_candidate."""
    store = CandidateStore(RunWorkspace.for_run(base_dir, "noop").candidate_store_dir)
    return store.get_candidate(candidate_id)


def _export_report_payload(base_dir: Path, run_id: str) -> str:
    """_export_report_payload."""
    report_path = RunWorkspace.for_run(base_dir, run_id).report_path
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found at {report_path}")
    return report_path.read_text()


def _write_output(path: Path, payload: str) -> None:
    """_write_output."""
    path.write_text(payload)


def _artifact_paths(
    base_dir: Path, run_id: str, artifacts_dir: Path | None
) -> dict[str, str]:
    """_artifact_paths."""
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    return {
        "run_dir": str(workspace.run_dir),
        "run_output_path": str(workspace.run_output_path),
        "run_summary_path": str(workspace.run_summary_path),
        "plan_path": str(workspace.plan_path),
        "execution_path": str(workspace.execution_path),
        "report_path": str(workspace.report_path),
        "telemetry_path": str(workspace.telemetry_path),
        "logs_path": str(workspace.logs_dir / "run.jsonl"),
        "timings_path": str(workspace.timings_path),
        "state_path": str(workspace.state_path),
        "config_path": str(workspace.config_path),
    }


def _emit_json_payload(payload: dict | list | str, pretty: bool) -> None:
    """_emit_json_payload."""
    if pretty:
        click.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    click.echo(json.dumps(payload, sort_keys=True, default=str))


def _load_run_summary(
    base_dir: Path, run_id: str, artifacts_dir: Path | None
) -> dict[str, Any]:
    """_load_run_summary."""
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    return json.loads(workspace.run_summary_path.read_text())


def _load_run_config(run_dir: Path) -> RunConfig:
    """_load_run_config."""
    config_path = run_dir / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found at {config_path}")
    return RunConfig.model_validate(json.loads(config_path.read_text()))


def _emit_run_summary_human(summary: dict[str, Any]) -> None:
    """_emit_run_summary_human."""
    click.echo("")
    if summary.get("execution_status") == "completed":
        click.echo("✔ Run completed")
    else:
        click.echo("✖ Run failed")
    click.echo("")
    click.echo(f"Run ID:        {summary['run_id']}")
    click.echo(f"Provider:      {summary.get('provider', 'unknown')}")
    if summary.get("tool_status") == "degraded":
        click.echo("Execution:     CPU fallback (degraded)")
    click.echo(f"QC status:     {summary.get('qc_status', 'unknown')}")
    click.echo(f"Workflow:      {summary.get('workflow_state', 'unknown')}")
    if summary.get("failure"):
        click.echo(f"Failure:       {summary['failure']}")
    click.echo("")
    click.echo("Artifacts:")
    click.echo(f"  {summary.get('artifacts_dir')}")
    if summary.get("workflow_state") == "awaiting_human_review":
        click.echo("")
        click.echo("Next steps:")
        candidate_id = summary.get("candidate_id", summary["run_id"])
        click.echo(f"  agentic-proteins inspect-candidate {candidate_id}")
        click.echo(f"  agentic-proteins resume  {candidate_id} --approve")


def _artifact_hashes(run_dir: Path) -> dict[str, str]:
    """_artifact_hashes."""
    artifacts_dir = run_dir / "artifacts"
    if not artifacts_dir.exists():
        raise FileNotFoundError(f"Artifacts not found at {artifacts_dir}")
    hashes: dict[str, str] = {}
    for path in sorted(artifacts_dir.glob("*.json")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.name] = digest
    return hashes


@click.group()
@click.version_option(
    version=importlib.metadata.version("agentic-proteins"),
    package_name="agentic-proteins",
)
def cli() -> None:
    """Agentic Proteins CLI (lab-oriented)."""


@cli.command("run")
@click.option("--sequence", type=str, help="Inline amino acid sequence.")
@click.option("--fasta", type=click.Path(path_type=Path), help="FASTA file path.")
@click.option("--rounds", type=int, default=1, show_default=True)
@click.option(
    "--provider",
    type=click.Choice(
        ["esmfold", "local_esmfold", "rosettafold", "local_rosettafold", "openprotein"]
    ),
    default=None,
    help="Enable real structure predictors (opt-in).",
)
@click.option(
    "--artifacts-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Write artifacts under this directory.",
)
@click.option(
    "--dry-run", is_flag=True, help="Plan and validate without executing tools."
)
@click.option("--no-logs", is_flag=True, help="Disable structured logging.")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
@click.option(
    "--execution-mode",
    type=click.Choice(["auto", "gpu", "cpu"]),
    default="auto",
    show_default=True,
    help="Select provider execution mode.",
)
def run(
    sequence: str | None,
    fasta: Path | None,
    rounds: int,
    provider: str | None,
    artifacts_dir: Path | None,
    dry_run: bool,
    no_logs: bool,
    pretty: bool,
    json_output: bool,
    execution_mode: str,
) -> None:
    """run."""
    try:
        seq = _read_sequence(sequence, fasta)
        _validate_sequence(seq)
        config = _build_run_config(
            rounds,
            dry_run,
            no_logs,
            provider,
            artifacts_dir,
            execution_mode,
        )
        result = _run_sequence(Path.cwd(), seq, config)
        run_output = RunOutput.model_validate(result)
        summary = _load_run_summary(Path.cwd(), run_output.run_id, artifacts_dir)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(status="error", command="run", error=str(exc)).model_dump(
                    mode="json"
                ),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        _emit_json_payload(summary, pretty=pretty)
        return
    _emit_run_summary_human(summary)


@cli.command("resume")
@click.argument("candidate_id", type=str)
@click.option("--rounds", type=int, default=1, show_default=True)
@click.option(
    "--provider",
    type=click.Choice(
        ["esmfold", "local_esmfold", "rosettafold", "local_rosettafold", "openprotein"]
    ),
    default=None,
    help="Enable real structure predictors (opt-in).",
)
@click.option(
    "--artifacts-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Write artifacts under this directory.",
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
@click.option(
    "--execution-mode",
    type=click.Choice(["auto", "gpu", "cpu"]),
    default="auto",
    show_default=True,
    help="Select provider execution mode.",
)
def resume(
    candidate_id: str,
    rounds: int,
    provider: str | None,
    artifacts_dir: Path | None,
    pretty: bool,
    json_output: bool,
    execution_mode: str,
) -> None:
    """resume."""
    try:
        result = _resume_candidate(
            Path.cwd(),
            candidate_id,
            rounds,
            provider,
            artifacts_dir,
            execution_mode,
        )
        run_output = RunOutput.model_validate(result)
        summary = _load_run_summary(Path.cwd(), run_output.run_id, artifacts_dir)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(status="error", command="resume", error=str(exc)).model_dump(
                    mode="json"
                ),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        _emit_json_payload(summary, pretty=pretty)
        return
    _emit_run_summary_human(summary)


@cli.command("compare")
@click.argument("run_a", type=click.Path(path_type=Path))
@click.argument("run_b", type=click.Path(path_type=Path))
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def compare(run_a: Path, run_b: Path, pretty: bool, json_output: bool) -> None:
    """compare."""
    try:
        comparison = _compare_runs_payload(run_a, run_b)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(status="error", command="compare", error=str(exc)).model_dump(
                    mode="json"
                ),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        _emit_json_payload(comparison, pretty=pretty)
        return
    _emit_json_payload(comparison, pretty=True)


@cli.command("inspect-candidate")
@click.argument("candidate_id", type=str)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def inspect_candidate(candidate_id: str, pretty: bool, json_output: bool) -> None:
    """inspect_candidate."""
    try:
        candidate = _inspect_candidate(Path.cwd(), candidate_id)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(
                    status="error",
                    command="inspect-candidate",
                    error=str(exc),
                ).model_dump(mode="json"),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    payload = candidate.model_dump()
    if json_output:
        _emit_json_payload(payload, pretty=pretty)
        return
    _emit_json_payload(payload, pretty=True)


@cli.command("export-report")
@click.argument("run_id", type=str)
@click.option("--output", type=click.Path(path_type=Path), default=None)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def export_report(
    run_id: str, output: Path | None, pretty: bool, json_output: bool
) -> None:
    """export_report."""
    try:
        report = _export_report_payload(Path.cwd(), run_id)
        if output:
            _write_output(output, report)
            payload = {"output_path": str(output)}
        else:
            payload = {"report": report}
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(
                    status="error", command="export-report", error=str(exc)
                ).model_dump(mode="json"),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        _emit_json_payload(payload, pretty=pretty)
        return
    _emit_json_payload(payload, pretty=True)


@cli.group("api")
def api() -> None:
    """api."""


@api.command("serve")
@click.option("--host", type=str, default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=8000, show_default=True)
@click.option("--reload", is_flag=True, help="Auto-reload on changes.")
@click.option("--no-docs", is_flag=True, help="Disable OpenAPI docs.")
def api_serve(host: str, port: int, reload: bool, no_docs: bool) -> None:
    """api_serve."""
    from agentic_proteins.api import AppConfig, create_app

    config = AppConfig(base_dir=Path.cwd(), docs_enabled=not no_docs)
    app = create_app(config)
    uvicorn.run(app, host=host, port=port, reload=reload)


@cli.command("reproduce")
@click.argument("run_id", type=str)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def reproduce(run_id: str, pretty: bool, json_output: bool) -> None:
    """reproduce."""
    try:
        base_dir = Path.cwd()
        original_workspace = RunWorkspace.for_run(base_dir, run_id)
        if not original_workspace.run_dir.exists():
            raise FileNotFoundError(f"Run not found at {original_workspace.run_dir}")
        summary = json.loads(original_workspace.run_summary_path.read_text())
        candidate_id = summary.get("candidate_id") or f"{run_id}-c0"
        store = CandidateStore(original_workspace.candidate_store_dir)
        candidate = store.get_candidate(candidate_id)
        config = _load_run_config(original_workspace.run_dir)
        reproduce_root = base_dir / "artifacts" / "reproduce"
        reproduce_workspace = RunWorkspace.for_run(
            base_dir, run_id, artifacts_root_override=reproduce_root
        )
        if reproduce_workspace.run_dir.exists():
            raise FileExistsError(
                f"Reproduce run already exists at {reproduce_workspace.run_dir}"
            )
        reproduce_config = config.model_copy(
            update={"artifacts_dir": str(reproduce_root)}
        )
        manager = RunManager(base_dir, reproduce_config)
        manager.run_candidate(candidate, run_id=run_id)
        original_hashes = _artifact_hashes(original_workspace.run_dir)
        reproduced_hashes = _artifact_hashes(reproduce_workspace.run_dir)
        if original_hashes != reproduced_hashes:
            raise ValueError(
                "Artifact hashes diverged between original and reproduced runs."
            )
        payload = {
            "run_id": run_id,
            "reproduced_run_dir": str(reproduce_workspace.run_dir),
            "artifact_hashes_match": True,
        }
    except Exception as exc:  # noqa: BLE001
        if json_output:
            _emit_json_payload(
                CliResult(
                    status="error", command="reproduce", error=str(exc)
                ).model_dump(mode="json"),
                pretty=pretty,
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        _emit_json_payload(payload, pretty=pretty)
        return
    _emit_json_payload(payload, pretty=True)


if __name__ == "__main__":
    cli()
