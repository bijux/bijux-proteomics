# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validation-planning TSV loaders for targeted support entrypoints."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics.targeted.validation_planning import (
    ValidationPlanningBiomarkerCandidateInput,
    ValidationPlanningOmittedCandidateInput,
    ValidationPlanningPanelAssayInput,
    ValidationPlanningPilotVarianceInput,
    ValidationPlanningSelectedPeptideInput,
)

from ..targeted_selection_io import _parse_cli_bool, _split_semicolon_field
from .panel_design import _load_targeted_panel_selected_peptides


def _load_validation_planning_biomarker_candidates(
    path: Path,
) -> tuple[ValidationPlanningBiomarkerCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for validation planning"
            )
        required_columns = {
            "candidate_id",
            "candidate_kind",
            "display_label",
            "target_protein_ref",
            "site_key",
            "priority_rank",
            "final_score",
            "penalty_total",
            "uncertainty",
            "effect_size",
            "adjusted_p_value",
            "support_count",
            "robustness_score",
            "assay_feasibility_score",
            "rank_reason_codes",
            "ranking_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningBiomarkerCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningBiomarkerCandidateInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("candidate_kind", "")).strip()
                        ),
                        display_label=str(row.get("display_label", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        site_key=(
                            None
                            if not str(row.get("site_key", "")).strip()
                            else str(row.get("site_key", "")).strip()
                        ),
                        priority_rank=int(str(row.get("priority_rank", "")).strip()),
                        final_score=float(str(row.get("final_score", "")).strip()),
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
                        robustness_score=float(
                            str(row.get("robustness_score", "")).strip()
                        ),
                        assay_feasibility_score=float(
                            str(row.get("assay_feasibility_score", "")).strip()
                        ),
                        rank_reason_codes=_split_semicolon_field(
                            row.get("rank_reason_codes", "")
                        ),
                        ranking_note=str(row.get("ranking_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biomarker-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_validation_planning_selected_peptides(
    path: Path,
) -> tuple[ValidationPlanningSelectedPeptideInput, ...]:
    return tuple(
        ValidationPlanningSelectedPeptideInput(
            target_protein_ref=entry.target_protein_ref,
            target_protein_group_id=entry.target_protein_group_id,
            gene_symbol=entry.gene_symbol,
            peptide_sequence=entry.peptide_sequence,
            canonical_peptide=entry.canonical_peptide,
            rank=entry.rank,
            observed_in_discovery=entry.observed_in_discovery,
            observed_psm_count=entry.observed_psm_count,
            run_count=entry.run_count,
            detection_frequency=entry.detection_frequency,
            replicate_consistency=entry.replicate_consistency,
            primary_evidence_class=entry.primary_evidence_class,
            uniqueness_class=entry.uniqueness_class,
            uniqueness_score=entry.uniqueness_score,
            detectability_score=entry.detectability_score,
            detectability_tier=entry.detectability_tier,
            suitability_score=entry.suitability_score,
            liability_tier=entry.liability_tier,
            liability_codes=entry.liability_codes,
        )
        for entry in _load_targeted_panel_selected_peptides(path)
    )


def _load_validation_planning_panel_assays(
    path: Path,
) -> tuple[ValidationPlanningPanelAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel assay TSV must include a header row for validation planning"
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
            "selected_transition_count",
            "exported_transition_count",
            "assay_interference_risk_tier",
            "warning_codes",
            "warning_note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "panel assay TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningPanelAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                warning_codes = tuple(
                    TargetedPanelWarningCode(code)
                    for code in _split_semicolon_field(row.get("warning_codes", ""))
                )
                rows.append(
                    ValidationPlanningPanelAssayInput(
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
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
                        target_protein_group_id=str(
                            row.get("target_protein_group_id", "")
                        ).strip(),
                        gene_symbol=(
                            None
                            if not str(row.get("gene_symbol", "")).strip()
                            else str(row.get("gene_symbol", "")).strip()
                        ),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        uniqueness_score=float(
                            str(row.get("uniqueness_score", "")).strip()
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
                        warning_codes=warning_codes,
                        warning_note=str(row.get("warning_note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid panel assay row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_validation_planning_omitted_candidates(
    path: Path,
) -> tuple[ValidationPlanningOmittedCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "panel omitted-candidate TSV must include a header row for validation planning"
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
                "panel omitted-candidate TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningOmittedCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningOmittedCandidateInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        candidate_kind=TargetedPanelCandidateKind(
                            str(row.get("candidate_kind", "")).strip()
                        ),
                        display_label=str(row.get("display_label", "")).strip(),
                        target_protein_ref=str(
                            row.get("target_protein_ref", "")
                        ).strip(),
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


def _load_validation_planning_pilot_variance(
    path: Path,
) -> tuple[ValidationPlanningPilotVarianceInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "power-variance TSV must include a header row for validation planning"
            )
        required_columns = {
            "entity_id",
            "protein_refs",
            "observed_sample_count",
            "missing_fraction",
            "contributing_condition_count",
            "used_global_variance_fallback",
            "pooled_log2_stddev",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "power-variance TSV is missing required columns for validation planning: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationPlanningPilotVarianceInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationPlanningPilotVarianceInput(
                        entity_id=str(row.get("entity_id", "")).strip(),
                        protein_refs=tuple(
                            value
                            for value in _split_semicolon_field(
                                row.get("protein_refs", "")
                            )
                            if value
                        ),
                        observed_sample_count=int(
                            str(row.get("observed_sample_count", "")).strip()
                        ),
                        missing_fraction=float(
                            str(row.get("missing_fraction", "")).strip()
                        ),
                        contributing_condition_count=int(
                            str(row.get("contributing_condition_count", "")).strip()
                        ),
                        used_global_variance_fallback=_parse_cli_bool(
                            row.get("used_global_variance_fallback", ""),
                            field_name="used_global_variance_fallback",
                        ),
                        pooled_log2_stddev=float(
                            str(row.get("pooled_log2_stddev", "")).strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid power-variance row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = [
    "_load_validation_planning_biomarker_candidates",
    "_load_validation_planning_omitted_candidates",
    "_load_validation_planning_panel_assays",
    "_load_validation_planning_pilot_variance",
    "_load_validation_planning_selected_peptides",
]
