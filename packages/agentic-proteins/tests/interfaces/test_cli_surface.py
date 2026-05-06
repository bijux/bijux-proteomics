# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib

from click.testing import CliRunner

from agentic_proteins.interfaces.cli import cli as compat_cli
from bijux_proteomics_runtime.api.cli import cli as runtime_cli

compat_cli_module = importlib.import_module("agentic_proteins.interfaces.cli")
runtime_cli_module = importlib.import_module("bijux_proteomics_runtime.api.cli")


def test_cli_help_matches_runtime_help() -> None:
    compat_result = CliRunner().invoke(compat_cli, ["--help"])
    runtime_result = CliRunner().invoke(runtime_cli, ["--help"])
    assert compat_result.exit_code == 0
    assert runtime_result.exit_code == 0
    assert compat_result.output == runtime_result.output


def test_cli_helper_exports_forward_to_runtime_module() -> None:
    helper_names = (
        "CliResult",
        "_artifact_hashes",
        "_artifact_paths",
        "_build_run_config",
        "_emit_json_payload",
        "_emit_run_summary_human",
        "_export_report_payload",
        "_load_run_config",
        "_load_run_summary",
        "_read_sequence",
        "_resume_candidate",
        "_write_output",
    )
    for name in helper_names:
        assert getattr(compat_cli_module, name) is getattr(runtime_cli_module, name)
