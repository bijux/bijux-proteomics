# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""CLI for Bijux Proteomics domain and FASTA operations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any

import click

from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    approximate_peptide_isotope_envelope,
    build_modification_localization_advisory,
    build_modified_peptide,
    build_peptide_charge_state,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
    load_modification_registry,
)
from bijux_proteomics.digestion import (
    PeptideDigestionMode,
    build_digest_manifest,
    digest_protein_records,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    get_protease_rule,
    peptide_export_fingerprint,
)
from bijux_proteomics.exceptions import (
    ProteomicsOperatorError,
    ProteomicsOperatorErrorCode,
)
from bijux_proteomics.formats import (
    ExperimentalDesignEntry,
    FormatConversionTarget,
    ProteomicsFormatKind,
    build_mzml_collection_summary,
    build_normalized_run_bundle,
    convert_proteomics_format,
    parse_experimental_design_table,
    parse_mzml,
    validate_proteomics_input,
)
from bijux_proteomics.identification import (
    FdrPolicy,
    SearchResultColumnMapping,
    TargetDecoyLabelPolicy,
    apply_q_values,
    assign_confidence_labels,
    assign_razor_peptides,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    build_peptide_summary_report,
    build_peptide_uniqueness_across_database,
    build_protein_coverage_map,
    build_protein_groups,
    build_protein_summary_report,
    build_psm_summary_report,
    build_search_result_provenance_manifest,
    calculate_grouped_fdr,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    export_psm_jsonl,
    export_psm_tsv,
    filter_psms_by_fdr,
    infer_proteins_by_parsimony,
    parse_psm_tsv,
)
from bijux_proteomics.programs import ProgramSpec, create_program_spec, program_summary
from bijux_proteomics.ptm import (
    PtmLocalizationColumnMapping,
    build_ptm_enrichment_input,
    build_ptm_motif_windows,
    build_ptm_site_ambiguity_report,
    build_ptm_site_coverage_report,
    build_ptm_site_fdr,
    build_ptm_site_table,
    estimate_ptm_site_occupancy,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.qc import (
    QcEvidenceInputFile,
    build_batch_qc_assessment,
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_qc_evidence_manifest,
    build_run_qc_assessment,
    default_qc_threshold_policy,
    load_qc_threshold_policy,
    render_qc_assessment_html,
    render_qc_assessment_tsv,
)
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_batch_effect_advisory,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_replicate_correlation_report,
    build_spectral_count_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
    summarize_missing_values,
)
from bijux_proteomics.search_adapters import (
    ScoreOrientation,
    SearchAdapterKind,
    build_search_adapter_capability_matrix,
    build_search_adapter_conformance_report,
    build_search_adapter_provenance_manifest,
    compare_search_result_reports,
    get_search_adapter_manifest,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
    validate_search_parameters,
)
from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    build_decoy_generation_manifest,
    FastaParseMode,
    FastaParseReport,
    build_fasta_provenance_manifest,
    build_fasta_stats,
    deduplicate_fasta_records,
    filter_fasta_records,
    generate_decoy_records,
    parse_fasta_document,
    render_fasta_records,
    sequence_checksum,
    validate_target_decoy_database,
)
from bijux_proteomics.spectra import (
    annotate_spectrum_fragments,
    build_spectrum_collection_summary,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    build_spectrum_provenance_manifest,
    export_spectrum_annotation_tsv,
    parse_mgf,
)
from bijux_proteomics.workflow_runtime import (
    WorkflowSchedulerKind,
    build_proteomics_workflow_runtime_bundle,
    build_workflow_runtime_validation_report,
)


def _emit_json(payload: Any, *, out_path: Path | None = None) -> None:
    if hasattr(payload, "to_stable_json"):
        rendered = payload.to_stable_json()
    else:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
    if out_path is not None:
        out_path.write_text(rendered + "\n")
    click.echo(rendered)


def _write_text_output(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_fasta_report(
    input_path: Path,
    *,
    mode: FastaParseMode,
    allow_rejected: bool,
) -> FastaParseReport:
    report = parse_fasta_document(input_path.read_text(), mode=mode)
    if report.rejected_records and not allow_rejected:
        rejected = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise click.ClickException(
            f"FASTA input contains rejected records under {mode.value} mode: {rejected}"
        )
    return report


def _mode_choice() -> click.Choice[str]:
    return click.Choice([mode.value for mode in FastaParseMode], case_sensitive=False)


def _decoy_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in DecoyGenerationMode],
        case_sensitive=False,
    )


def _digestion_mode_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideDigestionMode],
        case_sensitive=False,
    )


def _export_format_choice() -> click.Choice[str]:
    return click.Choice(["tsv", "jsonl", "parquet"], case_sensitive=False)


def _fragment_series_choice() -> click.Choice[str]:
    return click.Choice(
        [series.value for series in FragmentIonSeries], case_sensitive=False
    )


def _validate_kind_choice() -> click.Choice[str]:
    return click.Choice(
        ["auto", "fasta", "psm", "mgf", "mzml", "mod-registry", "design-table"],
        case_sensitive=False,
    )


def _conversion_target_choice() -> click.Choice[str]:
    return click.Choice(
        [target.value for target in FormatConversionTarget], case_sensitive=False
    )


def _search_adapter_choice() -> click.Choice[str]:
    return click.Choice(
        [adapter.value for adapter in SearchAdapterKind], case_sensitive=False
    )


def _score_orientation_choice() -> click.Choice[str]:
    return click.Choice(
        [orientation.value for orientation in ScoreOrientation], case_sensitive=False
    )


def _quant_entity_level_choice() -> click.Choice[str]:
    return click.Choice(
        [level.value for level in QuantEntityLevel], case_sensitive=False
    )


def _quant_measure_choice() -> click.Choice[str]:
    return click.Choice(
        [measure.value for measure in QuantMeasureKind], case_sensitive=False
    )


def _quant_rollup_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in QuantRollupMethod], case_sensitive=False
    )


def _normalization_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in NormalizationMethod], case_sensitive=False
    )


def _workflow_scheduler_choice() -> click.Choice[str]:
    return click.Choice(
        [scheduler.value for scheduler in WorkflowSchedulerKind], case_sensitive=False
    )


def _select_design_entry(
    design_path: Path | None,
    *,
    sample_id: str | None,
    spectra_path: Path,
) -> ExperimentalDesignEntry | None:
    if design_path is None:
        return None
    report = parse_experimental_design_table(design_path)
    if report.rejected_rows:
        raise ProteomicsOperatorError(
            ProteomicsOperatorErrorCode.INPUT_DESIGN_INVALID,
            "design table contains rejected rows",
        )
    if sample_id is not None:
        for entry in report.accepted_entries:
            if entry.sample_id == sample_id:
                return entry
        raise ProteomicsOperatorError(
            ProteomicsOperatorErrorCode.QC_SAMPLE_NOT_FOUND,
            f"sample {sample_id!r} is not present in the design table",
        )
    matching_entries = [
        entry
        for entry in report.accepted_entries
        if Path(entry.spectra_file).name == spectra_path.name
    ]
    if len(matching_entries) == 1:
        return matching_entries[0]
    if len(report.accepted_entries) == 1:
        return report.accepted_entries[0]
    raise ProteomicsOperatorError(
        ProteomicsOperatorErrorCode.QC_SAMPLE_NOT_FOUND,
        "design table requires --sample-id when multiple rows are present",
    )


def _build_psm_mapping(
    *,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
) -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id=spectrum_id_column,
        peptide=peptide_column,
        charge=charge_column,
        score=score_column,
        q_value=q_value_column,
        protein_refs=protein_refs_column,
        decoy_label=decoy_label_column,
        protein_separator=protein_separator,
    )


def _build_decoy_policy(
    *,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
) -> TargetDecoyLabelPolicy:
    return TargetDecoyLabelPolicy(
        protein_prefix=decoy_prefix,
        protein_suffix=decoy_suffix,
    )


def _default_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def _infer_input_kind(input_path: Path, explicit_kind: str) -> str:
    if explicit_kind != "auto":
        return explicit_kind
    suffix = input_path.suffix.lower()
    if suffix in {".fasta", ".fa", ".faa"}:
        return "fasta"
    if suffix == ".mgf":
        return "mgf"
    if suffix == ".mzml":
        return "mzml"
    if input_path.name.endswith(".design.tsv") or input_path.name.endswith(
        ".design.csv"
    ):
        return "design-table"
    if suffix == ".tsv":
        return "psm"
    if suffix == ".json":
        return "mod-registry"
    raise click.ClickException(
        f"cannot infer input kind for {input_path.name!r}; use --kind fasta, psm, mgf, mzml, design-table, or mod-registry"
    )


@click.group()
def cli() -> None:
    """Manage program manifests and protein-sequence operations."""


@cli.command("program-template")
@click.option("--program-id", required=True, help="Stable program identifier.")
@click.option("--name", required=True, help="Program name.")
@click.option("--objective", required=True, help="Scientific objective.")
@click.option("--target-id", required=True, help="Stable target identifier.")
@click.option("--target-name", required=True, help="Target name.")
@click.option("--sequence", required=True, help="Reference amino-acid sequence.")
@click.option("--organism", required=True, help="Source organism.")
@click.option("--mechanism", required=True, help="Working target hypothesis.")
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the JSON document.",
)
def program_template(
    program_id: str,
    name: str,
    objective: str,
    target_id: str,
    target_name: str,
    sequence: str,
    organism: str,
    mechanism: str,
    out_path: Path,
) -> None:
    """Write a starter program manifest."""
    program = create_program_spec(
        program_id=program_id,
        name=name,
        objective=objective,
        target_id=target_id,
        target_name=target_name,
        sequence=sequence,
        organism=organism,
        mechanism=mechanism,
    )
    program.save_json(out_path)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("summarize-program")
@click.argument("program_file", type=click.Path(exists=True, path_type=Path))
def summarize_program(program_file: Path) -> None:
    """Print a compact summary for a program document."""
    program = ProgramSpec.load_json(program_file)
    click.echo(json.dumps(program_summary(program), sort_keys=True))


@cli.command("sequence-checksum")
@click.option(
    "--sequence", required=True, help="Protein sequence to normalize and hash."
)
def sequence_checksum_command(sequence: str) -> None:
    """Emit the normalized sequence checksum for one protein sequence string."""
    normalized = "".join(
        character for character in sequence.upper() if not character.isspace()
    )
    _emit_json(
        {
            "normalized_sequence": normalized,
            "residue_count": len(normalized),
            "sequence_checksum": sequence_checksum(sequence),
        }
    )


@cli.command("fasta-parse")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_parse_command(input_fasta: Path, mode: str, out_path: Path | None) -> None:
    """Parse FASTA input and emit normalized acceptance and rejection details."""
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode(mode))
    _emit_json(report, out_path=out_path)


@cli.command("fasta-dedup")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the deduplicated FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_dedup_command(
    input_fasta: Path,
    mode: str,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Deduplicate FASTA records by accession and normalized sequence digest."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    deduplicated, dedup_report = deduplicate_fasta_records(report.accepted_records)
    out_fasta.write_text(render_fasta_records(deduplicated))
    _emit_json(dedup_report, out_path=report_out)


@cli.command("fasta-filter")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=None)
@click.option("--max-length", type=int, default=None)
@click.option(
    "--accession-pattern",
    default=None,
    help="Regular expression over canonical accession.",
)
@click.option(
    "--organism", default=None, help="Exact organism filter, case-insensitive."
)
@click.option("--exclude-contaminants", is_flag=True, default=False)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the filtered FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_filter_command(
    input_fasta: Path,
    mode: str,
    min_length: int | None,
    max_length: int | None,
    accession_pattern: str | None,
    organism: str | None,
    exclude_contaminants: bool,
    out_fasta: Path,
    report_out: Path | None,
) -> None:
    """Filter FASTA records while emitting explicit exclusion counts."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    filtered, filter_report = filter_fasta_records(
        report.accepted_records,
        min_length=min_length,
        max_length=max_length,
        accession_pattern=accession_pattern,
        organism=organism,
        exclude_contaminants=exclude_contaminants,
    )
    out_fasta.write_text(render_fasta_records(filtered))
    _emit_json(filter_report, out_path=report_out)


@cli.command("fasta-stats")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def fasta_stats_command(input_fasta: Path, mode: str, out_path: Path | None) -> None:
    """Report FASTA record, residue, duplication, and contaminant metrics."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=True,
    )
    stats = build_fasta_stats(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )
    _emit_json(stats, out_path=out_path)


@cli.command("fasta-provenance")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--operation", default="fasta-parse", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the provenance manifest JSON.",
)
def fasta_provenance_command(
    input_fasta: Path,
    mode: str,
    operation: str,
    out_path: Path,
) -> None:
    """Write a provenance manifest for one FASTA processing step."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=True,
    )
    manifest = build_fasta_provenance_manifest(
        operation=operation,
        source_path=input_fasta,
        parse_mode=FastaParseMode(mode),
        input_record_count=report.total_records,
        accepted_record_count=len(report.accepted_records),
        rejected_record_count=len(report.rejected_records),
        output_record_count=len(report.accepted_records),
        parameters={"operation": operation},
    )
    _emit_json(manifest, out_path=out_path)


@cli.command("fasta-decoy")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--decoy-mode",
    type=_decoy_mode_choice(),
    default=DecoyGenerationMode.REVERSE.value,
    show_default=True,
)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option("--seed", type=int, default=17, show_default=True)
@click.option(
    "--decoys-only",
    is_flag=True,
    default=False,
    help="Write only decoy records instead of target+decoy output.",
)
@click.option(
    "--out-fasta",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the generated target/decoy FASTA.",
)
@click.option(
    "--report-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation report output path.",
)
@click.option(
    "--manifest-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON manifest output path.",
)
def fasta_decoy_command(
    input_fasta: Path,
    mode: str,
    decoy_mode: str,
    prefix: str,
    seed: int,
    decoys_only: bool,
    out_fasta: Path,
    report_out: Path | None,
    manifest_out: Path | None,
) -> None:
    """Generate target/decoy FASTA output and validate the result."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
    )
    output_records = decoys if decoys_only else (*report.accepted_records, *decoys)
    out_fasta.write_text(render_fasta_records(tuple(output_records)))
    manifest = build_decoy_generation_manifest(
        input_records=report.accepted_records,
        output_records=tuple(output_records),
        mode=DecoyGenerationMode(decoy_mode),
        prefix=prefix,
        seed=seed,
        source_path=input_fasta,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")
    validation = validate_target_decoy_database(tuple(output_records), prefix=prefix)
    payload = validation.to_dict()
    payload["reproducibility_hash"] = manifest.reproducibility_hash
    payload["output_sha256"] = manifest.output_sha256
    _emit_json(payload, out_path=report_out)


@cli.command("target-decoy-validate")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--prefix", default="DECOY_", show_default=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def target_decoy_validate_command(
    input_fasta: Path,
    mode: str,
    prefix: str,
    out_path: Path | None,
) -> None:
    """Validate target/decoy pairing completeness for a FASTA collection."""
    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    validation = validate_target_decoy_database(report.accepted_records, prefix=prefix)
    _emit_json(validation, out_path=out_path)


@cli.command("digest")
@click.argument(
    "input_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option("--protease", default="trypsin", show_default=True)
@click.option("--missed-cleavages", type=int, default=0, show_default=True)
@click.option(
    "--digestion-mode",
    type=_digestion_mode_choice(),
    default=PeptideDigestionMode.FULL.value,
    show_default=True,
)
@click.option("--min-length", type=int, default=1, show_default=True)
@click.option("--max-length", type=int, default=None)
@click.option("--min-mass", type=float, default=None)
@click.option("--max-mass", type=float, default=None)
@click.option(
    "--format",
    "export_format",
    type=_export_format_choice(),
    default="tsv",
    show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), required=True
)
@click.option(
    "--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def digest_command(
    input_fasta: Path,
    mode: str,
    protease: str,
    missed_cleavages: int,
    digestion_mode: str,
    min_length: int,
    max_length: int | None,
    min_mass: float | None,
    max_mass: float | None,
    export_format: str,
    out_path: Path,
    manifest_out: Path | None,
) -> None:
    """Digest FASTA records into peptide exports."""
    try:
        protease_rule = get_protease_rule(protease)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    report = _load_fasta_report(
        input_fasta,
        mode=FastaParseMode(mode),
        allow_rejected=False,
    )
    peptides = digest_protein_records(
        report.accepted_records,
        protease=protease_rule,
        missed_cleavages=missed_cleavages,
        mode=PeptideDigestionMode(digestion_mode),
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
    )

    try:
        if export_format == "tsv":
            export_peptides_tsv(peptides, out_path)
        elif export_format == "jsonl":
            export_peptides_jsonl(peptides, out_path)
        else:
            export_peptides_parquet(peptides, out_path)
    except (RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    manifest = build_digest_manifest(
        peptides=peptides,
        protease=protease_rule.name,
        digestion_mode=PeptideDigestionMode(digestion_mode),
        missed_cleavages=missed_cleavages,
        min_length=min_length,
        max_length=max_length,
        min_mass=min_mass,
        max_mass=max_mass,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )
    if manifest_out is not None:
        manifest_out.write_text(manifest.to_stable_json() + "\n")

    _emit_json(
        {
            "input_record_count": report.total_records,
            "output_peptide_count": len(peptides),
            "protease": protease_rule.name,
            "digestion_mode": digestion_mode,
            "policy_hash": manifest.policy_hash,
            "export_format": export_format,
            "output_sha256": peptide_export_fingerprint(peptides),
            "output_path": str(out_path),
        }
    )


@cli.command("peptide-mass")
@click.argument("sequence")
@click.option(
    "--mod",
    "modifications",
    multiple=True,
    help="Modification assignment like Oxidation@3 or Acetyl@n-term.",
)
@click.option("--charge", type=int, default=2, show_default=True)
@click.option(
    "--fragment-series",
    multiple=True,
    type=_fragment_series_choice(),
    default=("b", "y"),
    show_default=True,
)
@click.option("--include-neutral-losses", is_flag=True, default=False)
@click.option("--isotope-peaks", type=int, default=4, show_default=True)
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional JSON modification registry path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def peptide_mass_command(
    sequence: str,
    modifications: tuple[str, ...],
    charge: int,
    fragment_series: tuple[str, ...],
    include_neutral_losses: bool,
    isotope_peaks: int,
    registry_path: Path | None,
    out_path: Path | None,
) -> None:
    """Emit peptide chemistry diagnostics for one sequence plus optional modifications."""
    try:
        registry = (
            load_modification_registry(registry_path)
            if registry_path is not None
            else None
        )
        peptide = build_modified_peptide(
            sequence,
            assignments=tuple(modifications),
            registry=registry,
        )
        charge_state = build_peptide_charge_state(
            peptide,
            charge=charge,
            registry=registry,
        )
        envelope = approximate_peptide_isotope_envelope(
            peptide,
            charge=charge,
            peak_count=isotope_peaks,
            registry=registry,
        )
        localization = build_modification_localization_advisory(
            peptide,
            registry=registry,
        )
        fragments = calculate_fragment_ions(
            peptide,
            charges=(charge,),
            series=tuple(FragmentIonSeries(series) for series in fragment_series),
            include_neutral_losses=include_neutral_losses,
            registry=registry,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = {
        "canonical_notation": canonicalize_modified_peptide(peptide, registry=registry),
        "charge_state": charge_state.to_dict(),
        "isotope_envelope": envelope.to_dict(),
        "localization": localization.to_dict(),
        "fragment_ion_count": len(fragments),
        "fragments": [fragment.to_dict() for fragment in fragments],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("psm-inspect")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def psm_inspect_command(
    input_tsv: Path,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Inspect a generic PSM TSV and emit normalized summaries."""
    try:
        mapping = _build_psm_mapping(
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        normalized = apply_q_values(report.accepted_records)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(normalized, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(normalized, tsv_out)

    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=report,
        decoy_policy=decoy_policy,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")

    payload = {
        "accepted_rows": len(report.accepted_records),
        "rejected_rows": len(report.rejected_rows),
        "psm_summary": build_psm_summary_report(normalized).to_dict(),
        "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
        "protein_summary": build_protein_summary_report(normalized).to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("fdr")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--audit-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--calibration-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    audit_out: Path | None,
    calibration_out: Path | None,
    out_path: Path | None,
) -> None:
    """Apply basic target-decoy FDR and emit filtered PSM summaries."""
    try:
        mapping = _build_psm_mapping(
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(accepted, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(accepted, tsv_out)

    fdr_policy = FdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=parse_report,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    audit_trail = build_fdr_audit_trail(
        parse_report.accepted_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    calibration_plot = build_calibration_plot_data(
        parse_report.accepted_records,
        score_orientation=score_orientation,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    if audit_out is not None:
        audit_out.write_text(audit_trail.to_stable_json() + "\n")
    if calibration_out is not None:
        calibration_out.write_text(calibration_plot.to_stable_json() + "\n")

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted),
        "psm_summary": build_psm_summary_report(accepted).to_dict(),
        "peptide_summary": build_peptide_summary_report(accepted).to_dict(),
        "protein_summary": build_protein_summary_report(accepted).to_dict(),
        "audit_trail": audit_trail.to_dict(),
        "calibration_plot": calibration_plot.to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("infer-proteins")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def infer_proteins_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    fasta_path: Path | None,
    out_path: Path | None,
) -> None:
    """Infer proteins, group evidence, and emit multi-level FDR artifacts."""
    try:
        mapping = _build_psm_mapping(
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        level_fdr = calculate_level_specific_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_charge = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="charge_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_modification = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="modification_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        protein_groups = build_protein_groups(accepted_records)
        confidence_labels = assign_confidence_labels(
            calculate_picked_protein_fdr(
                accepted_records,
                threshold=threshold,
                score_orientation=score_orientation,
                decoy_policy=decoy_policy,
            )
        )
        parsimony = infer_proteins_by_parsimony(accepted_records)
        picked_fdr = calculate_picked_protein_fdr(
            accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
        protein_sequences: dict[str, str] | None = None
        coverage_payload = None
        uniqueness_payload = None
        if fasta_path is not None:
            fasta_report = parse_fasta_document(
                fasta_path.read_text(), mode=FastaParseMode.STRICT
            )
            if fasta_report.rejected_records:
                rejected = ", ".join(
                    record.source_identifier for record in fasta_report.rejected_records
                )
                raise click.ClickException(
                    f"FASTA input contains rejected records under strict mode: {rejected}"
                )
            protein_sequences = {
                record.canonical_accession: record.residues
                for record in fasta_report.accepted_records
            }
            coverage_payload = [
                entry.to_dict()
                for entry in build_protein_coverage_map(
                    accepted_records,
                    protein_sequences=protein_sequences,
                )
            ]
            uniqueness_payload = [
                entry.to_dict()
                for entry in build_peptide_uniqueness_across_database(
                    tuple(
                        dict.fromkeys(
                            record.canonical_peptide for record in accepted_records
                        )
                    ),
                    protein_sequences=protein_sequences,
                )
            ]
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted_records),
        "level_fdr": level_fdr.to_dict(),
        "grouped_fdr": {
            "charge_state": grouped_charge.to_dict(),
            "modification_state": grouped_modification.to_dict(),
        },
        "protein_groups": [entry.to_dict() for entry in protein_groups],
        "parsimony_proteins": [entry.to_dict() for entry in parsimony],
        "picked_protein_fdr": [entry.to_dict() for entry in picked_fdr],
        "confidence_labels": [entry.to_dict() for entry in confidence_labels],
        "razor_assignments": [
            entry.to_dict() for entry in assign_razor_peptides(accepted_records)
        ],
        "protein_coverage": coverage_payload,
        "database_uniqueness": uniqueness_payload,
    }
    _emit_json(payload, out_path=out_path)


@cli.command("quantify")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--measure",
    type=_quant_measure_choice(),
    default=QuantMeasureKind.INTENSITY.value,
    show_default=True,
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--report-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def quantify_command(
    input_table: Path,
    measure: str,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    report_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a quantification matrix and optional differential report from MS1 features."""
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(
            input_table,
            mapping=mapping,
        )
        quant_entity_level = QuantEntityLevel(entity_level)
        quant_measure = QuantMeasureKind(measure)
        rollup_method = QuantRollupMethod(aggregation)
        if quant_measure is QuantMeasureKind.SPECTRAL_COUNT:
            table = build_spectral_count_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
            )
        else:
            table = build_label_free_intensity_table(
                parse_report.accepted_records,
                entity_level=quant_entity_level,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            table = normalize_label_free_table(
                table,
                method=NormalizationMethod(normalization),
            )
        missing_summary = summarize_missing_values(table)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        batch_effect = None
        replicate_correlations = None
        differential = None
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
            batch_effect = build_batch_effect_advisory(table, design_entries)
            replicate_correlations = build_replicate_correlation_report(
                table, design_entries
            )
            if quant_measure is QuantMeasureKind.INTENSITY:
                differential = apply_benjamini_hochberg(
                    build_differential_abundance_report(
                        table,
                        design_entries,
                        condition_a=condition_a,
                        condition_b=condition_b,
                    )
                )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "table": table.to_dict(),
        "missing_summary": missing_summary.to_dict(),
        "design_entries": len(design_entries),
        "batch_effect": batch_effect.to_dict() if batch_effect is not None else None,
        "replicate_correlations": (
            replicate_correlations.to_dict()
            if replicate_correlations is not None
            else None
        ),
        "differential_abundance": differential.to_dict()
        if differential is not None
        else None,
    }
    _emit_json(payload, out_path=report_out or out_path)


@cli.command("spectrum-stats")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_stats_command(
    input_mgf: Path,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    """Summarize one MGF collection."""
    report = parse_mgf(input_mgf)
    summary = build_spectrum_collection_summary(report)
    provenance = build_spectrum_provenance_manifest(
        source_path=input_mgf, parse_report=report
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "summary": summary.to_dict(),
        "provenance": provenance.to_dict(),
        "metrics": [
            build_spectrum_metrics(spectrum).to_dict()
            for spectrum in report.accepted_spectra
        ],
    }
    _emit_json(payload, out_path=out_path)


@cli.command("spectrum-annotate")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide", required=True)
@click.option(
    "--spectrum-id",
    default=None,
    help="Optional target spectrum id; defaults to the first accepted spectrum.",
)
@click.option("--tolerance-da", type=float, default=0.02, show_default=True)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--plot-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON annotation output path.",
)
def spectrum_annotate_command(
    input_mgf: Path,
    peptide: str,
    spectrum_id: str | None,
    tolerance_da: float,
    tsv_out: Path | None,
    plot_out: Path | None,
    out_path: Path | None,
) -> None:
    """Annotate one spectrum against a peptide sequence."""
    report = parse_mgf(input_mgf)
    if not report.accepted_spectra:
        raise click.ClickException(
            "MGF input does not contain an accepted spectrum to annotate"
        )
    if spectrum_id is None:
        spectrum = report.accepted_spectra[0]
    else:
        try:
            spectrum = next(
                item
                for item in report.accepted_spectra
                if item.spectrum_id == spectrum_id
            )
        except StopIteration as exc:
            raise click.ClickException(f"unknown spectrum id {spectrum_id!r}") from exc
    try:
        annotation = annotate_spectrum_fragments(
            spectrum,
            peptide=peptide,
            tolerance_da=tolerance_da,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    plot_payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    if tsv_out is not None:
        export_spectrum_annotation_tsv(annotation, tsv_out)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n")
    payload = {
        "annotation": annotation.to_dict(),
        "plot_payload": plot_payload.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.command("validate")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation output path.",
)
def validate_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Validate one FASTA, PSM TSV, MGF, mzML, design table, or modification registry input."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = validate_proteomics_input(
            input_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


@cli.command("summarize")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def summarize_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    """Summarize one FASTA, PSM TSV, MGF, mzML, or design-table input."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    if resolved_kind == "fasta":
        fasta_report = parse_fasta_document(
            input_path.read_text(), mode=FastaParseMode(mode)
        )
        payload = {
            "input_kind": resolved_kind,
            "summary": build_fasta_stats(fasta_report.accepted_records).to_dict(),
            "rejected_records": len(fasta_report.rejected_records),
        }
    elif resolved_kind == "psm":
        psm_report = parse_psm_tsv(input_path, mapping=_default_psm_mapping())
        normalized = apply_q_values(psm_report.accepted_records)
        payload = {
            "input_kind": resolved_kind,
            "psm_summary": build_psm_summary_report(normalized).to_dict(),
            "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
            "protein_summary": build_protein_summary_report(normalized).to_dict(),
            "rejected_rows": len(psm_report.rejected_rows),
        }
    elif resolved_kind == "mgf":
        mgf_report = parse_mgf(input_path)
        payload = {
            "input_kind": resolved_kind,
            "summary": build_spectrum_collection_summary(mgf_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mgf_report.accepted_spectra
            ],
        }
    elif resolved_kind == "mzml":
        mzml_report = parse_mzml(input_path)
        payload = {
            "input_kind": resolved_kind,
            "metadata": mzml_report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(mzml_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mzml_report.accepted_spectra
            ],
        }
    elif resolved_kind == "design-table":
        design_report = parse_experimental_design_table(input_path)
        payload = {
            "input_kind": resolved_kind,
            "accepted_entries": len(design_report.accepted_entries),
            "rejected_rows": len(design_report.rejected_rows),
            "instruments": sorted(
                {
                    entry.instrument
                    for entry in design_report.accepted_entries
                    if entry.instrument is not None
                }
            ),
            "search_engines": sorted(
                {
                    entry.search_engine
                    for entry in design_report.accepted_entries
                    if entry.search_engine is not None
                }
            ),
        }
    else:
        raise click.ClickException(
            "summarize currently supports fasta, psm, mgf, mzml, and design-table inputs"
        )
    _emit_json(payload, out_path=out_path)


@cli.command("format-convert")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option("--to", "target_format", type=_conversion_target_choice(), required=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the converted normalized output.",
)
def format_convert_command(
    input_path: Path,
    input_kind: str,
    target_format: str,
    out_path: Path,
) -> None:
    """Convert one supported input into a normalized Bijux output surface."""
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = convert_proteomics_format(
            input_path=input_path,
            output_path=out_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
            target_format=FormatConversionTarget(target_format),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report)


@cli.command("bundle-run")
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out-dir",
    "out_dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
    help="Directory where the normalized run bundle should be written.",
)
def bundle_run_command(
    spectra_path: Path,
    identifications_path: Path | None,
    design_path: Path | None,
    out_dir: Path,
) -> None:
    """Build one normalized run bundle from spectra, IDs, and optional design metadata."""
    try:
        manifest = build_normalized_run_bundle(
            bundle_dir=out_dir,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            design_path=design_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(manifest)


@cli.command("workflow-plan")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--dag-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--job-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--checkpoint-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_plan_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
    dag_out: Path | None,
    job_out: Path | None,
    checkpoint_out: Path | None,
) -> None:
    """Build a workflow-runtime bundle for digest/search/FDR/quant/QC execution."""
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        if dag_out is not None:
            dag_out.write_text(
                bundle.dag_plan.to_stable_json() + "\n", encoding="utf-8"
            )
        if job_out is not None:
            job_out.write_text(bundle.hpc_job.script_text, encoding="utf-8")
        if checkpoint_out is not None:
            checkpoint_out.write_text(
                bundle.checkpoint.to_stable_json() + "\n", encoding="utf-8"
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(bundle, out_path=out_path)


@cli.command("workflow-validate")
@click.option(
    "--proteins",
    "proteins_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--identifications",
    "identifications_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--features",
    "features_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option(
    "--search-adapter",
    type=_search_adapter_choice(),
    default=SearchAdapterKind.GENERIC.value,
    show_default=True,
)
@click.option(
    "--scheduler",
    type=_workflow_scheduler_choice(),
    default=WorkflowSchedulerKind.SLURM.value,
    show_default=True,
)
@click.option(
    "--container-image",
    default="ghcr.io/bijux/proteomics-runtime:stable",
    show_default=True,
)
@click.option(
    "--artifacts-dir", type=click.Path(path_type=Path, file_okay=False), default=None
)
@click.option("--completed-step", "completed_steps", multiple=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def workflow_validate_command(
    proteins_path: Path,
    spectra_path: Path,
    identifications_path: Path | None,
    features_path: Path | None,
    design_path: Path | None,
    sample_id: str | None,
    search_adapter: str,
    scheduler: str,
    container_image: str,
    artifacts_dir: Path | None,
    completed_steps: tuple[str, ...],
    out_path: Path | None,
) -> None:
    """Validate workflow runtime integrity without executing the workflow."""
    try:
        bundle = build_proteomics_workflow_runtime_bundle(
            proteins_path=proteins_path,
            spectra_path=spectra_path,
            identifications_path=identifications_path,
            features_path=features_path,
            design_path=design_path,
            sample_id=sample_id,
            search_adapter_kind=SearchAdapterKind(search_adapter),
            scheduler=WorkflowSchedulerKind(scheduler),
            default_container_image=container_image,
            artifacts_dir=artifacts_dir,
            completed_step_ids=tuple(completed_steps),
        )
        report = build_workflow_runtime_validation_report(bundle)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


@cli.group("qc")
def qc_group() -> None:
    """Build operator-facing LC-MS QC reports and artifacts."""


@qc_group.command("report")
@click.argument(
    "spectra_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-id", default=None)
@click.option("--run-id", default=None)
@click.option(
    "--policy",
    "policy_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--html-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--manifest-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--benchmark-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def qc_report_command(
    spectra_path: Path,
    psm_path: Path,
    proteins_fasta: Path,
    design_path: Path | None,
    sample_id: str | None,
    run_id: str | None,
    policy_path: Path | None,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    out_path: Path | None,
    tsv_out: Path | None,
    html_out: Path | None,
    manifest_out: Path | None,
    benchmark_out: Path | None,
) -> None:
    """Build QC summaries, threshold assessments, evidence manifests, and benchmark artifacts."""
    timings: dict[str, tuple[float, int | None]] = {}
    try:
        policy = default_qc_threshold_policy()
        if policy_path is not None:
            try:
                policy = load_qc_threshold_policy(policy_path)
            except Exception as exc:  # noqa: BLE001
                raise ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_POLICY_INVALID,
                    str(exc),
                ) from exc

        started = time.perf_counter()
        design_entry = _select_design_entry(
            design_path, sample_id=sample_id, spectra_path=spectra_path
        )
        timings["parse_design"] = (
            time.perf_counter() - started,
            0 if design_entry is None else 1,
        )

        started = time.perf_counter()
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise ProteomicsOperatorError(
                ProteomicsOperatorErrorCode.INPUT_FASTA_REJECTED,
                f"FASTA input contains rejected records under strict mode: {rejected}",
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        timings["parse_fasta"] = (
            time.perf_counter() - started,
            len(fasta_report.accepted_records),
        )

        started = time.perf_counter()
        spectrum_report = parse_mgf(spectra_path)
        timings["parse_spectra"] = (
            time.perf_counter() - started,
            len(spectrum_report.accepted_spectra),
        )

        started = time.perf_counter()
        psm_report = parse_psm_tsv(
            psm_path,
            mapping=SearchResultColumnMapping(
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
            ),
        )
        timings["parse_psms"] = (
            time.perf_counter() - started,
            len(psm_report.accepted_records),
        )

        started = time.perf_counter()
        run_report = build_lcms_run_qc_report(
            spectrum_report.accepted_spectra,
            psm_report.accepted_records,
            design_entry=design_entry,
            protein_sequences=protein_sequences,
            run_id=run_id,
        )
        run_assessment = build_run_qc_assessment(run_report, policy=policy)
        timings["build_run_qc"] = (
            time.perf_counter() - started,
            len(run_assessment.metric_assessments),
        )

        started = time.perf_counter()
        batch_report = None
        batch_assessment = None
        if design_entry and design_entry.batch:
            batch_report = build_instrument_batch_qc_report((run_report,))
            batch_assessment = build_batch_qc_assessment(batch_report, policy=policy)
        timings["build_batch_qc"] = (
            time.perf_counter() - started,
            0 if batch_assessment is None else len(batch_assessment.metric_assessments),
        )

        benchmark = build_performance_snapshot(run_report.run_id, operations=timings)
        input_files = [
            QcEvidenceInputFile(
                path=str(spectra_path),
                sha256=_file_sha256(spectra_path),
                role="spectra",
            ),
            QcEvidenceInputFile(
                path=str(psm_path),
                sha256=_file_sha256(psm_path),
                role="identifications",
            ),
            QcEvidenceInputFile(
                path=str(proteins_fasta),
                sha256=_file_sha256(proteins_fasta),
                role="proteins",
            ),
        ]
        if design_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(design_path),
                    sha256=_file_sha256(design_path),
                    role="design",
                )
            )
        if policy_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(policy_path),
                    sha256=_file_sha256(policy_path),
                    role="qc_policy",
                )
            )
        manifest = build_qc_evidence_manifest(
            run_report=run_report,
            run_assessment=run_assessment,
            policy=policy,
            input_files=tuple(input_files),
            batch_report=batch_report,
            batch_assessment=batch_assessment,
            benchmark=benchmark,
        )
    except ProteomicsOperatorError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_BUILD_FAILED, str(exc)
                )
            )
        ) from exc

    try:
        if tsv_out is not None:
            _write_text_output(
                tsv_out,
                render_qc_assessment_tsv(
                    run_assessment, batch_assessment=batch_assessment
                ),
            )
        if html_out is not None:
            _write_text_output(
                html_out,
                render_qc_assessment_html(
                    run_report,
                    run_assessment,
                    batch_report=batch_report,
                    batch_assessment=batch_assessment,
                ),
            )
        if manifest_out is not None:
            manifest_out.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
        if benchmark_out is not None:
            benchmark_out.write_text(
                benchmark.to_stable_json() + "\n", encoding="utf-8"
            )
    except OSError as exc:
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_OUTPUT_WRITE_FAILED, str(exc)
                )
            )
        ) from exc

    payload = {
        "run_report": run_report.to_dict(),
        "run_assessment": run_assessment.to_dict(),
        "batch_report": None if batch_report is None else batch_report.to_dict(),
        "batch_assessment": None
        if batch_assessment is None
        else batch_assessment.to_dict(),
        "evidence_manifest": manifest.to_dict(),
        "performance_snapshot": benchmark.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


@cli.group("ptm")
def ptm_group() -> None:
    """Summarize PTM evidence, mapped sites, and occupancy outputs."""


@ptm_group.command("summarize")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--features",
    "feature_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option("--flank-size", type=int, default=7, show_default=True)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_summarize_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_path: Path | None,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    threshold: float,
    flank_size: int,
    out_path: Path | None,
) -> None:
    """Summarize PTM site evidence from localized peptides and optional feature intensities."""
    try:
        mapping = PtmLocalizationColumnMapping(
            sample_id=sample_column,
            spectrum_id=spectrum_id_column,
            peptide=peptide_column,
            charge=charge_column,
            score=score_column,
            protein_refs=protein_refs_column,
            q_value=q_value_column,
            localization_score=localization_score_column,
            candidate_sites=candidate_sites_column,
            decoy_label=decoy_label_column,
            protein_separator=protein_separator,
            site_separator=site_separator,
        )
        evidence = parse_ptm_localization_tsv(evidence_tsv, mapping=mapping)
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        ambiguity = build_ptm_site_ambiguity_report(site_table)
        coverage = build_ptm_site_coverage_report(mappings)
        fdr = build_ptm_site_fdr(site_table, threshold=threshold)
        motifs = build_ptm_motif_windows(
            site_table, protein_sequences=protein_sequences, flank_size=flank_size
        )
        enrichment = build_ptm_enrichment_input(
            site_table, protein_sequences=protein_sequences
        )
        occupancy = None
        if feature_path is not None:
            feature_report = parse_ms1_feature_table(feature_path)
            occupancy = estimate_ptm_site_occupancy(
                site_table,
                feature_records=feature_report.accepted_records,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    payload = {
        "accepted_rows": len(evidence.accepted_records),
        "rejected_rows": len(evidence.rejected_rows),
        "site_table": [entry.to_dict() for entry in site_table],
        "ambiguity_report": [entry.to_dict() for entry in ambiguity],
        "coverage_report": [entry.to_dict() for entry in coverage],
        "fdr_report": fdr.to_dict(),
        "motif_windows": [entry.to_dict() for entry in motifs],
        "enrichment_input": enrichment.to_dict(),
        "occupancy": [entry.to_dict() for entry in occupancy]
        if occupancy is not None
        else None,
    }
    _emit_json(payload, out_path=out_path)


@cli.group("search-adapter")
def search_adapter_group() -> None:
    """Inspect and normalize search-engine-specific result tables."""


@search_adapter_group.command("inspect")
@click.option("--adapter", "adapter_name", type=_search_adapter_choice(), default=None)
def search_adapter_inspect_command(adapter_name: str | None) -> None:
    """Inspect one adapter manifest or the full capability matrix."""
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


@search_adapter_group.command("params")
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
    """Parse one supported search-engine parameter file."""
    try:
        payload = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("validate-config")
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
    """Validate one supported search-engine parameter file."""
    try:
        parameters = parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind(adapter_name),
        )
        payload = validate_search_parameters(parameters)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(payload, out_path=out_path)


@search_adapter_group.command("normalize")
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
    """Normalize one engine-specific search-result table into stable PSM records."""
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


@search_adapter_group.command("compare")
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
    """Compare two normalized adapter outputs on a shared score scale."""
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


@search_adapter_group.command("conformance")
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
    """Run the built-in adapter conformance checks on one search-result table."""
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
