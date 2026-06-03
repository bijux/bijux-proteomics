# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search adapter CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.search_adapter import run_search_adapter_inspect_command, run_search_adapter_params_command, run_search_adapter_validate_config_command, run_search_adapter_normalize_command, run_search_adapter_compare_command, run_search_adapter_conformance_command

@click.command("inspect")
@click.option("--adapter", "adapter_name", type=_search_adapter_choice(), default=None)
def search_adapter_inspect_command(adapter_name: str | None) -> None:
    'Inspect one adapter manifest or the full capability matrix.'
    return run_search_adapter_inspect_command(adapter_name)

@click.command("params")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_params_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    'Parse one supported search-engine parameter file.'
    return run_search_adapter_params_command(adapter_name, config_path, out_path)

@click.command("validate-config")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "config_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_validate_config_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    'Validate one supported search-engine parameter file.'
    return run_search_adapter_validate_config_command(adapter_name, config_path, out_path)

@click.command("normalize")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--adapter-version", default=None)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON normalization output path.",
)
def search_adapter_normalize_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    adapter_version: str | None,
    config_path: Path | None,
    jsonl_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    'Normalize one engine-specific search-result table into stable PSM records.'
    return run_search_adapter_normalize_command(adapter_name, input_path, mapping_json, adapter_version, config_path, jsonl_out, provenance_out, out_path)

@click.command("compare")
@click.argument("left_adapter_name", type=_search_adapter_choice())
@click.argument(
    "left_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("right_adapter_name", type=_search_adapter_choice())
@click.argument(
    "right_input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--left-mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--right-mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_compare_command(
    left_adapter_name: str,
    left_input_path: Path,
    right_adapter_name: str,
    right_input_path: Path,
    left_mapping_json: Path | None,
    right_mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    'Compare two normalized adapter outputs on a shared score scale.'
    return run_search_adapter_compare_command(left_adapter_name, left_input_path, right_adapter_name, right_input_path, left_mapping_json, right_mapping_json, out_path)

@click.command("conformance")
@click.argument("adapter_name", type=_search_adapter_choice())
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mapping-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def search_adapter_conformance_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    'Run the built-in adapter conformance checks on one search-result table.'
    return run_search_adapter_conformance_command(adapter_name, input_path, mapping_json, out_path)

COMMANDS = (
    search_adapter_inspect_command,
    search_adapter_params_command,
    search_adapter_validate_config_command,
    search_adapter_normalize_command,
    search_adapter_compare_command,
    search_adapter_conformance_command,
)
