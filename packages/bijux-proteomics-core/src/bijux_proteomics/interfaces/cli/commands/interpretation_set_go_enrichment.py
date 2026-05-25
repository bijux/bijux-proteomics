# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation set and GO enrichment CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("protein-set-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_set_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--background-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--missing-background-policy",
    type=click.Choice(
        [policy.value for policy in ProteinSetEnrichmentMissingBackgroundPolicy]
    ),
    default=ProteinSetEnrichmentMissingBackgroundPolicy.REJECT.value,
    show_default=True,
)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--result-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--universe-gap-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-set-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def protein_set_enrichment_command(
    foreground_tsv: Path,
    protein_set_tsv: Path,
    background_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    missing_background_policy: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    result_tsv_out: Path | None,
    universe_gap_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run generic enrichment over compartment and custom protein-set definitions.'
    return run_protein_set_enrichment_command(foreground_tsv, protein_set_tsv, background_tsv, protein_ref_column, row_id_column, protein_separator, set_id_column, set_name_column, set_category_column, source_name_column, source_accession_column, set_protein_ref_column, missing_background_policy, max_adjusted_p_value, min_enrichment_ratio, summary_tsv_out, result_tsv_out, universe_gap_tsv_out, rejected_set_tsv_out, out_path)

def run_protein_set_enrichment_command(
    foreground_tsv: Path,
    protein_set_tsv: Path,
    background_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    missing_background_policy: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    result_tsv_out: Path | None,
    universe_gap_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = (
            None
            if background_tsv is None
            else parse_protein_reference_table(
                background_tsv,
                mapping=ProteinReferenceColumnMapping(
                    protein_ref=protein_ref_column,
                    row_id=row_id_column,
                ),
                protein_separator=protein_separator,
            )
        )
        protein_sets = parse_protein_set_table(
            protein_set_tsv,
            mapping=ProteinSetColumnMapping(
                set_id=set_id_column,
                protein_ref=set_protein_ref_column,
                set_name=set_name_column,
                set_category=set_category_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
            ),
        )
        report = build_protein_set_enrichment_report(
            foreground.accepted_entries,
            protein_sets.accepted_records,
            background_entries=(
                None if background is None else background.accepted_entries
            ),
            policy=ProteinSetEnrichmentPolicy(
                missing_background_policy=ProteinSetEnrichmentMissingBackgroundPolicy(
                    missing_background_policy
                ),
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_protein_set_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if result_tsv_out is not None:
        result_tsv_out.write_text(
            render_protein_set_enrichment_tsv(report),
            encoding="utf-8",
        )
    if universe_gap_tsv_out is not None:
        universe_gap_tsv_out.write_text(
            render_protein_set_universe_gap_tsv(report),
            encoding="utf-8",
        )
    if rejected_set_tsv_out is not None:
        rejected_set_tsv_out.write_text(
            render_rejected_protein_set_membership_tsv(protein_sets),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": None if background is None else background.to_dict(),
        "protein_sets": protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "result_tsv": None if result_tsv_out is None else str(result_tsv_out),
            "universe_gap_tsv": (
                None
                if universe_gap_tsv_out is None
                else str(universe_gap_tsv_out)
            ),
            "rejected_set_tsv": (
                None
                if rejected_set_tsv_out is None
                else str(rejected_set_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

@click.command("go-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "go_annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--go-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--go-term-id-column", default="go_term_id", show_default=True)
@click.option("--go-term-name-column", default="go_term_name", show_default=True)
@click.option("--go-aspect-column", default="go_aspect", show_default=True)
@click.option("--evidence-code-column", default="evidence_code", show_default=True)
@click.option(
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unannotated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def go_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    go_annotation_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    go_protein_ref_column: str,
    go_term_id_column: str,
    go_term_name_column: str,
    go_aspect_column: str,
    evidence_code_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unannotated_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run GO term enrichment over foreground and background protein sets.'
    return run_go_enrichment_command(foreground_tsv, background_tsv, go_annotation_tsv, protein_ref_column, row_id_column, protein_separator, go_protein_ref_column, go_term_id_column, go_term_name_column, go_aspect_column, evidence_code_column, max_adjusted_p_value, min_enrichment_ratio, summary_tsv_out, term_tsv_out, unannotated_tsv_out, rejected_annotation_tsv_out, out_path)

def run_go_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    go_annotation_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    go_protein_ref_column: str,
    go_term_id_column: str,
    go_term_name_column: str,
    go_aspect_column: str,
    evidence_code_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unannotated_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        annotations = parse_go_annotation_table(
            go_annotation_tsv,
            mapping=GoAnnotationColumnMapping(
                protein_ref=go_protein_ref_column,
                go_term_id=go_term_id_column,
                go_term_name=go_term_name_column,
                go_aspect=go_aspect_column,
                evidence_code=evidence_code_column,
            ),
        )
        report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                annotations.accepted_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_go_enrichment_summary_tsv(report),
            encoding="utf-8",
        )
    if term_tsv_out is not None:
        term_tsv_out.write_text(
            render_go_enrichment_term_tsv(report),
            encoding="utf-8",
        )
    if unannotated_tsv_out is not None:
        unannotated_tsv_out.write_text(
            render_go_enrichment_unannotated_tsv(report),
            encoding="utf-8",
        )
    if rejected_annotation_tsv_out is not None:
        rejected_annotation_tsv_out.write_text(
            render_rejected_go_annotation_tsv(annotations),
            encoding="utf-8",
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "go_annotations": annotations.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "term_tsv": None if term_tsv_out is None else str(term_tsv_out),
            "unannotated_tsv": (
                None if unannotated_tsv_out is None else str(unannotated_tsv_out)
            ),
            "rejected_annotation_tsv": (
                None
                if rejected_annotation_tsv_out is None
                else str(rejected_annotation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    protein_set_enrichment_command,
    go_enrichment_command,
)
