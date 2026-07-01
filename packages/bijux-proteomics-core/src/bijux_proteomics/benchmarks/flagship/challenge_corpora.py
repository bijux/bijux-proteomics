# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship challenge corpora for blinded holdouts and adversarial perturbations."""

from __future__ import annotations

import csv
from enum import StrEnum
import json
from pathlib import Path
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.generalization.reports import (
    WorkflowGeneralizationReport,
    build_workflow_generalization_reports,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    build_ptm_ambiguity_propagation_benchmark_report,
    build_ptm_lab_targeting_rubric_report,
    build_ptm_localization_confidence_benchmark_report,
)
from bijux_proteomics.quantification.benchmarks import (
    MultiplexRatioExpectation,
    build_effect_size_stability_benchmark_report,
    build_multiplex_artifact_pressure_benchmark_report,
    build_quant_missingness_robustness_report,
)
from bijux_proteomics.quantification.contracts import (
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.quantification.contracts.input_models import (
    LabelBasedChannelRole,
    MissingChannelPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.label_based import (
    LabelBasedChannelPolicyEntry,
    LabelBasedQuantPolicy,
)
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryReport,
)
from bijux_proteomics.sequences.fasta import FastaParseMode, parse_fasta_document
from bijux_proteomics_foundation import JsonModel

_CHALLENGE_ROOT = (
    "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora"
)
_REGISTRY_PATH = f"{_CHALLENGE_ROOT}/challenge_registry.json"


class ChallengeKind(StrEnum):
    """Stable challenge families for flagship benchmark stress."""

    BLINDED_HOLDOUT = "blinded_holdout"
    PERTURBATION = "perturbation"


class HoldoutOutcomeState(StrEnum):
    """Revealed outcome after frozen surfaces are checked against holdout truth."""

    HIT = "hit"
    MISS = "miss"
    OVERCONFIDENT = "overconfident"
    UNDERCONFIDENT = "underconfident"


class PerturbationReactionState(StrEnum):
    """How one benchmark surface reacts under a stronger perturbation corpus."""

    SURVIVES = "survives"
    WEAKENS = "weakens"
    COLLAPSES = "collapses"


class HoldoutOutcomeFinding(JsonModel):
    """One blinded holdout finding after hidden truth is revealed."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    frozen_surface_paths: tuple[str, ...] = Field(default_factory=tuple)
    hidden_truth_summary: str = Field(..., min_length=1)
    revealed_outcome: HoldoutOutcomeState
    note: str = Field(..., min_length=1)


class BlindedHoldoutReport(JsonModel):
    """One blinded holdout report for a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    primary_package_id: str = Field(..., min_length=1)
    holdout_package_id: str = Field(..., min_length=1)
    frozen_surface_paths: tuple[str, ...] = Field(default_factory=tuple)
    withheld_truth_count: int = Field(..., ge=0)
    findings: tuple[HoldoutOutcomeFinding, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PerturbationMetricDelta(JsonModel):
    """One measurable before-versus-after change for a perturbation corpus."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(..., min_length=1)
    baseline_value: float
    perturbed_value: float
    delta: float
    interpretation: str = Field(..., min_length=1)


class PerturbationReactionReport(JsonModel):
    """One adversarial perturbation report over a flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    perturbation_axes: tuple[str, ...] = Field(default_factory=tuple)
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    workflow_reaction: PerturbationReactionState
    comparator_reaction: PerturbationReactionState
    review_reaction: PerturbationReactionState
    metric_deltas: tuple[PerturbationMetricDelta, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipChallengeEntry(JsonModel):
    """One durable challenge entry tracked in the product-owned registry."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    challenge_kind: ChallengeKind
    challenge_root: str = Field(..., min_length=1)
    manifest_path: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipChallengeRegistry(JsonModel):
    """Cross-family registry for flagship holdout and perturbation challenge roots."""

    model_config = ConfigDict(extra="forbid")

    registry_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipChallengeEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def flagship_challenge_root(challenge_dir_name: str) -> str:
    """Return the durable product-owned asset root for one flagship challenge."""

    return f"{_CHALLENGE_ROOT}/{challenge_dir_name}"


def flagship_challenge_registry_path() -> str:
    """Return the checked flagship challenge registry path."""

    return _REGISTRY_PATH


def _manifest_path(challenge_root: str) -> str:
    return f"{challenge_root}/challenge_manifest.json"


def _report_path(challenge_root: str, challenge_kind: ChallengeKind) -> str:
    file_name = (
        "blinded_holdout_report.json"
        if challenge_kind is ChallengeKind.BLINDED_HOLDOUT
        else "perturbation_report.json"
    )
    return f"{challenge_root}/{file_name}"


def _review_artifact_paths(package_manifest_path: str) -> tuple[str, ...]:
    manifest = json.loads(
        (_repo_root() / package_manifest_path).read_text(encoding="utf-8")
    )
    return tuple(manifest.get("expected_review_artifacts", ()))


def _generalization_reports_by_family() -> dict[str, WorkflowGeneralizationReport]:
    return {
        report.workflow_family: report
        for report in build_workflow_generalization_reports()
    }


def _blinded_holdout_root(workflow_family: str) -> str:
    return flagship_challenge_root(f"{workflow_family}_blinded_holdout")


def _perturbation_root(challenge_dir_name: str) -> str:
    return flagship_challenge_root(challenge_dir_name)


def _read_tsv_rows(repo_relative_path: str) -> list[dict[str, str]]:
    with (_repo_root() / repo_relative_path).open(
        newline="", encoding="utf-8"
    ) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _read_json_payload(repo_relative_path: str) -> dict[str, object]:
    payload = json.loads(
        (_repo_root() / repo_relative_path).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError(
            f"expected JSON object payload at {repo_relative_path}, found {type(payload).__name__}"
        )
    return cast(dict[str, object], payload)


def _require_object_mapping(
    payload: dict[str, object],
    key: str,
) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"expected object at key '{key}'")
    return cast(dict[str, object], value)


def _require_numeric_value(payload: dict[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"expected numeric value at key '{key}'")
    return float(value)


def _require_bool_value(payload: dict[str, object], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"expected boolean value at key '{key}'")
    return value


def _require_object_list(payload: dict[str, object], key: str) -> tuple[object, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"expected list value at key '{key}'")
    return tuple(value)


def _holdout_findings(
    report: WorkflowGeneralizationReport,
) -> tuple[HoldoutOutcomeFinding, ...]:
    findings: list[HoldoutOutcomeFinding] = []
    for finding in report.findings:
        if finding.state == "survives":
            outcome = HoldoutOutcomeState.HIT
            note = "the frozen benchmark and review surfaces stayed within the withheld claim boundary"
        elif finding.state == "weakens":
            outcome = HoldoutOutcomeState.OVERCONFIDENT
            note = "the hidden reveal showed that the frozen family claim was broader than the holdout package justifies"
        else:
            outcome = HoldoutOutcomeState.MISS
            note = "the hidden reveal showed that the frozen family claim does not survive the holdout package"
        findings.append(
            HoldoutOutcomeFinding(
                claim_id=finding.claim_id,
                frozen_surface_paths=(
                    report.package_manifest_paths[0],
                    report.package_manifest_paths[1],
                    report.artifact_path,
                ),
                hidden_truth_summary=finding.summary,
                revealed_outcome=outcome,
                note=note,
            )
        )
    return tuple(findings)


def _build_blinded_holdout_report(workflow_family: str) -> BlindedHoldoutReport:
    report = _generalization_reports_by_family()[workflow_family]
    challenge_root = _blinded_holdout_root(workflow_family)
    frozen_surface_paths = (
        report.package_manifest_paths
        + _review_artifact_paths(report.package_manifest_paths[0])
        + _review_artifact_paths(report.package_manifest_paths[1])
        + (report.artifact_path,)
    )
    return BlindedHoldoutReport(
        challenge_id=f"{workflow_family}-blinded-holdout",
        workflow_family=workflow_family,
        artifact_path=_report_path(challenge_root, ChallengeKind.BLINDED_HOLDOUT),
        primary_package_id=report.primary_package_id,
        holdout_package_id=report.secondary_package_id,
        frozen_surface_paths=frozen_surface_paths,
        withheld_truth_count=len(report.findings),
        findings=_holdout_findings(report),
        note=(
            "This blinded holdout report freezes the main reviewer-facing package surfaces first "
            "and only then reveals whether the hidden family-transfer findings still support the "
            "same workflow posture."
        ),
    )


def build_blinded_holdout_reports() -> tuple[BlindedHoldoutReport, ...]:
    """Return the current blinded holdout reports for flagship workflow families."""

    return tuple(
        _build_blinded_holdout_report(workflow_family)
        for workflow_family in ("dda", "dia", "lfq", "ptm")
    )


def _accepted_dda_counts(repo_relative_path: str) -> tuple[int, int, int]:
    accepted_target_count = 0
    accepted_decoy_count = 0
    accepted_contaminant_count = 0
    for row in _read_tsv_rows(repo_relative_path):
        if float(row["pep_value"]) > 0.01:
            continue
        proteins = row["leading_proteins"].strip()
        is_decoy = row["reverse_flag"].strip() == "+"
        is_contaminant = proteins.startswith("CON__")
        if is_decoy:
            accepted_decoy_count += 1
        elif is_contaminant:
            accepted_contaminant_count += 1
        else:
            accepted_target_count += 1
    return accepted_target_count, accepted_decoy_count, accepted_contaminant_count


def _accepted_dia_precursors(repo_relative_path: str) -> tuple[int, set[str]]:
    accepted = {
        row["Stripped.Sequence"].strip()
        for row in _read_tsv_rows(repo_relative_path)
        if int(row["Decoy"]) == 0 and float(row["Q.Value"]) <= 0.01
    }
    return len(accepted), accepted


def _spectronaut_peptides(repo_relative_path: str) -> set[str]:
    return {
        row["stripped_sequence"].strip()
        for row in _read_tsv_rows(repo_relative_path)
        if row["decoy_flag"].strip().lower() == "false"
    }


def _count_missing_values(summary_report: MissingValueSummaryReport) -> int:
    return sum(
        entry.zero_count + entry.not_observed_count + entry.filtered_count
        for entry in summary_report.entries
    )


def _observed_feature_row_count(
    repo_relative_path: str,
    *,
    sample_ids: set[str],
) -> int:
    return sum(
        1
        for row in _read_tsv_rows(repo_relative_path)
        if row["sample_id"] in sample_ids and row["intensity"].strip()
    )


def _multiplex_channel_policy(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> LabelBasedQuantPolicy:
    return LabelBasedQuantPolicy(
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
        channel_entries=tuple(
            LabelBasedChannelPolicyEntry(
                multiplex_group=entry.multiplex_group or "",
                multiplex_channel=entry.multiplex_channel or "",
                channel_role=(
                    LabelBasedChannelRole.CARRIER
                    if entry.sample_role == "pooled_reference"
                    else LabelBasedChannelRole.SAMPLE
                ),
            )
            for entry in design_entries
            if entry.multiplex_group and entry.multiplex_channel
        ),
    )


def _ptm_protein_sequences(repo_relative_fasta_path: str) -> dict[str, str]:
    fasta_report = parse_fasta_document(
        (_repo_root() / repo_relative_fasta_path).read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }


def _total_tic(repo_relative_path: str) -> float:
    return round(
        sum(float(row["tic"]) for row in _read_tsv_rows(repo_relative_path)),
        6,
    )


def _targeted_follow_up_summary(repo_relative_path: str) -> dict[str, float | bool]:
    payload = _read_json_payload(repo_relative_path)
    workflow_summary = _require_object_mapping(payload, "workflow_readiness_summary")
    handoff = _require_object_mapping(payload, "handoff_validation")
    transition_review = _require_object_mapping(payload, "transition_review")
    review_packet = _require_object_mapping(payload, "review_packet")
    executable_plan = _require_object_mapping(payload, "executable_plan")
    return {
        "ready_step_count": _require_numeric_value(
            workflow_summary, "ready_step_count"
        ),
        "blocked_step_count": _require_numeric_value(
            workflow_summary, "blocked_step_count"
        ),
        "accepted_assay_count": float(
            len(_require_object_list(handoff, "accepted_assay_ids"))
        ),
        "approved_transition_count": float(
            len(_require_object_list(transition_review, "approved_transition_ids"))
        ),
        "blocked_dependency_count": float(
            len(_require_object_list(executable_plan, "blocked_by"))
        ),
        "readiness_score": _require_numeric_value(transition_review, "readiness_score"),
        "accepted": _require_bool_value(handoff, "accepted"),
        "ready_for_synthesis": _require_bool_value(
            review_packet, "ready_for_synthesis"
        ),
    }


def _build_dda_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("dda_calibration_decoy_perturbation")
    baseline_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dda_reviewable_run/primary/maxquant_pipeline_export.tsv"
    )
    perturbed_path = f"{challenge_root}/evidence/perturbed_maxquant_pipeline_export.tsv"
    baseline_targets, baseline_decoys, baseline_contaminants = _accepted_dda_counts(
        baseline_path
    )
    perturbed_targets, perturbed_decoys, perturbed_contaminants = _accepted_dda_counts(
        perturbed_path
    )
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_targets < baseline_targets and perturbed_decoys > baseline_decoys
        else PerturbationReactionState.WEAKENS
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_contaminants > baseline_contaminants or perturbed_decoys > 0
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.WEAKENS
        if workflow_reaction is not PerturbationReactionState.SURVIVES
        else PerturbationReactionState.SURVIVES
    )
    return PerturbationReactionReport(
        challenge_id="dda-calibration-decoy-perturbation",
        workflow_family="dda",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "accepted-target loss",
            "accepted-decoy intrusion",
            "contaminant promotion",
        ),
        evidence_paths=(baseline_path, perturbed_path),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="accepted_target_count",
                baseline_value=float(baseline_targets),
                perturbed_value=float(perturbed_targets),
                delta=float(perturbed_targets - baseline_targets),
                interpretation="Fewer clean accepted targets means the DDA workflow loses stable identification support.",
            ),
            PerturbationMetricDelta(
                metric_id="accepted_decoy_count",
                baseline_value=float(baseline_decoys),
                perturbed_value=float(perturbed_decoys),
                delta=float(perturbed_decoys - baseline_decoys),
                interpretation="Accepted decoys force target-decoy and calibration claims back into downgrade territory.",
            ),
            PerturbationMetricDelta(
                metric_id="accepted_contaminant_count",
                baseline_value=float(baseline_contaminants),
                perturbed_value=float(perturbed_contaminants),
                delta=float(perturbed_contaminants - baseline_contaminants),
                interpretation="Contaminant promotion makes protein-facing review less trustworthy under the perturbation corpus.",
            ),
        ),
        note=(
            "This perturbation corpus worsens calibration and decoy behavior enough to show that DDA review claims must collapse back to refusal or stronger downgrade."
        ),
    )


def _build_dia_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("dia_library_dropout_perturbation")
    baseline_primary = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dia_matrix_shift_review_package/primary/diann_report.tsv"
    )
    baseline_comparator = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv"
    )
    perturbed_primary = f"{challenge_root}/evidence/perturbed_diann_report.tsv"
    perturbed_comparator = (
        f"{challenge_root}/evidence/perturbed_spectronaut_pipeline_export.tsv"
    )
    baseline_count, baseline_peptides = _accepted_dia_precursors(baseline_primary)
    perturbed_count, perturbed_peptides = _accepted_dia_precursors(perturbed_primary)
    baseline_overlap = len(
        baseline_peptides & _spectronaut_peptides(baseline_comparator)
    )
    perturbed_overlap = len(
        perturbed_peptides & _spectronaut_peptides(perturbed_comparator)
    )
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_count == 0
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_overlap == 0
        else PerturbationReactionState.WEAKENS
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if workflow_reaction is PerturbationReactionState.COLLAPSES
        and comparator_reaction is PerturbationReactionState.COLLAPSES
        else PerturbationReactionState.WEAKENS
    )
    return PerturbationReactionReport(
        challenge_id="dia-library-dropout-perturbation",
        workflow_family="dia",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "accepted-precursor dropout",
            "shared-peptide loss",
            "library-conditioned comparator shrinkage",
        ),
        evidence_paths=(
            baseline_primary,
            baseline_comparator,
            perturbed_primary,
            perturbed_comparator,
        ),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="accepted_precursor_count",
                baseline_value=float(baseline_count),
                perturbed_value=float(perturbed_count),
                delta=float(perturbed_count - baseline_count),
                interpretation="The perturbed DIA corpus loses accepted precursor support and becomes less reviewable.",
            ),
            PerturbationMetricDelta(
                metric_id="shared_peptide_overlap",
                baseline_value=float(baseline_overlap),
                perturbed_value=float(perturbed_overlap),
                delta=float(perturbed_overlap - baseline_overlap),
                interpretation="The comparator overlap shrinks when the perturbation removes library-conditioned peptide continuity.",
            ),
        ),
        note=(
            "This perturbation corpus worsens library-conditioned evidence enough to show where current DIA review posture collapses rather than merely weakens."
        ),
    )


def _build_lfq_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("lfq_missingness_drift_perturbation")
    baseline_feature_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv"
    )
    design_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "lfq_cohort_review_package/evidence/study_scale.design.tsv"
    )
    perturbed_feature_path = (
        f"{challenge_root}/evidence/perturbed_study_scale_ms1_features.tsv"
    )
    design_entries = parse_experimental_design_table(
        _repo_root() / design_path
    ).accepted_entries
    baseline_records = parse_ms1_feature_table(
        _repo_root() / baseline_feature_path
    ).accepted_records
    perturbed_records = parse_ms1_feature_table(
        _repo_root() / perturbed_feature_path
    ).accepted_records
    baseline_robustness = build_quant_missingness_robustness_report(
        baseline_records,
        design_entries=design_entries,
    )
    perturbed_robustness = build_quant_missingness_robustness_report(
        perturbed_records,
        design_entries=design_entries,
    )
    stability = build_effect_size_stability_benchmark_report(
        baseline_records,
        perturbed_records,
        design_entries=design_entries,
        condition_a="control",
        condition_b="treatment",
    )
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if not perturbed_robustness.robust_for_interpretation
        and stability.overlap_fraction < 0.5
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.WEAKENS
        if stability.overlap_fraction < 1.0
        else PerturbationReactionState.SURVIVES
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if not stability.stable_top_rank
        else PerturbationReactionState.WEAKENS
    )
    baseline_missing = _count_missing_values(baseline_robustness.missing_value_summary)
    perturbed_missing = _count_missing_values(
        perturbed_robustness.missing_value_summary
    )
    return PerturbationReactionReport(
        challenge_id="lfq-missingness-drift-perturbation",
        workflow_family="lfq",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "missing-value inflation",
            "batch-drift pressure",
            "differential narrative reshuffle",
        ),
        evidence_paths=(baseline_feature_path, design_path, perturbed_feature_path),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="missing_value_count",
                baseline_value=float(baseline_missing),
                perturbed_value=float(perturbed_missing),
                delta=float(perturbed_missing - baseline_missing),
                interpretation="Higher missing-value burden forces LFQ interpretation back toward bounded, downgrade-heavy claims.",
            ),
            PerturbationMetricDelta(
                metric_id="top_entity_overlap_fraction",
                baseline_value=1.0,
                perturbed_value=stability.overlap_fraction,
                delta=stability.overlap_fraction - 1.0,
                interpretation="The overlap fraction records whether the main LFQ differential story survives the perturbation corpus.",
            ),
        ),
        note=(
            "This perturbation corpus worsens missingness and batch drift enough to reveal whether LFQ effect-direction language remains stable or reshuffles under pressure."
        ),
    )


def _build_multiplex_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("multiplex_reference_bleed_perturbation")
    baseline_feature_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv"
    )
    design_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "multiplex_tmtpro_review_package/evidence/multiplex.design.tsv"
    )
    perturbed_feature_path = (
        f"{challenge_root}/evidence/perturbed_multiplex_ms1_features.tsv"
    )
    design_entries = parse_experimental_design_table(
        _repo_root() / design_path
    ).accepted_entries
    expected_ratios = (
        MultiplexRatioExpectation(
            numerator_sample_id="plex_a_126",
            denominator_sample_id="plex_a_127N",
            expected_ratio=1.0,
        ),
        MultiplexRatioExpectation(
            numerator_sample_id="plex_b_126",
            denominator_sample_id="plex_b_127N",
            expected_ratio=1.0,
        ),
    )
    baseline_table = build_label_free_intensity_table(
        parse_ms1_feature_table(_repo_root() / baseline_feature_path).accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    perturbed_table = build_label_free_intensity_table(
        parse_ms1_feature_table(_repo_root() / perturbed_feature_path).accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    baseline_artifact = build_multiplex_artifact_pressure_benchmark_report(
        baseline_table,
        design_entries=design_entries,
        expected_ratios=expected_ratios,
        interference_fraction_by_sample={
            "plex_a_126": 0.0,
            "plex_a_127N": 0.0,
            "plex_b_126": 0.0,
            "plex_b_127N": 0.0,
        },
        reporter_bleed_fraction_by_sample={
            "plex_a_126": 0.0,
            "plex_a_127N": 0.0,
            "plex_b_126": 0.0,
            "plex_b_127N": 0.0,
        },
    )
    perturbed_artifact = build_multiplex_artifact_pressure_benchmark_report(
        perturbed_table,
        design_entries=design_entries,
        expected_ratios=expected_ratios,
        interference_fraction_by_sample={
            "plex_a_126": 0.22,
            "plex_a_127N": 0.18,
            "plex_b_126": 0.21,
            "plex_b_127N": 0.17,
        },
        reporter_bleed_fraction_by_sample={
            "plex_a_127N": 0.19,
            "plex_b_127N": 0.16,
        },
    )
    reference_sample_ids = {"plex_a_128N", "plex_b_128N"}
    baseline_reference_rows = _observed_feature_row_count(
        baseline_feature_path,
        sample_ids=reference_sample_ids,
    )
    perturbed_reference_rows = _observed_feature_row_count(
        perturbed_feature_path,
        sample_ids=reference_sample_ids,
    )
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_artifact.materially_compressed_count
        > baseline_artifact.materially_compressed_count
        and perturbed_reference_rows == 0
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_artifact.interference_flagged_channel_count
        or perturbed_artifact.reporter_bleed_flagged_channel_count
        else PerturbationReactionState.SURVIVES
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if workflow_reaction is PerturbationReactionState.COLLAPSES
        else PerturbationReactionState.WEAKENS
    )
    return PerturbationReactionReport(
        challenge_id="multiplex-reference-bleed-perturbation",
        workflow_family="multiplex",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "reference dropout",
            "channel bleed",
            "carrier-conditioned ratio compression",
        ),
        evidence_paths=(baseline_feature_path, design_path, perturbed_feature_path),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="materially_compressed_ratio_count",
                baseline_value=float(baseline_artifact.materially_compressed_count),
                perturbed_value=float(perturbed_artifact.materially_compressed_count),
                delta=float(
                    perturbed_artifact.materially_compressed_count
                    - baseline_artifact.materially_compressed_count
                ),
                interpretation="More materially compressed ratios mean multiplex conclusions are no longer stable under bleed and carrier distortion pressure.",
            ),
            PerturbationMetricDelta(
                metric_id="reference_feature_row_count",
                baseline_value=float(baseline_reference_rows),
                perturbed_value=float(perturbed_reference_rows),
                delta=float(perturbed_reference_rows - baseline_reference_rows),
                interpretation="Reference-channel dropout removes the pooled anchor that the multiplex decision brief depends on.",
            ),
            PerturbationMetricDelta(
                metric_id="interference_or_bleed_flagged_channel_count",
                baseline_value=float(
                    baseline_artifact.interference_flagged_channel_count
                    + baseline_artifact.reporter_bleed_flagged_channel_count
                ),
                perturbed_value=float(
                    perturbed_artifact.interference_flagged_channel_count
                    + perturbed_artifact.reporter_bleed_flagged_channel_count
                ),
                delta=float(
                    perturbed_artifact.interference_flagged_channel_count
                    + perturbed_artifact.reporter_bleed_flagged_channel_count
                    - baseline_artifact.interference_flagged_channel_count
                    - baseline_artifact.reporter_bleed_flagged_channel_count
                ),
                interpretation="Flagged interference and bleed make channel-level and protein-level multiplex conclusions visibly unsafe.",
            ),
        ),
        note=(
            "This perturbation corpus combines reference dropout, bleed, and carrier distortion so multiplex claims collapse into bounded internal-support posture."
        ),
    )


def _build_ptm_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("ptm_ambiguity_occupancy_perturbation")
    baseline_localization_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "ptm_localization_review_package/evidence/localization_results.tsv"
    )
    baseline_feature_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "ptm_localization_review_package/evidence/ptm_features.tsv"
    )
    fasta_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "ptm_localization_review_package/evidence/ptm_sites.fasta"
    )
    perturbed_localization_path = (
        f"{challenge_root}/evidence/perturbed_localization_results.tsv"
    )
    perturbed_feature_path = f"{challenge_root}/evidence/perturbed_ptm_features.tsv"
    protein_sequences = _ptm_protein_sequences(fasta_path)
    baseline_localization = parse_ptm_localization_tsv(
        _repo_root() / baseline_localization_path
    )
    baseline_mappings = map_ptm_evidence_to_protein_sites(
        baseline_localization.accepted_records,
        protein_sequences=protein_sequences,
    )
    baseline_sites = build_ptm_site_table(baseline_mappings)
    baseline_features = parse_ms1_feature_table(
        _repo_root() / baseline_feature_path
    ).accepted_records
    perturbed_localization = parse_ptm_localization_tsv(
        _repo_root() / perturbed_localization_path
    )
    perturbed_mappings = map_ptm_evidence_to_protein_sites(
        perturbed_localization.accepted_records,
        protein_sequences=protein_sequences,
    )
    perturbed_sites = build_ptm_site_table(perturbed_mappings)
    perturbed_features = parse_ms1_feature_table(
        _repo_root() / perturbed_feature_path
    ).accepted_records
    fragment_support = {
        "scan=ptm-001": ("b5", "y6"),
        "scan=ptm-002": ("b4",),
    }
    baseline_confidence = build_ptm_localization_confidence_benchmark_report(
        baseline_localization.accepted_records,
        baseline_mappings,
        fragment_ion_support_by_spectrum=fragment_support,
    )
    perturbed_confidence = build_ptm_localization_confidence_benchmark_report(
        perturbed_localization.accepted_records,
        perturbed_mappings,
        fragment_ion_support_by_spectrum=fragment_support,
    )
    baseline_ambiguity = build_ptm_ambiguity_propagation_benchmark_report(
        baseline_sites,
        feature_records=baseline_features,
    )
    perturbed_ambiguity = build_ptm_ambiguity_propagation_benchmark_report(
        perturbed_sites,
        feature_records=perturbed_features,
    )
    perturbed_targeting = build_ptm_lab_targeting_rubric_report(
        perturbed_localization.accepted_records,
        perturbed_mappings,
        perturbed_sites,
        feature_records=perturbed_features,
    )
    baseline_confident_count = (
        baseline_confidence.decisive_count + baseline_confidence.supported_count
    )
    perturbed_confident_count = (
        perturbed_confidence.decisive_count + perturbed_confidence.supported_count
    )
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_confident_count == 0
        and perturbed_confidence.ambiguous_count > baseline_confidence.ambiguous_count
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.WEAKENS
        if perturbed_ambiguity.propagated_site_count
        > baseline_ambiguity.propagated_site_count
        else PerturbationReactionState.SURVIVES
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if workflow_reaction is PerturbationReactionState.COLLAPSES
        and perturbed_targeting.targetable_count == 0
        else PerturbationReactionState.WEAKENS
    )
    return PerturbationReactionReport(
        challenge_id="ptm-ambiguity-occupancy-perturbation",
        workflow_family="ptm",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "localization ambiguity",
            "occupancy instability",
            "targetability collapse",
        ),
        evidence_paths=(
            baseline_localization_path,
            baseline_feature_path,
            fasta_path,
            perturbed_localization_path,
            perturbed_feature_path,
        ),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="decisive_or_supported_site_count",
                baseline_value=float(baseline_confident_count),
                perturbed_value=float(perturbed_confident_count),
                delta=float(perturbed_confident_count - baseline_confident_count),
                interpretation="Losing decisive and supported PTM sites removes the narrow set of localization claims the package could previously defend.",
            ),
            PerturbationMetricDelta(
                metric_id="ambiguous_site_count",
                baseline_value=float(baseline_confidence.ambiguous_count),
                perturbed_value=float(perturbed_confidence.ambiguous_count),
                delta=float(
                    perturbed_confidence.ambiguous_count
                    - baseline_confidence.ambiguous_count
                ),
                interpretation="More ambiguous sites make PTM localization and occupancy conclusions visibly less credible.",
            ),
            PerturbationMetricDelta(
                metric_id="ambiguity_propagated_site_count",
                baseline_value=float(baseline_ambiguity.propagated_site_count),
                perturbed_value=float(perturbed_ambiguity.propagated_site_count),
                delta=float(
                    perturbed_ambiguity.propagated_site_count
                    - baseline_ambiguity.propagated_site_count
                ),
                interpretation="When ambiguity propagates into more occupancy sites, targetability language must stay interpretive-only.",
            ),
        ),
        note=(
            "This perturbation corpus worsens localization ambiguity and occupancy fragility enough to collapse PTM conclusions back to interpretive-only posture."
        ),
    )


def _build_targeted_perturbation_report() -> PerturbationReactionReport:
    challenge_root = _perturbation_root("targeted_interference_carryover_perturbation")
    baseline_qc_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv"
    )
    baseline_follow_up_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "targeted_transition_review_package/follow_up/supported_targeted_follow_up.json"
    )
    perturbed_qc_path = f"{challenge_root}/evidence/perturbed_targeted_benchmark_qc.tsv"
    perturbed_follow_up_path = (
        f"{challenge_root}/follow_up/perturbed_supported_targeted_follow_up.json"
    )
    baseline_qc_tic = _total_tic(baseline_qc_path)
    perturbed_qc_tic = _total_tic(perturbed_qc_path)
    baseline_follow_up = _targeted_follow_up_summary(baseline_follow_up_path)
    perturbed_follow_up = _targeted_follow_up_summary(perturbed_follow_up_path)
    workflow_reaction = (
        PerturbationReactionState.COLLAPSES
        if perturbed_follow_up["approved_transition_count"] == 0.0
        and perturbed_follow_up["readiness_score"]
        < baseline_follow_up["readiness_score"]
        else PerturbationReactionState.WEAKENS
    )
    comparator_reaction = (
        PerturbationReactionState.WEAKENS
        if perturbed_qc_tic < baseline_qc_tic
        else PerturbationReactionState.SURVIVES
    )
    review_reaction = (
        PerturbationReactionState.COLLAPSES
        if not perturbed_follow_up["accepted"]
        and not perturbed_follow_up["ready_for_synthesis"]
        else PerturbationReactionState.WEAKENS
    )
    return PerturbationReactionReport(
        challenge_id="targeted-interference-carryover-perturbation",
        workflow_family="targeted",
        artifact_path=_report_path(challenge_root, ChallengeKind.PERTURBATION),
        perturbation_axes=(
            "calibrant drift",
            "transition interference",
            "carryover-blocked follow-up",
        ),
        evidence_paths=(
            baseline_qc_path,
            baseline_follow_up_path,
            perturbed_qc_path,
            perturbed_follow_up_path,
        ),
        workflow_reaction=workflow_reaction,
        comparator_reaction=comparator_reaction,
        review_reaction=review_reaction,
        metric_deltas=(
            PerturbationMetricDelta(
                metric_id="total_tic",
                baseline_value=baseline_qc_tic,
                perturbed_value=perturbed_qc_tic,
                delta=round(perturbed_qc_tic - baseline_qc_tic, 6),
                interpretation="Lower total ion current makes the quantitative surface visibly weaker before any targeted follow-up claims are promoted.",
            ),
            PerturbationMetricDelta(
                metric_id="approved_transition_count",
                baseline_value=float(baseline_follow_up["approved_transition_count"]),
                perturbed_value=float(perturbed_follow_up["approved_transition_count"]),
                delta=float(
                    perturbed_follow_up["approved_transition_count"]
                    - baseline_follow_up["approved_transition_count"]
                ),
                interpretation="Losing approved transitions collapses the narrow targeted handoff the supported packet previously justified.",
            ),
            PerturbationMetricDelta(
                metric_id="blocked_dependency_count",
                baseline_value=float(baseline_follow_up["blocked_dependency_count"]),
                perturbed_value=float(perturbed_follow_up["blocked_dependency_count"]),
                delta=float(
                    perturbed_follow_up["blocked_dependency_count"]
                    - baseline_follow_up["blocked_dependency_count"]
                ),
                interpretation="More blocked dependencies expose how quickly targeted follow-up becomes execution-ineligible under interference and carryover pressure.",
            ),
        ),
        note=(
            "This perturbation corpus forces the targeted workflow from supported follow-up into blocked execution posture under calibrant drift, interference, and carryover pressure."
        ),
    )


def build_perturbation_reports() -> tuple[PerturbationReactionReport, ...]:
    """Return the currently shipped perturbation reports."""

    return (
        _build_dda_perturbation_report(),
        _build_dia_perturbation_report(),
        _build_lfq_perturbation_report(),
        _build_multiplex_perturbation_report(),
        _build_ptm_perturbation_report(),
        _build_targeted_perturbation_report(),
    )


def build_flagship_challenge_registry() -> FlagshipChallengeRegistry:
    """Return the registry for flagship challenge-corpus assets."""

    entries = [
        FlagshipChallengeEntry(
            challenge_id=report.challenge_id,
            workflow_family=report.workflow_family,
            challenge_kind=ChallengeKind.BLINDED_HOLDOUT,
            challenge_root=_blinded_holdout_root(report.workflow_family),
            manifest_path=_manifest_path(_blinded_holdout_root(report.workflow_family)),
            report_path=report.artifact_path,
            note=(
                "This challenge root keeps frozen surfaces and revealed holdout outcomes together "
                "under a durable product-owned path."
            ),
        )
        for report in build_blinded_holdout_reports()
    ]
    entries.extend(
        FlagshipChallengeEntry(
            challenge_id=report.challenge_id,
            workflow_family=report.workflow_family,
            challenge_kind=ChallengeKind.PERTURBATION,
            challenge_root=report.artifact_path.rsplit("/", 1)[0],
            manifest_path=_manifest_path(report.artifact_path.rsplit("/", 1)[0]),
            report_path=report.artifact_path,
            note=(
                "This challenge root keeps the perturbed corpus and the measured workflow reaction together "
                "under a durable product-owned path."
            ),
        )
        for report in build_perturbation_reports()
    )
    return FlagshipChallengeRegistry(
        registry_id="flagship-challenge-registry",
        artifact_path=_REGISTRY_PATH,
        entries=tuple(entries),
        note=(
            "The flagship challenge registry keeps blinded holdouts and adversarial perturbation "
            "corpora visible as product evidence instead of test-only sidecars."
        ),
    )


__all__ = [
    "BlindedHoldoutReport",
    "ChallengeKind",
    "FlagshipChallengeEntry",
    "FlagshipChallengeRegistry",
    "HoldoutOutcomeFinding",
    "HoldoutOutcomeState",
    "PerturbationMetricDelta",
    "PerturbationReactionReport",
    "PerturbationReactionState",
    "build_blinded_holdout_reports",
    "build_flagship_challenge_registry",
    "build_perturbation_reports",
    "flagship_challenge_registry_path",
    "flagship_challenge_root",
]
