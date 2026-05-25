# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search adapter CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("inspect")
@click.option("--adapter", "adapter_name", type=_search_adapter_choice(), default=None)
def search_adapter_inspect_command(adapter_name: str | None) -> None:
    'Inspect one adapter manifest or the full capability matrix.'
    return run_search_adapter_inspect_command(adapter_name)

def run_search_adapter_inspect_command(adapter_name: str | None) -> None:
    if adapter_name is None:
        payload = {
            "capabilities": [
                row.to_dict() for row in build_search_adapter_capability_matrix()
            ],
        }
        _emit_json(payload)
        return
    manifest = get_search_adapter_manifest(SearchAdapterKind(adapter_name))
    _emit_json(manifest)

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

def run_search_adapter_params_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    try:
        payload = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)

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

def run_search_adapter_validate_config_command(
    adapter_name: str,
    config_path: Path,
    out_path: Path | None,
) -> None:
    try:
        parameters = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
        payload = validate_search_parameters(parameters)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)

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

def run_search_adapter_normalize_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    adapter_version: str | None,
    config_path: Path | None,
    jsonl_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    mapping = None
    if mapping_json is not None:
        mapping = SearchResultColumnMapping.model_validate_json(
            mapping_json.read_text()
        )
    try:
        report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        provenance = build_search_adapter_provenance_manifest(
            source_path=input_path,
            normalization_report=report,
            adapter_version=adapter_version,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    if jsonl_out is not None:
        export_psm_jsonl(report.normalized_records, jsonl_out)
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "adapter": report.adapter_manifest.to_dict(),
        "accepted_rows": len(report.parse_report.accepted_records),
        "rejected_rows": len(report.parse_report.rejected_rows),
        "normalized_records": [
            record.to_dict() for record in report.normalized_records
        ],
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)

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

def run_search_adapter_compare_command(
    left_adapter_name: str,
    left_input_path: Path,
    right_adapter_name: str,
    right_input_path: Path,
    left_mapping_json: Path | None,
    right_mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    left_mapping = (
        SearchResultColumnMapping.model_validate_json(left_mapping_json.read_text())
        if left_mapping_json is not None
        else None
    )
    right_mapping = (
        SearchResultColumnMapping.model_validate_json(right_mapping_json.read_text())
        if right_mapping_json is not None
        else None
    )
    try:
        left_report = normalize_search_results_with_adapter(
            source_path=left_input_path,
            adapter_kind=SearchAdapterKind(left_adapter_name),
            mapping=left_mapping,
        )
        right_report = normalize_search_results_with_adapter(
            source_path=right_input_path,
            adapter_kind=SearchAdapterKind(right_adapter_name),
            mapping=right_mapping,
        )
        payload = compare_search_result_reports(left_report, right_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)

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

def run_search_adapter_conformance_command(
    adapter_name: str,
    input_path: Path,
    mapping_json: Path | None,
    out_path: Path | None,
) -> None:
    mapping = (
        SearchResultColumnMapping.model_validate_json(mapping_json.read_text())
        if mapping_json is not None
        else None
    )
    try:
        normalization_report = normalize_search_results_with_adapter(
            source_path=input_path,
            adapter_kind=SearchAdapterKind(adapter_name),
            mapping=mapping,
        )
        payload = build_search_adapter_conformance_report(normalization_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    search_adapter_inspect_command,
    search_adapter_params_command,
    search_adapter_validate_config_command,
    search_adapter_normalize_command,
    search_adapter_compare_command,
    search_adapter_conformance_command,
)
