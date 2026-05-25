# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search import and FragPipe benchmark CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("psm-contaminants")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--contaminant-prefix",
    "contaminant_prefixes",
    multiple=True,
    default=("CON__",),
    show_default=True,
    help="Protein-reference prefixes that mark contaminant evidence.",
)
@click.option("--run-id-column", default=None)
@click.option("--intensity-column", default=None)
@click.option(
    "--burden-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON contaminant-match report output path.",
)
def psm_contaminants_command(
    input_tsv: Path,
    contaminant_prefixes: tuple[str, ...],
    run_id_column: str | None,
    intensity_column: str | None,
    burden_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Separate contaminant-carrying peptide-spectrum matches from target-only evidence.'
    return run_psm_contaminants_command(input_tsv, contaminant_prefixes, run_id_column, intensity_column, burden_tsv_out, protein_tsv_out, out_path)

def run_psm_contaminants_command(
    input_tsv: Path,
    contaminant_prefixes: tuple[str, ...],
    run_id_column: str | None,
    intensity_column: str | None,
    burden_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    report = parse_psm_tsv(
        input_tsv,
        mapping=_build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column="spectrum_id",
            peptide_column="peptide",
            modified_peptide_column=None,
            charge_column="charge",
            score_column="score",
            q_value_column="q_value",
            protein_refs_column="proteins",
            decoy_label_column=None,
            contaminant_label_column=None,
            protein_separator=";",
            intensity_column=intensity_column,
        ),
    )
    contaminant_report = build_contaminant_peptide_match_report(
        report.accepted_records,
        contaminant_prefixes=tuple(contaminant_prefixes),
    )
    contaminant_evidence = build_contaminant_evidence_report(
        report.accepted_records,
        contaminant_prefixes=tuple(contaminant_prefixes),
    )
    if burden_tsv_out is not None:
        _write_text_output(
            burden_tsv_out,
            render_contaminant_burden_tsv(contaminant_evidence),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_contaminant_proteins_tsv(contaminant_evidence),
        )
    _emit_json(
        {
            **contaminant_report.to_dict(),
            "contaminant_evidence": contaminant_evidence.to_dict(),
        },
        out_path=out_path,
    )

@click.command("fragpipe-import")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--quant-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--peptide-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-review-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--open-search-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-quantity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_import_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    quant_tsv: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    peptide_review_tsv_out: Path | None,
    protein_review_tsv_out: Path | None,
    open_search_tsv_out: Path | None,
    protein_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one FragPipe result bundle with explicit PSM, peptide, and protein review.'
    return run_fragpipe_import_command(psm_tsv, peptide_tsv, protein_tsv, quant_tsv, summary_tsv_out, canonical_psm_tsv_out, psm_tsv_out, peptide_review_tsv_out, protein_review_tsv_out, open_search_tsv_out, protein_quantity_tsv_out, rejected_tsv_out, out_path)

def run_fragpipe_import_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    quant_tsv: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    peptide_review_tsv_out: Path | None,
    protein_review_tsv_out: Path | None,
    open_search_tsv_out: Path | None,
    protein_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_fragpipe_import_report(
            psm_tsv,
            peptide_tsv_path=peptide_tsv,
            protein_tsv_path=protein_tsv,
            quant_tsv_path=quant_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_fragpipe_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_fragpipe_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_fragpipe_psm_tsv(report.psm_rows))
    if peptide_review_tsv_out is not None:
        _write_text_output(
            peptide_review_tsv_out,
            render_fragpipe_peptide_tsv(report.peptide_rows),
        )
    if protein_review_tsv_out is not None:
        _write_text_output(
            protein_review_tsv_out,
            render_fragpipe_protein_tsv(report.protein_rows),
        )
    if open_search_tsv_out is not None:
        _write_text_output(
            open_search_tsv_out,
            render_fragpipe_open_search_evidence_tsv(report.open_search_evidence),
        )
    if protein_quantity_tsv_out is not None:
        _write_text_output(
            protein_quantity_tsv_out,
            render_fragpipe_protein_quantity_tsv(report.protein_quantity_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "psm_normalization": {
            "adapter": report.psm_normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(
                report.psm_normalization.parse_report.accepted_records
            ),
            "rejected_rows": len(report.psm_normalization.parse_report.rejected_rows),
        },
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "peptide_rows": [row.to_dict() for row in report.peptide_rows],
        "protein_rows": [row.to_dict() for row in report.protein_rows],
        "open_search_evidence": [row.to_dict() for row in report.open_search_evidence],
        "protein_quantity_rows": [row.to_dict() for row in report.protein_quantity_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "peptide_review_tsv": None
            if peptide_review_tsv_out is None
            else str(peptide_review_tsv_out),
            "protein_review_tsv": None
            if protein_review_tsv_out is None
            else str(protein_review_tsv_out),
            "open_search_tsv": None
            if open_search_tsv_out is None
            else str(open_search_tsv_out),
            "protein_quantity_tsv": None
            if protein_quantity_tsv_out is None
            else str(protein_quantity_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

@click.command("fragpipe-benchmark")
@click.argument("psm_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--peptide-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--protein-tsv",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--count-comparisons-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-groups-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--psm-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--peptide-qvalues-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def fragpipe_benchmark_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_groups_tsv_out: Path | None,
    psm_qvalues_tsv_out: Path | None,
    peptide_qvalues_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Benchmark governed FragPipe import behavior against the source FragPipe bundle.'
    return run_fragpipe_benchmark_command(psm_tsv, peptide_tsv, protein_tsv, summary_tsv_out, count_comparisons_tsv_out, protein_groups_tsv_out, psm_qvalues_tsv_out, peptide_qvalues_tsv_out, out_path)

def run_fragpipe_benchmark_command(
    psm_tsv: Path,
    peptide_tsv: Path,
    protein_tsv: Path,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_groups_tsv_out: Path | None,
    psm_qvalues_tsv_out: Path | None,
    peptide_qvalues_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_fragpipe_import_benchmark_report(
            psm_tsv,
            peptide_tsv_path=peptide_tsv,
            protein_tsv_path=protein_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_fragpipe_benchmark_summary_tsv(report),
        )
    if count_comparisons_tsv_out is not None:
        _write_text_output(
            count_comparisons_tsv_out,
            render_fragpipe_count_comparisons_tsv(report),
        )
    if protein_groups_tsv_out is not None:
        _write_text_output(
            protein_groups_tsv_out,
            render_fragpipe_protein_group_comparison_tsv(report),
        )
    if psm_qvalues_tsv_out is not None:
        _write_text_output(
            psm_qvalues_tsv_out,
            render_fragpipe_q_value_comparison_tsv(report.q_value_behavior.psm_entries),
        )
    if peptide_qvalues_tsv_out is not None:
        _write_text_output(
            peptide_qvalues_tsv_out,
            render_fragpipe_q_value_comparison_tsv(
                report.q_value_behavior.peptide_entries
            ),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "protein_group_comparison": report.protein_group_comparison.to_dict(),
        "q_value_behavior": report.q_value_behavior.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "count_comparisons_tsv": None
            if count_comparisons_tsv_out is None
            else str(count_comparisons_tsv_out),
            "protein_groups_tsv": None
            if protein_groups_tsv_out is None
            else str(protein_groups_tsv_out),
            "psm_qvalues_tsv": None
            if psm_qvalues_tsv_out is None
            else str(psm_qvalues_tsv_out),
            "peptide_qvalues_tsv": None
            if peptide_qvalues_tsv_out is None
            else str(peptide_qvalues_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

@click.command("sage-import")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--canonical-psm-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--psm-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--rejected-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def sage_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Import one Sage result table with explicit score, q-value, and modification review.'
    return run_sage_import_command(result_tsv, config_path, summary_tsv_out, canonical_psm_tsv_out, psm_tsv_out, rejected_tsv_out, out_path)

def run_sage_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_sage_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_sage_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_sage_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_sage_psm_tsv(report.psm_rows))
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "dialect_id": report.dialect_id,
        "summary": report.summary.to_dict(),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "rejected_tsv": None
            if rejected_tsv_out is None
            else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    psm_contaminants_command,
    fragpipe_import_command,
    fragpipe_benchmark_command,
    sage_import_command,
)
