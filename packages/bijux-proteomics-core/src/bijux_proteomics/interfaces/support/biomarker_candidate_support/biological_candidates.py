# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Biological report biomarker candidate loaders."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_protein_id
from bijux_proteomics.io.tables import (
    DelimitedLookupJoinSpec,
    iter_delimited_rows,
    iter_streaming_lookup_join,
)

from ..foundation import Path, click
from ..review_sequences_study import (
    BiomarkerCandidateKind,
    BiomarkerCandidateRankingInput,
)
from ..targeted_selection_io.field_parsing import _split_semicolon_field
from ..targeted_selection_io.report_artifacts import (
    _read_summary_field_map,
    _require_report_artifact,
)
from .candidate_scoring import (
    _score_annotation_labels,
    _score_effect_size,
    _score_protein_assay_feasibility,
    _score_protein_detectability,
    _score_protein_specificity,
)
from .lookup_joins import _require_joined_row


def _build_biomarker_candidates_from_biological_report_dir(
    report_dir: Path,
    *,
    selected_peptide_support: dict[str, dict[str, float]] | None,
    assay_interference_support: dict[str, dict[str, float | bool]] | None,
) -> tuple[tuple[BiomarkerCandidateRankingInput, ...], float]:
    summary_path = _require_report_artifact(
        report_dir,
        "biological_report_summary.tsv",
        description="biological report directory",
    )
    card_path = _require_report_artifact(
        report_dir,
        "biological_protein_cards.tsv",
        description="biological report directory",
    )
    differential_path = _require_report_artifact(
        report_dir,
        "biological_differential.tsv",
        description="biological report directory",
    )
    summary_fields = _read_summary_field_map(
        summary_path,
        description="biological report summary TSV",
    )
    sample_qc_score = float(summary_fields.get("experiment_confidence_score", "0.5"))
    candidates: list[BiomarkerCandidateRankingInput] = []
    required_columns = (
        "card_id",
        "protein_group_id",
        "representative_protein_ref",
        "gene_symbol",
        "identity_level",
        "unique_peptide_count",
        "shared_peptide_count",
        "evidence_tier",
        "pathway_ids",
        "context_ids",
        "functional_regions",
        "proteogenomic_support_class",
        "ptm_sites",
        "warning_codes",
    )
    lookup_specs = (
        DelimitedLookupJoinSpec(
            join_name="differential",
            path=differential_path,
            primary_key_columns=("protein_group_id",),
            lookup_key_columns=("entity_id",),
            required_lookup_columns=(
                "entity_id",
                "log2_fold_change",
                "adjusted_p_value",
                "robustness_score",
            ),
        ),
    )
    for joined in iter_streaming_lookup_join(
        card_path,
        lookup_specs=lookup_specs,
        required_primary_columns=required_columns,
    ):
        row_number = joined.row_number
        row = joined.primary_row
        try:
            protein_group_id = str(row.get("protein_group_id", "")).strip()
            differential_row = _require_joined_row(
                joined.joined_rows["differential"],
                row_label=f"protein_group_id {protein_group_id!r}",
                join_name="biological differential",
            )
            differential_entry = _parse_biological_differential_row(
                differential_row,
                row_number=row_number,
                path_name=differential_path.name,
            )
            protein_ref = str(row.get("representative_protein_ref", "")).strip()
            selected_support = (
                {}
                if selected_peptide_support is None
                else selected_peptide_support.get(protein_ref, {})
            )
            assay_support = (
                {}
                if assay_interference_support is None
                else assay_interference_support.get(protein_ref, {})
            )
            unique_count = int(str(row.get("unique_peptide_count", "")).strip())
            shared_count = int(str(row.get("shared_peptide_count", "")).strip())
            annotation_labels = tuple(
                label
                for label in (
                    _split_semicolon_field(row.get("pathway_ids", ""))
                    + _split_semicolon_field(row.get("context_ids", ""))
                    + _split_semicolon_field(row.get("functional_regions", ""))
                    + _split_semicolon_field(row.get("ptm_sites", ""))
                )
                if label
            )
            proteogenomic_support_class = str(
                row.get("proteogenomic_support_class", "")
            ).strip()
            if proteogenomic_support_class:
                annotation_labels += (f"proteogenomic:{proteogenomic_support_class}",)
            annotation_score = _score_annotation_labels(annotation_labels)
            specificity_score = _score_protein_specificity(
                unique_count=unique_count,
                shared_count=shared_count,
                identity_level=str(row.get("identity_level", "")).strip(),
                selected_uniqueness_score=float(
                    selected_support.get("uniqueness_score", 0.0)
                ),
            )
            detectability_score = _score_protein_detectability(
                selected_detectability_score=float(
                    selected_support.get("detectability_score", 0.0)
                ),
                unique_count=unique_count,
                evidence_tier=str(row.get("evidence_tier", "")).strip(),
            )
            assay_feasibility_score = _score_protein_assay_feasibility(
                selected_suitability_score=float(
                    selected_support.get("suitability_score", 0.0)
                ),
                detectability_score=detectability_score,
                assay_score=float(assay_support.get("assay_score", 0.0)),
            )
            support_count = max(unique_count, unique_count + shared_count)
            display_label = (
                value
                if (value := str(row.get("gene_symbol", "")).strip())
                else protein_ref
            )
            candidates.append(
                BiomarkerCandidateRankingInput(
                    candidate_id=build_protein_id(protein_group_id),
                    candidate_kind=BiomarkerCandidateKind.PROTEIN,
                    display_label=display_label,
                    target_protein_ref=protein_ref,
                    effect_size=differential_entry["log2_fold_change"],
                    adjusted_p_value=differential_entry["adjusted_p_value"],
                    support_count=support_count,
                    effect_score=_score_effect_size(
                        differential_entry["log2_fold_change"]
                    ),
                    robustness_score=differential_entry["robustness_score"],
                    detectability_score=detectability_score,
                    specificity_score=specificity_score,
                    annotation_score=annotation_score,
                    assay_feasibility_score=assay_feasibility_score,
                    sample_qc_score=sample_qc_score,
                    annotation_labels=annotation_labels,
                    source_ids=(
                        str(row.get("card_id", "")).strip(),
                        protein_group_id,
                    ),
                    note=(
                        "protein candidate ranking combines biological differential evidence "
                        "with targeted detectability and interference readiness"
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(
                f"invalid biological protein-card row {row_number} in {card_path.name!r}: {exc}"
            ) from exc
    return tuple(candidates), sample_qc_score


def _load_biological_differential_rows(
    path: Path,
) -> dict[str, dict[str, float | None]]:
    rows: dict[str, dict[str, float | None]] = {}
    try:
        for row_number, row in iter_delimited_rows(
            path,
            required_columns=(
                "entity_id",
                "log2_fold_change",
                "adjusted_p_value",
                "robustness_score",
            ),
        ):
            rows[str(row.get("entity_id", "")).strip()] = (
                _parse_biological_differential_row(
                    row,
                    row_number=row_number,
                    path_name=path.name,
                )
            )
    except ValueError as exc:
        raise click.ClickException(
            "biological differential TSV is missing required columns for biomarker candidate ranking: "
            + str(exc)
        ) from exc
    return rows


def _parse_biological_differential_row(
    row: dict[str, str],
    *,
    row_number: int,
    path_name: str,
) -> dict[str, float | None]:
    try:
        return {
            "log2_fold_change": float(str(row.get("log2_fold_change", "")).strip()),
            "adjusted_p_value": (
                None
                if not str(row.get("adjusted_p_value", "")).strip()
                else float(str(row.get("adjusted_p_value", "")).strip())
            ),
            "robustness_score": float(str(row.get("robustness_score", "")).strip()),
        }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(
            f"invalid biological differential row {row_number} in {path_name!r}: {exc}"
        ) from exc
