# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI entry point aligned to the canonical runtime flow."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import import_module
import importlib.metadata
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

if TYPE_CHECKING:
    import click
else:
    try:
        import click
    except ModuleNotFoundError:

        class _ClickDecoratorShim:
            def __call__(self, func: Any) -> Any:
                return func

        class _ClickTypeShim:
            def __init__(self, *_args: object, **_kwargs: object) -> None:
                pass

        class _ClickCommandShim:
            def __init__(self, callback: Any) -> None:
                self.callback = callback
                self.name = getattr(callback, "__name__", "cli")

            def __call__(self, *args: object, **kwargs: object) -> Any:
                return self.callback(*args, **kwargs)

            def command(self, *_args: object, **_kwargs: object) -> Any:
                def _decorator(func: Any) -> Any:
                    return func

                return _decorator

            def group(self, *_args: object, **_kwargs: object) -> Any:
                def _decorator(func: Any) -> _ClickCommandShim:
                    return _ClickCommandShim(func)

                return _decorator

        class _ClickShim:
            Path = _ClickTypeShim
            Choice = _ClickTypeShim

            @staticmethod
            def echo(message: object = "") -> None:
                print(message)

            @staticmethod
            def group(*_args: object, **_kwargs: object) -> Any:
                def _decorator(func: Any) -> _ClickCommandShim:
                    return _ClickCommandShim(func)

                return _decorator

            @staticmethod
            def version_option(*_args: object, **_kwargs: object) -> Any:
                return _ClickDecoratorShim()

            @staticmethod
            def option(*_args: object, **_kwargs: object) -> Any:
                return _ClickDecoratorShim()

            @staticmethod
            def argument(*_args: object, **_kwargs: object) -> Any:
                return _ClickDecoratorShim()

        click = cast(Any, _ClickShim())

if TYPE_CHECKING:
    from bijux_proteomics_intelligence.candidates import CandidateStore
    from bijux_proteomics_intelligence.candidates.schema import Candidate
    from bijux_proteomics_runtime.runs.manager import RunManager
    from bijux_proteomics_runtime.runs.request import RunRequest
    from bijux_proteomics_runtime.runs.run_config import RunConfig
    from bijux_proteomics_runtime.support.workspace import RunWorkspace

__all__ = [
    "CliResult",
    "_artifact_hashes",
    "_artifact_paths",
    "_build_run_config",
    "_emit_json_payload",
    "_emit_run_summary_human",
    "_export_report_payload",
    "_load_run_config",
    "_load_run_summary",
    "_import_result",
    "_read_sequence",
    "_resume_candidate",
    "_write_output",
    "cli",
]

class _RunsOperationsModule(Protocol):
    def build_runtime_run_config(
        self,
        *,
        rounds: int,
        dry_run: bool,
        logging_enabled: bool,
        provider: str | None,
        artifacts_dir: Path | None,
        execution_mode: str,
        launch_surface: str = "local",
    ) -> RunConfig: ...

    def run_sequence_operation(
        self,
        base_dir: Path,
        sequence: str,
        config: RunConfig,
    ) -> dict[str, Any]: ...

    def resume_candidate_operation(
        self,
        base_dir: Path,
        *,
        candidate_id: str,
        rounds: int,
        provider: str | None,
        artifacts_dir: Path | None,
        execution_mode: str,
    ) -> dict[str, Any]: ...

    def import_external_result_operation(
        self,
        base_dir: Path,
        *,
        sequence: str,
        source_path: Path,
        engine_name: str,
        engine_version: str,
        artifacts_dir: Path | None = None,
    ) -> dict[str, Any]: ...

    def compare_run_operation(self, run_a: Path, run_b: Path) -> dict[str, Any]: ...

    def inspect_candidate_operation(
        self,
        base_dir: Path,
        candidate_id: str,
    ) -> Candidate: ...

    def load_run_summary_operation(
        self,
        base_dir: Path,
        run_id: str,
        artifacts_dir: Path | None,
    ) -> dict[str, Any]: ...

    def load_run_config_operation(self, run_dir: Path) -> RunConfig: ...

    def export_report_operation(self, base_dir: Path, run_id: str) -> str: ...


_CLI_ERROR_TYPE = "https://bijux.dev/errors/cli"


def _api_catalog_module() -> Any:
    return import_module("bijux_proteomics_runtime.api.catalog")


def _api_schema_module() -> Any:
    return import_module("bijux_proteomics_runtime.api.v1.schema")


def _runs_correlation_module() -> Any:
    return import_module("bijux_proteomics_runtime.runs.correlation")


def _runs_operations_module() -> _RunsOperationsModule:
    return cast(
        _RunsOperationsModule,
        import_module("bijux_proteomics_runtime.runs.operations"),
    )


def _run_request_type() -> type[RunRequest]:
    from bijux_proteomics_runtime.runs.request import RunRequest as RuntimeRunRequest

    return RuntimeRunRequest


def _run_workspace_type() -> type[RunWorkspace]:
    from bijux_proteomics_runtime.support.workspace import (
        RunWorkspace as RuntimeRunWorkspace,
    )

    return RuntimeRunWorkspace


def _runtime_banner() -> str:
    from bijux_proteomics_runtime.support.identity import runtime_banner

    return runtime_banner()


def _model_dump_json(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _candidate_store_type() -> type[CandidateStore]:
    """Load the candidate store only for commands that resume stored candidates."""
    from bijux_proteomics_intelligence.candidates import CandidateStore

    return CandidateStore


def _run_manager_type() -> type[RunManager]:
    """Load the runtime manager only for commands that execute candidate replay."""
    from bijux_proteomics_runtime.runs.manager import RunManager

    return RunManager


def _result_run_id(result: dict[str, Any]) -> str:
    """Read one run identifier from an operation result payload."""
    run_id = result.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run output missing run_id")
    return run_id


def _package_version() -> str:
    try:
        return importlib.metadata.version("bijux-proteomics-runtime")
    except importlib.metadata.PackageNotFoundError:
        return "0+local"


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


@dataclass(slots=True)
class CliResult:
    """CliResult."""

    status: Literal["ok", "error"]
    command: str
    payload: dict[str, Any] | list[Any] | str | None = None
    artifacts: dict[str, str] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status == "ok" and self.payload is None:
            raise ValueError("payload required for ok status")
        if self.status == "error" and not self.error:
            raise ValueError("error required for error status")

    def model_dump(self, *, mode: str = "json") -> dict[str, Any]:
        if mode != "json":
            raise ValueError("CliResult only supports json-style dumps")
        return {
            "status": self.status,
            "command": self.command,
            "payload": self.payload,
            "artifacts": self.artifacts,
            "error": self.error,
        }


def _build_run_config(
    rounds: int,
    dry_run: bool,
    no_logs: bool,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
) -> RunConfig:
    """_build_run_config."""
    return _runs_operations_module().build_runtime_run_config(
        rounds=rounds,
        dry_run=dry_run,
        logging_enabled=not no_logs,
        provider=provider,
        artifacts_dir=artifacts_dir,
        execution_mode=execution_mode,
    )


def _validate_sequence(sequence: str) -> None:
    """_validate_sequence."""
    _run_request_type().model_validate({"sequence": sequence})


def _run_sequence(base_dir: Path, sequence: str, config: RunConfig) -> dict[str, Any]:
    """_run_sequence."""
    return _runs_operations_module().run_sequence_operation(base_dir, sequence, config)


def _resume_candidate(
    base_dir: Path,
    candidate_id: str,
    rounds: int,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
) -> dict[str, Any]:
    """_resume_candidate."""
    return _runs_operations_module().resume_candidate_operation(
        base_dir,
        candidate_id=candidate_id,
        rounds=rounds,
        provider=provider,
        artifacts_dir=artifacts_dir,
        execution_mode=execution_mode,
    )


def _import_result(
    base_dir: Path,
    *,
    sequence: str,
    source_path: Path,
    engine_name: str,
    engine_version: str,
    artifacts_dir: Path | None,
) -> dict[str, Any]:
    """_import_result."""
    return _runs_operations_module().import_external_result_operation(
        base_dir,
        sequence=sequence,
        source_path=source_path,
        engine_name=engine_name,
        engine_version=engine_version,
        artifacts_dir=artifacts_dir,
    )


def _compare_runs_payload(run_a: Path, run_b: Path) -> dict[str, Any]:
    """_compare_runs_payload."""
    return _runs_operations_module().compare_run_operation(run_a, run_b)


def _inspect_candidate(base_dir: Path, candidate_id: str) -> Candidate:
    """_inspect_candidate."""
    return _runs_operations_module().inspect_candidate_operation(base_dir, candidate_id)


def _export_report_payload(base_dir: Path, run_id: str) -> str:
    """_export_report_payload."""
    return _runs_operations_module().export_report_operation(base_dir, run_id)


def _write_output(path: Path, payload: str) -> None:
    """_write_output."""
    path.write_text(payload)


def _artifact_paths(
    base_dir: Path, run_id: str, artifacts_dir: Path | None
) -> dict[str, str]:
    """_artifact_paths."""
    workspace = _run_workspace_type().for_run(
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


def _emit_json_payload(payload: dict[str, Any] | list[Any] | str, pretty: bool) -> None:
    """_emit_json_payload."""
    if pretty:
        click.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    click.echo(json.dumps(payload, sort_keys=True, default=str))


def _emit_api_envelope(
    data: Any | None,
    *,
    pretty: bool,
    error: Any | None = None,
    meta: dict[str, Any] | None = None,
    surface: str = "cli",
    correlation_key: str | None = None,
) -> None:
    """Emit a canonical API-style envelope for CLI JSON flows."""
    base_meta = _runs_correlation_module().build_correlation_meta(
        surface,
        f"cli:{surface}",
        correlation_key,
    )
    if meta:
        base_meta.update(meta)
    payload = (
        _api_schema_module()
        .ApiEnvelope(
            status="error" if error is not None else "ok",
            data=data,
            error=error,
            meta=base_meta,
        )
        .model_dump(mode="json")
    )
    _emit_json_payload(payload, pretty=pretty)


def _load_run_summary(
    base_dir: Path, run_id: str, artifacts_dir: Path | None
) -> dict[str, Any]:
    """_load_run_summary."""
    return _runs_operations_module().load_run_summary_operation(
        base_dir, run_id, artifacts_dir
    )


def _load_run_config(run_dir: Path) -> RunConfig:
    """_load_run_config."""
    return _runs_operations_module().load_run_config_operation(run_dir)


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
        click.echo(f"  bijux-proteomics-runtime inspect-candidate {candidate_id}")
        click.echo(f"  bijux-proteomics-runtime resume  {candidate_id} --approve")


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
    version=_package_version(),
    package_name="bijux-proteomics-runtime",
)
def cli() -> None:
    """bijux-proteomics-runtime CLI (lab-oriented)."""


@cli.command("identity")
def identity_command() -> None:
    """identity_command."""
    click.echo(_runtime_banner())


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
        run_id = _result_run_id(result)
        summary = _load_run_summary(Path.cwd(), run_id, artifacts_dir)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            schema = _api_schema_module()
            _emit_api_envelope(
                None,
                pretty=pretty,
                surface="run",
                error=schema.ErrorResponse(
                    type=_CLI_ERROR_TYPE,
                    title="CLI error",
                    status=1,
                    detail=str(exc),
                    instance="cli:run",
                    failure_class="cli",
                    remediation_hint="inspect the CLI arguments and local runtime state",
                    evidence_pointer=None,
                ),
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        schema = _api_schema_module()
        _emit_api_envelope(
            schema.RunResponse.model_validate(summary),
            pretty=pretty,
            surface="run",
            correlation_key=run_id,
        )
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
        run_id = _result_run_id(result)
        summary = _load_run_summary(Path.cwd(), run_id, artifacts_dir)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            schema = _api_schema_module()
            _emit_api_envelope(
                None,
                pretty=pretty,
                surface="resume",
                error=schema.ErrorResponse(
                    type=_CLI_ERROR_TYPE,
                    title="CLI error",
                    status=1,
                    detail=str(exc),
                    instance="cli:resume",
                    failure_class="cli",
                    remediation_hint="inspect the CLI arguments and local runtime state",
                    evidence_pointer=None,
                ),
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        schema = _api_schema_module()
        _emit_api_envelope(
            schema.RunResponse.model_validate(summary),
            pretty=pretty,
            surface="resume",
            correlation_key=run_id,
        )
        return
    _emit_run_summary_human(summary)


@cli.command("import-result")
@click.option("--sequence", type=str, required=True, help="Amino acid sequence.")
@click.option(
    "--source",
    type=click.Path(path_type=Path),
    required=True,
    help="External engine result file path.",
)
@click.option("--engine-name", type=str, required=True, help="External engine name.")
@click.option(
    "--engine-version", type=str, required=True, help="External engine version."
)
@click.option(
    "--artifacts-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Write artifacts under this directory.",
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def import_result(
    sequence: str,
    source: Path,
    engine_name: str,
    engine_version: str,
    artifacts_dir: Path | None,
    pretty: bool,
    json_output: bool,
) -> None:
    """import_result."""
    try:
        _validate_sequence(sequence)
        result = _import_result(
            Path.cwd(),
            sequence=sequence,
            source_path=source,
            engine_name=engine_name,
            engine_version=engine_version,
            artifacts_dir=artifacts_dir,
        )
        run_id = _result_run_id(result)
        summary = _load_run_summary(Path.cwd(), run_id, artifacts_dir)
    except Exception as exc:  # noqa: BLE001
        if json_output:
            schema = _api_schema_module()
            _emit_api_envelope(
                None,
                pretty=pretty,
                surface="import",
                error=schema.ErrorResponse(
                    type=_CLI_ERROR_TYPE,
                    title="CLI error",
                    status=1,
                    detail=str(exc),
                    instance="cli:import",
                    failure_class="cli",
                    remediation_hint="inspect the import source and runtime state",
                    evidence_pointer=None,
                ),
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        schema = _api_schema_module()
        _emit_api_envelope(
            schema.RunResponse.model_validate(summary),
            pretty=pretty,
            surface="import",
            correlation_key=run_id,
        )
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
            schema = _api_schema_module()
            _emit_api_envelope(
                None,
                pretty=pretty,
                surface="compare",
                error=schema.ErrorResponse(
                    type=_CLI_ERROR_TYPE,
                    title="CLI error",
                    status=1,
                    detail=str(exc),
                    instance="cli:compare",
                    failure_class="cli",
                    remediation_hint="inspect the CLI arguments and local runtime state",
                    evidence_pointer=None,
                ),
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    if json_output:
        schema = _api_schema_module()
        _emit_api_envelope(
            schema.CompareResponse.model_validate(comparison),
            pretty=pretty,
            surface="compare",
            correlation_key=f"{run_a}:{run_b}",
        )
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
            schema = _api_schema_module()
            _emit_api_envelope(
                None,
                pretty=pretty,
                surface="inspect-candidate",
                error=schema.ErrorResponse(
                    type=_CLI_ERROR_TYPE,
                    title="CLI error",
                    status=1,
                    detail=str(exc),
                    instance="cli:inspect-candidate",
                    failure_class="cli",
                    remediation_hint="inspect the CLI arguments and local runtime state",
                    evidence_pointer=None,
                ),
            )
        else:
            click.echo(f"Error: {exc}")
        raise SystemExit(1) from exc
    schema = _api_schema_module()
    payload = schema.InspectResponse(
        candidate=schema.ApiCandidate.model_validate(candidate.model_dump(mode="json")),
        qc_status=None,
        artifacts={},
    )
    if json_output:
        _emit_api_envelope(
            payload,
            pretty=pretty,
            surface="inspect-candidate",
            correlation_key=candidate_id,
        )
        return
    _emit_json_payload(_model_dump_json(payload), pretty=True)


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
    import uvicorn

    from bijux_proteomics_runtime.api import AppConfig, create_app

    config = AppConfig(base_dir=Path.cwd(), docs_enabled=not no_docs)
    app = create_app(config)
    uvicorn.run(app, host=host, port=port, reload=reload)


@api.command("status")
@click.argument("run_id", type=str)
@click.option("--include-documents", is_flag=True, help="Inline small documents.")
@click.option("--max-inline-bytes", type=int, default=256000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_status(
    run_id: str, include_documents: bool, max_inline_bytes: int, pretty: bool
) -> None:
    """Emit the canonical runtime-status contract via CLI."""
    response = _api_catalog_module().build_runtime_status_response(
        Path.cwd(),
        run_id,
        include_documents=include_documents,
        max_inline_bytes=max_inline_bytes,
    )
    _emit_api_envelope(
        response, pretty=pretty, surface="runtime-status", correlation_key=run_id
    )


@api.command("artifacts")
@click.argument("run_id", type=str)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_artifacts(run_id: str, pretty: bool) -> None:
    """Emit the canonical run-artifacts contract via CLI."""
    response = _api_catalog_module().build_run_artifacts_response(Path.cwd(), run_id)
    _emit_api_envelope(
        response, pretty=pretty, surface="run-artifacts", correlation_key=run_id
    )


@api.command("evidence-bundle")
@click.argument("run_id", type=str)
@click.option("--include-document", is_flag=True, help="Inline small documents.")
@click.option("--max-inline-bytes", type=int, default=256000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_evidence_bundle(
    run_id: str,
    include_document: bool,
    max_inline_bytes: int,
    pretty: bool,
) -> None:
    """Emit the canonical evidence-bundle contract via CLI."""
    response = _api_catalog_module().build_run_evidence_response(
        Path.cwd(),
        run_id,
        include_document=include_document,
        max_inline_bytes=max_inline_bytes,
    )
    _emit_api_envelope(
        response,
        pretty=pretty,
        surface="run-evidence-bundle",
        correlation_key=run_id,
    )


@api.command("review-packet")
@click.argument("run_id", type=str)
@click.option("--include-document", is_flag=True, help="Inline small documents.")
@click.option("--max-inline-bytes", type=int, default=256000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_review_packet(
    run_id: str,
    include_document: bool,
    max_inline_bytes: int,
    pretty: bool,
) -> None:
    """Emit the canonical review-packet contract via CLI."""
    response = _api_catalog_module().build_run_review_response(
        Path.cwd(),
        run_id,
        include_document=include_document,
        max_inline_bytes=max_inline_bytes,
    )
    _emit_api_envelope(
        response,
        pretty=pretty,
        surface="run-review-packet",
        correlation_key=run_id,
    )


@api.command("health")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_health(pretty: bool) -> None:
    """Emit the canonical runtime health contract via CLI."""
    response = _api_catalog_module().build_runtime_health_response(Path.cwd())
    _emit_api_envelope(response, pretty=pretty, surface="runtime-health")


@api.command("history")
@click.option("--provider", type=str, default=None)
@click.option("--workflow-state", type=str, default=None)
@click.option("--outcome", type=str, default=None)
@click.option("--candidate-id", type=str, default=None)
@click.option("--cursor", type=str, default=None)
@click.option("--page-size", type=int, default=20, show_default=True)
@click.option("--max-query-cost", type=int, default=1000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_history(
    provider: str | None,
    workflow_state: str | None,
    outcome: str | None,
    candidate_id: str | None,
    cursor: str | None,
    page_size: int,
    max_query_cost: int,
    pretty: bool,
) -> None:
    """Emit the canonical run-history contract via CLI."""
    response = _api_catalog_module().build_run_history_response(
        Path.cwd(),
        provider=provider,
        workflow_state=workflow_state,
        outcome=outcome,
        candidate_id=candidate_id,
        cursor=cursor,
        page_size=page_size,
        max_query_cost=max_query_cost,
    )
    _emit_api_envelope(response, pretty=pretty, surface="run-history")


@api.command("lookup-artifacts")
@click.option("--run-id", type=str, default=None)
@click.option("--artifact-kind", type=str, default=None)
@click.option("--cursor", type=str, default=None)
@click.option("--page-size", type=int, default=20, show_default=True)
@click.option("--max-query-cost", type=int, default=1000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_lookup_artifacts(
    run_id: str | None,
    artifact_kind: str | None,
    cursor: str | None,
    page_size: int,
    max_query_cost: int,
    pretty: bool,
) -> None:
    """Emit the canonical artifact-lookup contract via CLI."""
    response = _api_catalog_module().build_artifact_lookup_response(
        Path.cwd(),
        run_id=run_id,
        artifact_kind=artifact_kind,
        cursor=cursor,
        page_size=page_size,
        max_query_cost=max_query_cost,
    )
    _emit_api_envelope(response, pretty=pretty, surface="artifact-lookup")


@api.command("lookup-evidence")
@click.option("--run-id", type=str, default=None)
@click.option("--document-kind", type=str, default=None)
@click.option("--availability", type=str, default=None)
@click.option("--cursor", type=str, default=None)
@click.option("--page-size", type=int, default=20, show_default=True)
@click.option("--max-query-cost", type=int, default=1000, show_default=True)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
def api_lookup_evidence(
    run_id: str | None,
    document_kind: str | None,
    availability: str | None,
    cursor: str | None,
    page_size: int,
    max_query_cost: int,
    pretty: bool,
) -> None:
    """Emit the canonical evidence-lookup contract via CLI."""
    response = _api_catalog_module().build_evidence_lookup_response(
        Path.cwd(),
        run_id=run_id,
        document_kind=document_kind,
        availability=availability,
        cursor=cursor,
        page_size=page_size,
        max_query_cost=max_query_cost,
    )
    _emit_api_envelope(response, pretty=pretty, surface="evidence-lookup")


@cli.command("reproduce")
@click.argument("run_id", type=str)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output.")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
def reproduce(run_id: str, pretty: bool, json_output: bool) -> None:
    """reproduce."""
    try:
        base_dir = Path.cwd()
        original_workspace = _run_workspace_type().for_run(base_dir, run_id)
        if not original_workspace.run_dir.exists():
            raise FileNotFoundError(f"Run not found at {original_workspace.run_dir}")
        summary = json.loads(original_workspace.run_summary_path.read_text())
        candidate_id = summary.get("candidate_id") or f"{run_id}-c0"
        store = _candidate_store_type()(original_workspace.candidate_store_dir)
        candidate = store.get_candidate(candidate_id)
        config = _load_run_config(original_workspace.run_dir)
        reproduce_root = base_dir / "artifacts" / "reproduce"
        reproduce_workspace = _run_workspace_type().for_run(
            base_dir, run_id, artifacts_root_override=reproduce_root
        )
        if reproduce_workspace.run_dir.exists():
            raise FileExistsError(
                f"Reproduce run already exists at {reproduce_workspace.run_dir}"
            )
        reproduce_config = config.model_copy(
            update={"artifacts_dir": str(reproduce_root)}
        )
        manager = _run_manager_type()(base_dir, reproduce_config)
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
