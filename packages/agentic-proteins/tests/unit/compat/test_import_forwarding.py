from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, cast

from click.testing import CliRunner

from agentic_proteins.interfaces.http import AppConfig as CompatAppConfig
from agentic_proteins.interfaces.http import create_app as compat_create_app
from agentic_proteins.interfaces.http.errors import _ERROR_TYPES as COMPAT_ERROR_TYPES
from agentic_proteins.interfaces.structure_reports import Report as CompatReport
from agentic_proteins.interfaces.structure_reports import nl_summary as compat_nl_summary
from agentic_proteins.interfaces.structure_reports import (
    confidence_summary as compat_confidence_summary,
)
from agentic_proteins.interfaces.structure_reports import format_pct as compat_format_pct
from agentic_proteins.interfaces.structure_reports import to_text as compat_to_text
from agentic_proteins.execution.evaluation.observations import (
    EvaluationInput as CompatEvaluationInput,
)
from agentic_proteins.interfaces.cli import (
    _artifact_hashes as compat_artifact_hashes,
)
from agentic_proteins.interfaces.cli import (
    _artifact_paths as compat_artifact_paths,
)
from agentic_proteins.interfaces.cli import (
    _build_run_config as compat_build_run_config,
)
from agentic_proteins.interfaces.cli import (
    _emit_json_payload as compat_emit_json_payload,
)
from agentic_proteins.interfaces.cli import (
    _emit_run_summary_human as compat_emit_run_summary_human,
)
from agentic_proteins.interfaces.cli import (
    _export_report_payload as compat_export_report_payload,
)
from agentic_proteins.interfaces.cli import (
    _load_run_config as compat_load_run_config,
)
from agentic_proteins.interfaces.cli import (
    _load_run_summary as compat_load_run_summary,
)
from agentic_proteins.interfaces.cli import (
    _read_sequence as compat_read_sequence,
)
from agentic_proteins.interfaces.cli import (
    _resume_candidate as compat_resume_candidate,
)
from agentic_proteins.interfaces.cli import (
    _write_output as compat_write_output,
)
from agentic_proteins.interfaces.cli import (
    cli as compat_cli,
)
from agentic_proteins.providers.base import _time_left as compat_time_left
from agentic_proteins.providers.selection import _require_module as compat_require_module
from agentic_proteins.agents.catalog import AgentCatalog as CompatAgentCatalog
from agentic_proteins.agents.catalog import AgentRegistry as CompatAgentRegistry
from agentic_proteins.tools.catalog import ToolCatalog as CompatToolCatalog
from agentic_proteins.tools.catalog import ToolRegistry as CompatToolRegistry
from agentic_proteins.runtime.control.artifacts import (
    _sign_payload as compat_sign_payload,
)
from agentic_proteins.runtime.control.execution import (
    _build_run_summary as compat_build_run_summary,
)
from agentic_proteins.runtime.control.execution import (
    _ensure_telemetry_costs as compat_ensure_telemetry_costs,
)
from agentic_proteins.runtime.control.execution import (
    _select_structure_tool as compat_select_structure_tool,
)
from agentic_proteins.runtime.control.execution import (
    _version_info as compat_version_info,
)
from agentic_proteins.providers.capabilities import KNOWN_PROVIDERS as COMPAT_KNOWN_PROVIDERS
from agentic_proteins.providers import capabilities as compat_capabilities
from agentic_proteins.providers.capabilities import (
    validate_runtime_capabilities as compat_validate_runtime_capabilities,
)
from agentic_proteins.agents.contracts import (
    _minimal_payload as compat_minimal_payload,
)
from agentic_proteins.agents.contracts import (
    _placeholder_for_type as compat_placeholder_for_type,
)
from bijux_proteomics_runtime.api import AppConfig as RuntimeAppConfig
from bijux_proteomics_runtime.api import create_app as runtime_create_app
from bijux_proteomics_runtime.api.errors import _ERROR_TYPES as RUNTIME_ERROR_TYPES
from bijux_proteomics.structure_report import Report as RuntimeReport
from bijux_proteomics.structure_report.render import (
    confidence_summary as runtime_confidence_summary,
)
from bijux_proteomics.structure_report.render import format_pct as runtime_format_pct
from bijux_proteomics.structure_report.render import nl_summary as runtime_nl_summary
from bijux_proteomics.structure_report.render import to_text as runtime_to_text
from bijux_proteomics_runtime.execution.evaluation.observations import (
    EvaluationInput as RuntimeEvaluationInput,
)
from bijux_proteomics_runtime.api.cli import (
    _artifact_hashes as runtime_artifact_hashes,
)
from bijux_proteomics_runtime.api.cli import (
    _artifact_paths as runtime_artifact_paths,
)
from bijux_proteomics_runtime.api.cli import (
    _build_run_config as runtime_build_run_config,
)
from bijux_proteomics_runtime.api.cli import (
    _emit_json_payload as runtime_emit_json_payload,
)
from bijux_proteomics_runtime.api.cli import (
    _emit_run_summary_human as runtime_emit_run_summary_human,
)
from bijux_proteomics_runtime.api.cli import (
    _export_report_payload as runtime_export_report_payload,
)
from bijux_proteomics_runtime.api.cli import (
    _load_run_config as runtime_load_run_config,
)
from bijux_proteomics_runtime.api.cli import (
    _load_run_summary as runtime_load_run_summary,
)
from bijux_proteomics_runtime.api.cli import (
    _read_sequence as runtime_read_sequence,
)
from bijux_proteomics_runtime.api.cli import (
    _resume_candidate as runtime_resume_candidate,
)
from bijux_proteomics_runtime.api.cli import (
    _write_output as runtime_write_output,
)
from bijux_proteomics_runtime.api.cli import (
    cli as runtime_cli,
)
from bijux_proteomics_runtime.providers.contracts import _time_left as runtime_time_left
from bijux_proteomics_runtime.providers.selection import (
    _require_module as runtime_require_module,
)
from bijux_proteomics_runtime.execution.agents.catalog import AgentCatalog as RuntimeAgentCatalog
from bijux_proteomics_runtime.execution.tools.catalog import (
    ToolCatalog as RuntimeToolCatalog,
)
from bijux_proteomics_runtime.runs.artifacts import (
    _sign_payload as runtime_sign_payload,
)
from bijux_proteomics_runtime.runs.manager import (
    _build_run_summary as runtime_build_run_summary,
)
from bijux_proteomics_runtime.runs.manager import (
    _ensure_telemetry_costs as runtime_ensure_telemetry_costs,
)
from bijux_proteomics_runtime.runs.manager import (
    _select_structure_tool as runtime_select_structure_tool,
)
from bijux_proteomics_runtime.runs.manager import (
    _version_info as runtime_version_info,
)
from bijux_proteomics_runtime.providers import capabilities as runtime_capabilities
from bijux_proteomics_runtime.providers.capabilities import (
    KNOWN_PROVIDERS as RUNTIME_KNOWN_PROVIDERS,
)
from bijux_proteomics_runtime.providers.capabilities import (
    validate_runtime_capabilities as runtime_validate_runtime_capabilities,
)
from bijux_proteomics_runtime.execution.agents.contracts import (
    _minimal_payload as runtime_minimal_payload,
)
from bijux_proteomics_runtime.execution.agents.contracts import (
    _placeholder_for_type as runtime_placeholder_for_type,
)


def _config_payload(config: object) -> dict[str, object]:
    if is_dataclass(config):
        return cast(dict[str, object], asdict(cast(Any, config)))
    if hasattr(config, "model_dump"):
        return cast(dict[str, object], cast(Any, config).model_dump())
    if hasattr(config, "dict"):
        return cast(dict[str, object], cast(Any, config).dict())
    raise TypeError(f"Unsupported config model type: {type(config)!r}")


def test_compat_cli_import_forwards_to_runtime_symbol() -> None:
    assert compat_cli is runtime_cli


def test_compat_and_runtime_cli_help_are_equivalent() -> None:
    compat_result = CliRunner().invoke(compat_cli, ["--help"])
    runtime_result = CliRunner().invoke(runtime_cli, ["--help"])
    assert compat_result.exit_code == 0
    assert runtime_result.exit_code == 0
    assert compat_result.output == runtime_result.output


def test_compat_and_runtime_api_factory_are_equivalent() -> None:
    base_dir = Path.cwd()
    compat_config = CompatAppConfig(base_dir=base_dir, docs_enabled=False)
    runtime_config = RuntimeAppConfig(base_dir=base_dir, docs_enabled=False)
    assert _config_payload(compat_config) == _config_payload(runtime_config)

    compat_app = compat_create_app(compat_config)
    runtime_app = runtime_create_app(runtime_config)
    assert compat_app.title == runtime_app.title
    assert [getattr(route, "path", "") for route in compat_app.routes] == [
        getattr(route, "path", "") for route in runtime_app.routes
    ]


def test_compat_evaluation_observations_forward_to_runtime_symbols() -> None:
    assert CompatEvaluationInput is RuntimeEvaluationInput


def test_compat_api_error_contracts_forward_to_runtime_symbols() -> None:
    assert COMPAT_ERROR_TYPES is RUNTIME_ERROR_TYPES


def test_compat_report_surface_forwards_to_core_symbols() -> None:
    assert CompatReport is RuntimeReport
    assert compat_nl_summary is runtime_nl_summary
    assert compat_confidence_summary is runtime_confidence_summary
    assert compat_format_pct is runtime_format_pct
    assert compat_to_text is runtime_to_text


def test_compat_cli_input_helpers_forward_to_runtime_symbols() -> None:
    assert compat_read_sequence is runtime_read_sequence
    assert compat_build_run_config is runtime_build_run_config
    assert compat_resume_candidate is runtime_resume_candidate


def test_compat_cli_artifact_helpers_forward_to_runtime_symbols() -> None:
    assert compat_export_report_payload is runtime_export_report_payload
    assert compat_write_output is runtime_write_output
    assert compat_artifact_paths is runtime_artifact_paths
    assert compat_emit_json_payload is runtime_emit_json_payload
    assert compat_load_run_summary is runtime_load_run_summary
    assert compat_load_run_config is runtime_load_run_config
    assert compat_emit_run_summary_human is runtime_emit_run_summary_human
    assert compat_artifact_hashes is runtime_artifact_hashes


def test_compat_provider_deadline_helper_forwards_to_runtime_symbol() -> None:
    assert compat_time_left is runtime_time_left


def test_compat_provider_dependency_helper_forwards_to_runtime_symbol() -> None:
    assert compat_require_module is runtime_require_module


def test_compat_catalog_surface_forwards_to_runtime_symbols() -> None:
    assert CompatAgentCatalog is RuntimeAgentCatalog
    assert CompatAgentRegistry is RuntimeAgentCatalog
    assert CompatToolCatalog is RuntimeToolCatalog
    assert CompatToolRegistry is RuntimeToolCatalog


def test_compat_artifact_signature_helper_forwards_to_runtime_symbol() -> None:
    assert compat_sign_payload is runtime_sign_payload


def test_compat_execution_summary_helpers_forward_to_runtime_symbols() -> None:
    assert compat_build_run_summary is runtime_build_run_summary
    assert compat_version_info is runtime_version_info


def test_compat_execution_runtime_helpers_forward_to_runtime_symbols() -> None:
    assert compat_select_structure_tool is runtime_select_structure_tool
    assert compat_ensure_telemetry_costs is runtime_ensure_telemetry_costs


def test_compat_validation_payload_helpers_forward_to_runtime_symbols() -> None:
    assert compat_minimal_payload is runtime_minimal_payload
    assert compat_placeholder_for_type is runtime_placeholder_for_type


def test_compat_runtime_capability_surface_forwards_to_runtime_symbols() -> None:
    assert (
        compat_capabilities.PROVIDER_CAPABILITIES
        is runtime_capabilities.PROVIDER_CAPABILITIES
    )
    assert compat_capabilities.provider_requirements is runtime_capabilities.provider_requirements
    assert COMPAT_KNOWN_PROVIDERS is RUNTIME_KNOWN_PROVIDERS
    assert compat_validate_runtime_capabilities is runtime_validate_runtime_capabilities
