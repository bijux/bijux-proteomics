# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM report biomarker candidate loaders."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_site_id
from bijux_proteomics.io.tables import (
    DelimitedLookupJoinSpec,
    iter_delimited_rows,
    iter_streaming_lookup_join,
)

from ..imports import *  # noqa: F401,F403
from ..targeted_selection_io.field_parsing import _parse_cli_bool, _split_semicolon_field
from ..targeted_selection_io.report_artifacts import _require_report_artifact
from .candidate_scoring import (
    _score_annotation_labels,
    _score_effect_size,
    _score_ptm_assay_feasibility,
    _score_ptm_detectability,
    _score_ptm_robustness,
    _score_ptm_specificity,
)
from .lookup_joins import _require_joined_row


def _build_biomarker_candidates_from_ptm_report_dir(
    report_dir: Path,
    *,
    sample_qc_score: float | None,
) -> tuple[BiomarkerCandidateRankingInput, ...]:
    card_path = _require_report_artifact(
        report_dir,
        "ptm_evidence_cards.tsv",
        description="ptm report directory",
    )
    differential_path = _require_report_artifact(
        report_dir,
        "ptm_differential.tsv",
        description="ptm report directory",
    )
    active_sample_qc_score = 0.60 if sample_qc_score is None else sample_qc_score
    candidates: list[BiomarkerCandidateRankingInput] = []
    required_columns = (
        "card_id",
        "site_key",
        "protein_ref",
        "residue",
        "position",
        "modification_name",
        "identity_level",
        "localization_tier",
        "mechanism_class",
        "peptide_spectrum_count",
        "observed_sample_count",
        "centered_windows",
        "ortholog_conservation_status",
        "functional_regions",
        "regulators",
        "warning_codes",
    )
    lookup_specs = (
        DelimitedLookupJoinSpec(
            join_name="ptm_differential",
            path=differential_path,
            primary_key_columns=("site_key",),
            lookup_key_columns=("site_key",),
            required_lookup_columns=(
                "site_key",
                "low_localization",
                "ambiguous",
                "shared_peptide",
                "log2_fold_change",
                "adjusted_p_value",
                "imputation_dependent_hit",
                "protein_correction_status",
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
            site_key = str(row.get("site_key", "")).strip()
            differential_row = _require_joined_row(
                joined.joined_rows["ptm_differential"],
                row_label=f"site_key {site_key!r}",
                join_name="PTM differential",
            )
            differential_entry = _parse_ptm_differential_row(
                differential_row,
                row_number=row_number,
                path_name=differential_path.name,
            )
            annotation_labels = tuple(
                label
                for label in (
                    _split_semicolon_field(row.get("centered_windows", ""))
                    + _split_semicolon_field(row.get("functional_regions", ""))
                    + _split_semicolon_field(row.get("regulators", ""))
                )
                if label
            )
            ortholog_status = str(row.get("ortholog_conservation_status", "")).strip()
            if ortholog_status:
                annotation_labels += (f"ortholog:{ortholog_status}",)
            mechanism_class = str(row.get("mechanism_class", "")).strip()
            if mechanism_class:
                annotation_labels += (f"mechanism:{mechanism_class}",)
            peptide_spectrum_count = int(
                str(row.get("peptide_spectrum_count", "")).strip()
            )
            observed_sample_count = int(
                str(row.get("observed_sample_count", "")).strip()
            )
            specificity_score = _score_ptm_specificity(
                localization_tier=str(row.get("localization_tier", "")).strip(),
                identity_level=str(row.get("identity_level", "")).strip(),
                low_localization=bool(differential_entry["low_localization"]),
                ambiguous=bool(differential_entry["ambiguous"]),
                shared_peptide=bool(differential_entry["shared_peptide"]),
            )
            detectability_score = _score_ptm_detectability(
                peptide_spectrum_count=peptide_spectrum_count,
                observed_sample_count=observed_sample_count,
            )
            assay_feasibility_score = _score_ptm_assay_feasibility(
                specificity_score=specificity_score,
                warning_count=len(_split_semicolon_field(row.get("warning_codes", ""))),
                protein_correction_status=str(
                    differential_entry["protein_correction_status"]
                ),
            )
            display_label = (
                f"{row.get('protein_ref', '')} "
                f"{row.get('residue', '')}{row.get('position', '')} "
                f"{row.get('modification_name', '')}"
            ).strip()
            effect_size_raw = differential_entry["log2_fold_change"]
            adjusted_p_value_raw = differential_entry["adjusted_p_value"]
            if not isinstance(effect_size_raw, int | float):
                raise TypeError("PTM differential log2_fold_change must be numeric")
            if adjusted_p_value_raw is not None and not isinstance(
                adjusted_p_value_raw, int | float
            ):
                raise TypeError("PTM differential adjusted_p_value must be numeric")
            effect_size = float(effect_size_raw)
            adjusted_p_value = (
                None if adjusted_p_value_raw is None else float(adjusted_p_value_raw)
            )
            candidates.append(
                BiomarkerCandidateRankingInput(
                    candidate_id=build_site_id(
                        str(row.get("protein_ref", "")).strip(),
                        str(row.get("residue", "")).strip(),
                        int(str(row.get("position", "")).strip()),
                        str(row.get("modification_name", "")).strip(),
                    ),
                    candidate_kind=BiomarkerCandidateKind.PTM_SITE,
                    display_label=display_label,
                    target_protein_ref=str(row.get("protein_ref", "")).strip(),
                    site_key=site_key,
                    effect_size=effect_size,
                    adjusted_p_value=adjusted_p_value,
                    support_count=peptide_spectrum_count,
                    effect_score=_score_effect_size(effect_size),
                    robustness_score=_score_ptm_robustness(
                        adjusted_p_value=adjusted_p_value,
                        imputation_dependent=bool(
                            differential_entry["imputation_dependent_hit"]
                        ),
                        low_localization=bool(differential_entry["low_localization"]),
                        ambiguous=bool(differential_entry["ambiguous"]),
                    ),
                    detectability_score=detectability_score,
                    specificity_score=specificity_score,
                    annotation_score=_score_annotation_labels(annotation_labels),
                    assay_feasibility_score=assay_feasibility_score,
                    sample_qc_score=active_sample_qc_score,
                    annotation_labels=annotation_labels,
                    source_ids=(str(row.get("card_id", "")).strip(), site_key),
                    note=(
                        "PTM candidate ranking combines site differential evidence, "
                        "localization specificity, and validation practicality"
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(
                f"invalid PTM evidence-card row {row_number} in {card_path.name!r}: {exc}"
            ) from exc
    return tuple(candidates)


def _load_ptm_differential_rows(
    path: Path,
) -> dict[str, dict[str, float | str | bool | None]]:
    rows: dict[str, dict[str, float | str | bool | None]] = {}
    try:
        for row_number, row in iter_delimited_rows(
            path,
            required_columns=(
                "site_key",
                "low_localization",
                "ambiguous",
                "shared_peptide",
                "log2_fold_change",
                "adjusted_p_value",
                "imputation_dependent_hit",
                "protein_correction_status",
            ),
        ):
            rows[str(row.get("site_key", "")).strip()] = _parse_ptm_differential_row(
                row,
                row_number=row_number,
                path_name=path.name,
            )
    except ValueError as exc:
        raise click.ClickException(
            "ptm differential TSV is missing required columns for biomarker candidate ranking: "
            + str(exc)
        ) from exc
    return rows


def _parse_ptm_differential_row(
    row: dict[str, str],
    *,
    row_number: int,
    path_name: str,
) -> dict[str, float | str | bool | None]:
    try:
        return {
            "low_localization": _parse_cli_bool(
                row.get("low_localization", ""),
                field_name="low_localization",
            ),
            "ambiguous": _parse_cli_bool(
                row.get("ambiguous", ""),
                field_name="ambiguous",
            ),
            "shared_peptide": _parse_cli_bool(
                row.get("shared_peptide", ""),
                field_name="shared_peptide",
            ),
            "log2_fold_change": float(str(row.get("log2_fold_change", "")).strip()),
            "adjusted_p_value": (
                None
                if not str(row.get("adjusted_p_value", "")).strip()
                else float(str(row.get("adjusted_p_value", "")).strip())
            ),
            "imputation_dependent_hit": _parse_cli_bool(
                row.get("imputation_dependent_hit", ""),
                field_name="imputation_dependent_hit",
            ),
            "protein_correction_status": str(
                row.get("protein_correction_status", "")
            ).strip(),
        }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(
            f"invalid PTM differential row {row_number} in {path_name!r}: {exc}"
        ) from exc
