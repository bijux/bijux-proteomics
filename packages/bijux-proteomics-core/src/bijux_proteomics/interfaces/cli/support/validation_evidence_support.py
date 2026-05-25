# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Validation-evidence loaders shared by CLI command modules."""

from __future__ import annotations

from .imports import *  # noqa: F401,F403

from .targeted_selection_io import _parse_cli_bool, _split_semicolon_field

def _load_validation_evidence_discovery_candidates(
    path: Path,
) -> tuple[ValidationEvidenceDiscoveryInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "weighted_evidence_total",
            "penalty_total",
            "uncertainty",
            "effect_size",
            "adjusted_p_value",
            "support_count",
            "annotation_labels",
            "rank_reason_codes",
            "source_ids",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceDiscoveryInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceDiscoveryInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("candidate_kind", "")).strip()
                        ),
                        display_label=str(row.get("display_label", "")).strip(),
                        target_protein_ref=str(row.get("target_protein_ref", "")).strip(),
                        site_key=(
                            None
                            if not str(row.get("site_key", "")).strip()
                            else str(row.get("site_key", "")).strip()
                        ),
                        priority_rank=int(str(row.get("priority_rank", "")).strip()),
                        final_score=float(str(row.get("final_score", "")).strip()),
                        weighted_evidence_total=float(
                            str(row.get("weighted_evidence_total", "")).strip()
                        ),
                        penalty_total=float(str(row.get("penalty_total", "")).strip()),
                        uncertainty=float(str(row.get("uncertainty", "")).strip()),
                        effect_size=(
                            None
                            if not str(row.get("effect_size", "")).strip()
                            else float(str(row.get("effect_size", "")).strip())
                        ),
                        adjusted_p_value=(
                            None
                            if not str(row.get("adjusted_p_value", "")).strip()
                            else float(str(row.get("adjusted_p_value", "")).strip())
                        ),
                        support_count=int(str(row.get("support_count", "")).strip()),
                        annotation_labels=_split_semicolon_field(
                            row.get("annotation_labels", "")
                        ),
                        rank_reason_codes=_split_semicolon_field(
                            row.get("rank_reason_codes", "")
                        ),
                        source_ids=_split_semicolon_field(row.get("source_ids", "")),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biomarker-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_panel_assays(
    path: Path,
) -> tuple[ValidationEvidencePanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel assay TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_display_label",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "uniqueness_score",
            "precursor_charge",
            "precursor_mz",
            "expected_retention_time_minutes",
            "retention_window_start_minutes",
            "retention_window_end_minutes",
            "selected_transition_count",
            "exported_transition_count",
            "assay_interference_risk_tier",
            "warning_codes",
            "warning_note",
            "source_library_entry_id",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "panel assay TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidencePanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidencePanelAssayInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        biomarker_candidate_id=str(
                            row.get("biomarker_candidate_id", "")
                        ).strip(),
                        biomarker_candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("biomarker_candidate_kind", "")).strip()
                        ),
                        biomarker_display_label=str(
                            row.get("biomarker_display_label", "")
                        ).strip(),
                        biomarker_priority_rank=int(
                            str(row.get("biomarker_priority_rank", "")).strip()
                        ),
                        target_protein_ref=str(row.get("target_protein_ref", "")).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(
                            row.get("canonical_peptide", "")
                        ).strip(),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
                        ),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        precursor_mz=float(str(row.get("precursor_mz", "")).strip()),
                        expected_retention_time_minutes=(
                            None
                            if not str(
                                row.get("expected_retention_time_minutes", "")
                            ).strip()
                            else float(
                                str(
                                    row.get("expected_retention_time_minutes", "")
                                ).strip()
                            )
                        ),
                        retention_window_start_minutes=(
                            None
                            if not str(
                                row.get("retention_window_start_minutes", "")
                            ).strip()
                            else float(
                                str(
                                    row.get("retention_window_start_minutes", "")
                                ).strip()
                            )
                        ),
                        retention_window_end_minutes=(
                            None
                            if not str(
                                row.get("retention_window_end_minutes", "")
                            ).strip()
                            else float(
                                str(row.get("retention_window_end_minutes", "")).strip()
                            )
                        ),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        assay_interference_risk_tier=TargetedAssayInterferenceRiskTier(
                            str(row.get("assay_interference_risk_tier", "")).strip()
                        ),
                        warning_codes=tuple(
                            TargetedPanelWarningCode(code)
                            for code in _split_semicolon_field(
                                row.get("warning_codes", "")
                            )
                        ),
                        warning_note=str(row.get("warning_note", "")).strip(),
                        source_library_entry_id=(
                            None
                            if not str(row.get("source_library_entry_id", "")).strip()
                            else str(row.get("source_library_entry_id", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid panel assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_omitted_candidates(
    path: Path,
) -> tuple[ValidationEvidenceOmittedCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "omitted-candidate TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "omission_reason",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "omitted-candidate TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceOmittedCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceOmittedCandidateInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("candidate_kind", "")).strip()
                        ),
                        display_label=str(row.get("display_label", "")).strip(),
                        target_protein_ref=str(row.get("target_protein_ref", "")).strip(),
                        site_key=(
                            None
                            if not str(row.get("site_key", "")).strip()
                            else str(row.get("site_key", "")).strip()
                        ),
                        priority_rank=int(str(row.get("priority_rank", "")).strip()),
                        omission_reason=str(row.get("omission_reason", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid omitted-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_results(
    path: Path,
) -> tuple[ValidationEvidenceResultInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "validation TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "verdict",
            "validation_log2_effect",
            "assay_evidence_count",
            "confirmed_assay_count",
            "contradicted_assay_count",
            "inconclusive_assay_count",
            "reason_codes",
            "note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "validation TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceResultInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceResultInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        verdict=TargetedValidationVerdict(
                            str(row.get("verdict", "")).strip()
                        ),
                        validation_log2_effect=(
                            None
                            if not str(row.get("validation_log2_effect", "")).strip()
                            else float(
                                str(row.get("validation_log2_effect", "")).strip()
                            )
                        ),
                        assay_evidence_count=int(
                            str(row.get("assay_evidence_count", "")).strip()
                        ),
                        confirmed_assay_count=int(
                            str(row.get("confirmed_assay_count", "")).strip()
                        ),
                        contradicted_assay_count=int(
                            str(row.get("contradicted_assay_count", "")).strip()
                        ),
                        inconclusive_assay_count=int(
                            str(row.get("inconclusive_assay_count", "")).strip()
                        ),
                        reason_codes=tuple(
                            TargetedValidationReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("reason_codes", "")
                            )
                        ),
                        note=str(row.get("note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid validation row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_result_assays(
    path: Path,
) -> tuple[ValidationEvidenceResultAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "validation-evidence TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "assay_entry_id",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "uniqueness_class",
            "validation_log2_effect",
            "verdict",
            "reason_codes",
            "note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "validation-evidence TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceResultAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceResultAssayInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(
                            row.get("canonical_peptide", "")
                        ).strip(),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        validation_log2_effect=(
                            None
                            if not str(row.get("validation_log2_effect", "")).strip()
                            else float(
                                str(row.get("validation_log2_effect", "")).strip()
                            )
                        ),
                        verdict=TargetedValidationVerdict(
                            str(row.get("verdict", "")).strip()
                        ),
                        reason_codes=tuple(
                            TargetedValidationReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("reason_codes", "")
                            )
                        ),
                        note=str(row.get("note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid validation-evidence row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_stability_entries(
    path: Path,
) -> tuple[ValidationEvidenceStabilityInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "stability TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "stability_score",
            "stability_penalty",
            "downgraded",
            "instability_reasons",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "stability TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceStabilityInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceStabilityInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        stability_score=float(
                            str(row.get("stability_score", "")).strip()
                        ),
                        stability_penalty=float(
                            str(row.get("stability_penalty", "")).strip()
                        ),
                        downgraded=_parse_cli_bool(
                            row.get("downgraded", ""),
                            field_name="downgraded",
                        ),
                        instability_reasons=tuple(
                            BiomarkerStabilityReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("instability_reasons", "")
                            )
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid stability row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_validation_evidence_redundancy_entries(
    path: Path,
) -> tuple[ValidationEvidenceRedundancyInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "redundancy TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "cluster_id",
            "representative_candidate_id",
            "representative",
            "dropped",
            "shared_sample_count",
            "max_redundant_correlation",
            "redundancy_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "redundancy TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceRedundancyInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceRedundancyInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        cluster_id=str(row.get("cluster_id", "")).strip(),
                        representative_candidate_id=str(
                            row.get("representative_candidate_id", "")
                        ).strip(),
                        representative=_parse_cli_bool(
                            row.get("representative", ""),
                            field_name="representative",
                        ),
                        dropped=_parse_cli_bool(
                            row.get("dropped", ""),
                            field_name="dropped",
                        ),
                        shared_sample_count=int(
                            str(row.get("shared_sample_count", "")).strip()
                        ),
                        max_redundant_correlation=(
                            None
                            if not str(row.get("max_redundant_correlation", "")).strip()
                            else float(
                                str(row.get("max_redundant_correlation", "")).strip()
                            )
                        ),
                        redundancy_reason_codes=_split_semicolon_field(
                            row.get("redundancy_reason_codes", "")
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid redundancy row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

def _load_targeted_validation_panel_assays(
    path: Path,
) -> tuple[TargetedValidationPanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel assay TSV must include a header row for targeted result validation"
            )
        required_columns = {
            "assay_entry_id",
            "biomarker_candidate_id",
            "biomarker_candidate_kind",
            "biomarker_display_label",
            "biomarker_priority_rank",
            "target_protein_ref",
            "target_protein_group_id",
            "gene_symbol",
            "peptide_sequence",
            "canonical_peptide",
            "uniqueness_class",
            "precursor_charge",
            "selected_transition_count",
            "exported_transition_count",
            "warning_codes",
            "warning_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "panel assay TSV is missing required columns for targeted result validation: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedValidationPanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                warning_codes = tuple(
                    TargetedPanelWarningCode(code)
                    for code in _split_semicolon_field(row.get("warning_codes", ""))
                )
                rows.append(
                    TargetedValidationPanelAssayInput(
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        biomarker_candidate_id=str(
                            row.get("biomarker_candidate_id", "")
                        ).strip(),
                        biomarker_candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("biomarker_candidate_kind", "")).strip()
                        ),
                        biomarker_display_label=str(
                            row.get("biomarker_display_label", "")
                        ).strip(),
                        biomarker_priority_rank=int(
                            str(row.get("biomarker_priority_rank", "")).strip()
                        ),
                        target_protein_ref=str(row.get("target_protein_ref", "")).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(
                            row.get("canonical_peptide", "")
                        ).strip(),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        selected_transition_count=int(
                            str(row.get("selected_transition_count", "")).strip()
                        ),
                        exported_transition_count=int(
                            str(row.get("exported_transition_count", "")).strip()
                        ),
                        warning_codes=warning_codes,
                        warning_note=str(row.get("warning_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid panel assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

__all__ = [name for name in globals() if not name.startswith("__")]
