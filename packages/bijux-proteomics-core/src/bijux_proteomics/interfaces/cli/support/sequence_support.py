# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Sequence, FASTA, and click-choice helpers shared by CLI command modules."""

from __future__ import annotations

from .imports import *  # noqa: F401,F403

from .output_protocol import _emit_json, _write_text_output

def _resolve_cli_protease_rule(
    *,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
) -> tuple[ProteaseRule, str | None]:
    specification = custom_protease.strip() if custom_protease is not None else ""
    if not specification:
        rule = resolve_protease_rule(protease)
        return rule, None
    if protease != "trypsin":
        raise ValueError(
            "custom protease rules cannot be combined with a second built-in protease name"
        )
    rule = resolve_protease_rule(
        custom_specification=specification,
        custom_name=custom_protease_name,
    )
    return rule, specification

def _resolve_cli_theoretical_digest_modifications(
    *,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
) -> tuple[
    ModificationRegistryDocument | None,
    tuple[StaticModification, ...],
    tuple[VariableModification, ...],
    IsotopicLabelingPolicy | None,
]:
    registry = (
        load_modification_registry(registry_path)
        if registry_path is not None
        else None
    )
    resolved_static: list[StaticModification] = []
    for token in static_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, StaticModification):
            raise ValueError(f"static modification {token!r} is not a static definition")
        resolved_static.append(definition)
    resolved_variable: list[VariableModification] = []
    for token in variable_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, VariableModification):
            raise ValueError(
                f"variable modification {token!r} is not a variable definition"
            )
        resolved_variable.append(definition)
    labeling_policy = (
        IsotopicLabelingPolicy(
            allow_isotopic_labels=allow_isotopic_labels,
            allowed_label_families=allowed_label_families,
        )
        if allow_isotopic_labels or allowed_label_families
        else None
    )
    return registry, tuple(resolved_static), tuple(resolved_variable), labeling_policy

def _emit_fasta_profile(
    profile: FastaDatabaseProfile,
    *,
    out_path: Path | None,
    summary_tsv_out: Path | None,
    length_tsv_out: Path | None,
    organism_tsv_out: Path | None,
    invalid_sequence_tsv_out: Path | None,
) -> None:
    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_fasta_profile_summary_tsv(profile))
    if length_tsv_out is not None:
        _write_text_output(
            length_tsv_out, render_fasta_profile_length_distribution_tsv(profile)
        )
    if organism_tsv_out is not None:
        _write_text_output(
            organism_tsv_out, render_fasta_profile_organism_distribution_tsv(profile)
        )
    if invalid_sequence_tsv_out is not None:
        _write_text_output(
            invalid_sequence_tsv_out,
            render_fasta_profile_invalid_sequence_tsv(profile),
        )
    _emit_json(profile, out_path=out_path)

def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _load_fasta_report(
    input_path: Path,
    *,
    mode: FastaParseMode,
    duplicate_accession_policy: DuplicateAccessionPolicy = DuplicateAccessionPolicy.REJECT,
    allow_rejected: bool,
) -> FastaParseReport:
    report = parse_fasta_document(
        input_path.read_text(),
        mode=mode,
        duplicate_accession_policy=duplicate_accession_policy,
    )
    if report.rejected_records and not allow_rejected:
        rejected = ", ".join(
            rejected.source_identifier for rejected in report.rejected_records
        )
        raise click.ClickException(
            f"FASTA input contains rejected records under {mode.value} mode: {rejected}"
        )
    return report

def _load_precursor_mass_error_queries(
    input_tsv: Path,
    *,
    peptide_column: str,
    observed_mz_column: str,
    charge_column: str,
    spectrum_id_column: str | None,
) -> tuple[PrecursorMassErrorQuery, ...]:
    queries: list[PrecursorMassErrorQuery] = []
    with input_tsv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "precursor mass-error TSV must include a header row"
            )
        for required_column in (peptide_column, observed_mz_column, charge_column):
            if required_column not in reader.fieldnames:
                raise click.ClickException(
                    f"missing required precursor mass-error column {required_column!r}"
                )

        for row_number, row in enumerate(reader, start=2):
            try:
                peptide = str(row.get(peptide_column, "")).strip()
                observed_mz = float(str(row.get(observed_mz_column, "")).strip())
                charge = int(str(row.get(charge_column, "")).strip())
                if not peptide:
                    raise ValueError("peptide must not be blank")
                if observed_mz <= 0:
                    raise ValueError("observed_mz must be greater than zero")
                if charge < 1:
                    raise ValueError("charge must be at least 1")
                spectrum_id = (
                    str(row.get(spectrum_id_column, "")).strip()
                    if spectrum_id_column is not None
                    else ""
                )
                queries.append(
                    PrecursorMassErrorQuery(
                        peptide=peptide,
                        observed_mz=observed_mz,
                        charge=charge,
                        spectrum_id=spectrum_id or None,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise click.ClickException(
                    f"invalid precursor mass-error row at line {row_number}: {exc}"
                ) from exc
    return tuple(queries)

def _mode_choice() -> click.Choice[str]:
    return click.Choice([mode.value for mode in FastaParseMode], case_sensitive=False)

def _duplicate_accession_policy_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in DuplicateAccessionPolicy],
        case_sensitive=False,
    )

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
    return click.Choice(["tsv", "jsonl", "parquet", "fasta"], case_sensitive=False)

def _fragment_series_choice() -> click.Choice[str]:
    return click.Choice(
        [series.value for series in FragmentIonSeries], case_sensitive=False
    )

def _modified_peptide_dialect_choice() -> click.Choice[str]:
    return click.Choice(
        [dialect.value for dialect in SearchEngineModifiedPeptideDialect],
        case_sensitive=False,
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

def _imputation_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in ImputationMethod], case_sensitive=False
    )

def _heatmap_missing_value_choice() -> click.Choice[str]:
    return click.Choice(
        [policy.value for policy in HeatmapMissingValuePolicy],
        case_sensitive=False,
    )

def _peptide_matrix_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "psm"), case_sensitive=False)

def _peptide_matrix_builder_input_kind_choice() -> click.Choice[str]:
    return click.Choice(("feature", "precursor", "psm"), case_sensitive=False)

def _peptide_matrix_grouping_choice() -> click.Choice[str]:
    return click.Choice(
        [mode.value for mode in PeptideMatrixGroupingMode], case_sensitive=False
    )

def _protein_matrix_target_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in ProteinMatrixTargetKind], case_sensitive=False
    )

def _tmt_source_kind_choice() -> click.Choice[str]:
    return click.Choice(
        [kind.value for kind in TmtSearchResultSourceKind], case_sensitive=False
    )

def _tmt_normalization_method_choice() -> click.Choice[str]:
    return click.Choice(
        [method.value for method in TmtNormalizationMethod], case_sensitive=False
    )

def _tmt_ratio_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        ("none", *[method.value for method in TmtNormalizationMethod]),
        case_sensitive=False,
    )

def _label_based_differential_normalization_choice() -> click.Choice[str]:
    return click.Choice(
        (NormalizationMethod.NONE.value, NormalizationMethod.MEDIAN.value),
        case_sensitive=False,
    )

def _silac_label_choice() -> click.Choice[str]:
    return click.Choice([label.value for label in SilacLabel], case_sensitive=False)

def _workflow_scheduler_choice() -> click.Choice[str]:
    return click.Choice(
        [scheduler.value for scheduler in WorkflowSchedulerKind], case_sensitive=False
    )

def _parse_tmt_channel_column_specs(
    specs: tuple[str, ...],
) -> tuple[TmtReporterChannelColumn, ...]:
    resolved: list[TmtReporterChannelColumn] = []
    for spec in specs:
        if "=" not in spec:
            raise click.ClickException(
                "channel-column must use CHANNEL=COLUMN syntax"
            )
        channel, column_name = spec.split("=", 1)
        channel = channel.strip()
        column_name = column_name.strip()
        if not channel or not column_name:
            raise click.ClickException(
                "channel-column must use CHANNEL=COLUMN syntax"
            )
        resolved.append(
            TmtReporterChannelColumn(
                multiplex_channel=channel,
                column_name=column_name,
            )
        )
    return tuple(resolved)

def _parse_silac_label_spec(spec: str) -> tuple[SilacLabel, ...]:
    labels = tuple(
        SilacLabel(token.strip().lower())
        for token in spec.split(",")
        if token.strip()
    )
    if len(labels) < 2:
        raise click.ClickException("labels must name at least two SILAC label states")
    return labels

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
    run_id_column: str | None,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    posterior_error_probability_column: str | None = None,
    intensity_column: str | None = None,
) -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        run_id=run_id_column,
        spectrum_id=spectrum_id_column,
        peptide=peptide_column,
        modified_peptide=modified_peptide_column,
        charge=charge_column,
        score=score_column,
        intensity=intensity_column,
        q_value=q_value_column,
        posterior_error_probability=posterior_error_probability_column,
        protein_refs=protein_refs_column,
        decoy_label=decoy_label_column,
        contaminant_label=contaminant_label_column,
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

def _build_run_detection_contexts(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> tuple[RunDetectionContext, ...]:
    return tuple(
        RunDetectionContext(
            run_id=entry.spectra_file,
            sample_id=entry.sample_id,
            condition_id=entry.condition,
            replicate_id=str(entry.replicate),
        )
        for entry in design_entries
    )

def _filter_review_psms(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    """Preserve imported q-values for review surfaces when they are complete."""
    if records and all(record.q_value is not None for record in records):
        return tuple(
            record
            for record in records
            if record.q_value is not None and record.q_value <= threshold
        )
    return filter_psms_by_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
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

__all__ = [name for name in globals() if not name.startswith("__")]
