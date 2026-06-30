# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Typed input resolution helpers for sequence-adjacent workflows."""

from __future__ import annotations

from typing import cast

from ..imports import *  # noqa: F401,F403


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return cast(
        tuple[PsmRecord, ...],
        filter_psms_by_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        ),
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
