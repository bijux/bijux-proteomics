# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Biomarker candidate scoring helpers shared by CLI command modules."""

from __future__ import annotations

from .imports import *  # noqa: F401,F403

from .targeted_selection_io import _parse_cli_bool, _read_summary_field_map, _require_report_artifact, _split_semicolon_field

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
    differential_by_entity = _load_biological_differential_rows(differential_path)
    candidates: list[BiomarkerCandidateRankingInput] = []
    with card_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biological protein-card TSV must include a header row"
            )
        required_columns = {
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
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biological protein-card TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        for row_number, row in enumerate(reader, start=2):
            try:
                protein_group_id = str(row.get("protein_group_id", "")).strip()
                differential_row = differential_by_entity.get(protein_group_id)
                if differential_row is None:
                    raise ValueError(
                        f"no differential row matched protein_group_id {protein_group_id!r}"
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
                        candidate_id=f"protein:{protein_group_id}",
                        candidate_kind=BiomarkerCandidateKind.PROTEIN,
                        display_label=display_label,
                        target_protein_ref=protein_ref,
                        effect_size=differential_row["log2_fold_change"],
                        adjusted_p_value=differential_row["adjusted_p_value"],
                        support_count=support_count,
                        effect_score=_score_effect_size(
                            differential_row["log2_fold_change"]
                        ),
                        robustness_score=differential_row["robustness_score"],
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
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biological differential TSV must include a header row"
            )
        required_columns = {
            "entity_id",
            "log2_fold_change",
            "adjusted_p_value",
            "robustness_score",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biological differential TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        rows: dict[str, dict[str, float | None]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                rows[str(row.get("entity_id", "")).strip()] = {
                    "log2_fold_change": float(
                        str(row.get("log2_fold_change", "")).strip()
                    ),
                    "adjusted_p_value": (
                        None
                        if not str(row.get("adjusted_p_value", "")).strip()
                        else float(str(row.get("adjusted_p_value", "")).strip())
                    ),
                    "robustness_score": float(
                        str(row.get("robustness_score", "")).strip()
                    ),
                }
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biological differential row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return rows

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
    differential_by_site = _load_ptm_differential_rows(differential_path)
    active_sample_qc_score = 0.60 if sample_qc_score is None else sample_qc_score
    candidates: list[BiomarkerCandidateRankingInput] = []
    with card_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException("ptm evidence-card TSV must include a header row")
        required_columns = {
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
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "ptm evidence-card TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        for row_number, row in enumerate(reader, start=2):
            try:
                site_key = str(row.get("site_key", "")).strip()
                differential_row = differential_by_site.get(site_key)
                if differential_row is None:
                    raise ValueError(f"no PTM differential row matched site_key {site_key!r}")
                annotation_labels = tuple(
                    label
                    for label in (
                        _split_semicolon_field(row.get("centered_windows", ""))
                        + _split_semicolon_field(row.get("functional_regions", ""))
                        + _split_semicolon_field(row.get("regulators", ""))
                    )
                    if label
                )
                ortholog_status = str(
                    row.get("ortholog_conservation_status", "")
                ).strip()
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
                    low_localization=bool(differential_row["low_localization"]),
                    ambiguous=bool(differential_row["ambiguous"]),
                    shared_peptide=bool(differential_row["shared_peptide"]),
                )
                detectability_score = _score_ptm_detectability(
                    peptide_spectrum_count=peptide_spectrum_count,
                    observed_sample_count=observed_sample_count,
                )
                assay_feasibility_score = _score_ptm_assay_feasibility(
                    specificity_score=specificity_score,
                    warning_count=len(
                        _split_semicolon_field(row.get("warning_codes", ""))
                    ),
                    protein_correction_status=str(
                        differential_row["protein_correction_status"]
                    ),
                )
                display_label = (
                    f"{row.get('protein_ref', '')} "
                    f"{row.get('residue', '')}{row.get('position', '')} "
                    f"{row.get('modification_name', '')}"
                ).strip()
                candidates.append(
                    BiomarkerCandidateRankingInput(
                        candidate_id=f"ptm_site:{site_key}",
                        candidate_kind=BiomarkerCandidateKind.PTM_SITE,
                        display_label=display_label,
                        target_protein_ref=str(row.get("protein_ref", "")).strip(),
                        site_key=site_key,
                        effect_size=float(differential_row["log2_fold_change"]),
                        adjusted_p_value=differential_row["adjusted_p_value"],
                        support_count=peptide_spectrum_count,
                        effect_score=_score_effect_size(
                            float(differential_row["log2_fold_change"])
                        ),
                        robustness_score=_score_ptm_robustness(
                            adjusted_p_value=differential_row["adjusted_p_value"],
                            imputation_dependent=bool(
                                differential_row["imputation_dependent_hit"]
                            ),
                            low_localization=bool(differential_row["low_localization"]),
                            ambiguous=bool(differential_row["ambiguous"]),
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
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException("ptm differential TSV must include a header row")
        required_columns = {
            "site_key",
            "low_localization",
            "ambiguous",
            "shared_peptide",
            "log2_fold_change",
            "adjusted_p_value",
            "imputation_dependent_hit",
            "protein_correction_status",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "ptm differential TSV is missing required columns for biomarker candidate ranking: "
                + ", ".join(sorted(missing_columns))
            )
        rows: dict[str, dict[str, float | str | bool | None]] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                rows[str(row.get("site_key", "")).strip()] = {
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
                    "log2_fold_change": float(
                        str(row.get("log2_fold_change", "")).strip()
                    ),
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
                    f"invalid PTM differential row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return rows

def _score_effect_size(log2_fold_change: float | None) -> float:
    if log2_fold_change is None:
        return 0.0
    return max(0.0, min(1.0, abs(log2_fold_change) / 2.0))

def _score_annotation_labels(annotation_labels: tuple[str, ...]) -> float:
    if not annotation_labels:
        return 0.0
    prefixes = {
        label.split(":", 1)[0] if ":" in label else label
        for label in annotation_labels
    }
    return max(0.0, min(1.0, len(prefixes) / 4.0))

def _score_protein_specificity(
    *,
    unique_count: int,
    shared_count: int,
    identity_level: str,
    selected_uniqueness_score: float,
) -> float:
    peptide_total = max(1, unique_count + shared_count)
    unique_fraction = unique_count / peptide_total
    base = max(unique_fraction, selected_uniqueness_score)
    identity_adjustment = {
        "isoform_level": 0.10,
        "protein_level": 0.0,
        "gene_level": -0.15,
        "family_level": -0.25,
        "ambiguous": -0.35,
    }.get(identity_level, 0.0)
    return max(0.0, min(1.0, base + identity_adjustment))

def _score_protein_detectability(
    *,
    selected_detectability_score: float,
    unique_count: int,
    evidence_tier: str,
) -> float:
    tier_score = {
        "high": 0.90,
        "moderate": 0.65,
        "low": 0.35,
        "warning": 0.25,
    }.get(evidence_tier, 0.40)
    return max(
        0.0,
        min(
            1.0,
            max(selected_detectability_score, 0.50 * min(1.0, unique_count / 2.0))
            + (0.25 * tier_score),
        ),
    )

def _score_protein_assay_feasibility(
    *,
    selected_suitability_score: float,
    detectability_score: float,
    assay_score: float,
) -> float:
    baseline = max(selected_suitability_score, 0.60 * detectability_score)
    if assay_score > 0.0:
        baseline = (0.45 * baseline) + (0.55 * assay_score)
    return max(0.0, min(1.0, baseline))

def _score_ptm_specificity(
    *,
    localization_tier: str,
    identity_level: str,
    low_localization: bool,
    ambiguous: bool,
    shared_peptide: bool,
) -> float:
    base = {
        "high": 0.90,
        "moderate": 0.65,
        "low": 0.30,
        "unsupported": 0.10,
    }.get(localization_tier, 0.40)
    if low_localization:
        base -= 0.20
    if ambiguous:
        base -= 0.15
    if shared_peptide:
        base -= 0.15
    if identity_level in {"gene_level", "family_level", "ambiguous"}:
        base -= 0.10
    return max(0.0, min(1.0, base))

def _score_ptm_detectability(
    *,
    peptide_spectrum_count: int,
    observed_sample_count: int,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            (0.60 * min(1.0, peptide_spectrum_count / 5.0))
            + (0.40 * min(1.0, observed_sample_count / 4.0)),
        ),
    )

def _score_ptm_assay_feasibility(
    *,
    specificity_score: float,
    warning_count: int,
    protein_correction_status: str,
) -> float:
    score = 0.70 * specificity_score
    if protein_correction_status == "corrected":
        score += 0.10
    score -= min(0.20, 0.05 * warning_count)
    return max(0.0, min(1.0, score))

def _score_ptm_robustness(
    *,
    adjusted_p_value: float | None,
    imputation_dependent: bool,
    low_localization: bool,
    ambiguous: bool,
) -> float:
    if adjusted_p_value is None:
        score = 0.25
    else:
        score = max(0.0, min(1.0, 1.0 - (adjusted_p_value / 0.10)))
    if imputation_dependent:
        score -= 0.20
    if low_localization:
        score -= 0.15
    if ambiguous:
        score -= 0.10
    return max(0.0, min(1.0, score))

def _load_biomarker_candidate_inputs(
    path: Path,
) -> tuple[TargetedPanelBiomarkerCandidateInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "biomarker-candidate TSV must include a header row for targeted panel building"
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
            "rank_reason_codes",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "biomarker-candidate TSV is missing required columns for targeted panel building: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[TargetedPanelBiomarkerCandidateInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    TargetedPanelBiomarkerCandidateInput(
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
                        penalty_total=float(str(row.get("penalty_total", "")).strip()),
                        rank_reason_codes=_split_semicolon_field(
                            row.get("rank_reason_codes", "")
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid biomarker-candidate row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)

__all__ = [name for name in globals() if not name.startswith("__")]
