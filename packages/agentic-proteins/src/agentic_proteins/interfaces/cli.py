"""Compatibility forwarding module for canonical runtime interface ownership."""

from bijux_proteomics_runtime.interfaces import cli as _runtime_cli
from bijux_proteomics_runtime.interfaces.cli import *  # noqa: F401,F403

_export_report_payload = _runtime_cli._export_report_payload
_write_output = _runtime_cli._write_output
_artifact_paths = _runtime_cli._artifact_paths
_emit_json_payload = _runtime_cli._emit_json_payload
_load_run_summary = _runtime_cli._load_run_summary
_load_run_config = _runtime_cli._load_run_config
_emit_run_summary_human = _runtime_cli._emit_run_summary_human
_artifact_hashes = _runtime_cli._artifact_hashes
