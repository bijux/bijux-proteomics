# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Iteration-04 identification, FDR, and inference capability surfaces."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    ParsimonyVariant,
    PsmRecord,
    ConfidenceLabel,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    assign_razor_peptides,
    build_confidence_threshold_sensitivity_report,
    build_grouped_confidence_report,
    build_peptide_protein_trace_report,
    build_protein_groups,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    infer_proteins_by_parsimony,
    normalize_psm_score_orientation,
    validate_target_decoy_accession_collisions,
    validate_target_decoy_policy,
)
from bijux_proteomics_foundation import JsonModel


class TargetDecoyStrategyKind(StrEnum):
    """Supported target-decoy confidence strategies."""

    CONCATENATED = "concatenated"
    SEPARATE = "separate"
    PICKED = "picked"
    ENTRAPMENT = "entrapment"
    CUSTOM = "custom"
    NO_DECOY = "no_decoy"


class TargetDecoyStrategyDefinition(JsonModel):
    """One strategy definition inside the target-decoy registry."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: TargetDecoyStrategyKind
    display_name: str = Field(..., min_length=1)
    supports_psm: bool = True
    supports_peptide: bool = True
    supports_protein: bool = True
    supports_ptm: bool = False
    supports_group: bool = False
    requires_decoy_channel: bool = True
    reproducibility_notes: tuple[str, ...] = Field(default_factory=tuple)
    cautionary_notes: tuple[str, ...] = Field(default_factory=tuple)


class TargetDecoyStrategyRegistry(JsonModel):
    """Stable registry over supported target-decoy confidence strategies."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[TargetDecoyStrategyDefinition, ...] = Field(default_factory=tuple)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


def _default_target_decoy_strategy_definitions() -> tuple[TargetDecoyStrategyDefinition, ...]:
    return (
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.CONCATENATED,
            display_name="Concatenated target-decoy",
            supports_ptm=True,
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "record target and decoy hits in one ranked list with fixed score orientation",
                "persist tie-handling and threshold policy alongside accepted evidence",
            ),
            cautionary_notes=(
                "mixing independently filtered runs can invalidate concatenated ranking assumptions",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.SEPARATE,
            display_name="Separate target and decoy searches",
            supports_ptm=True,
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "store per-run target and decoy score distributions before merge",
                "normalize separate-run score scales before computing q-values",
            ),
            cautionary_notes=(
                "unscaled score distributions can bias separate-search confidence estimates",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.PICKED,
            display_name="Picked protein strategy",
            supports_group=True,
            requires_decoy_channel=True,
            reproducibility_notes=(
                "retain target/decoy competition outcomes at the protein accession level",
            ),
            cautionary_notes=(
                "picked strategy assumes deterministic target-decoy accession pairing",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.ENTRAPMENT,
            display_name="Entrapment-aware strategy",
            supports_group=True,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "capture entrapment set composition and accession versioning",
                "separate entrapment-derived calibration from primary q-value thresholds",
            ),
            cautionary_notes=(
                "entrapment references must remain disjoint from biological targets",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.CUSTOM,
            display_name="Custom confidence strategy",
            supports_group=True,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "declare custom confidence formula inputs and deterministic ordering keys",
            ),
            cautionary_notes=(
                "custom strategies require explicit validation before reuse across studies",
            ),
        ),
        TargetDecoyStrategyDefinition(
            strategy_kind=TargetDecoyStrategyKind.NO_DECOY,
            display_name="No-decoy advisory strategy",
            supports_psm=True,
            supports_peptide=True,
            supports_protein=False,
            supports_ptm=False,
            supports_group=False,
            requires_decoy_channel=False,
            reproducibility_notes=(
                "report confidence as advisory and avoid hard biological acceptance claims",
            ),
            cautionary_notes=(
                "missing decoy evidence prevents comparative FDR validation",
            ),
        ),
    )


def build_target_decoy_strategy_registry(
    *,
    custom_entries: tuple[TargetDecoyStrategyDefinition, ...] = (),
) -> TargetDecoyStrategyRegistry:
    """Build the stable target-decoy strategy registry with optional custom entries."""
    entries_by_kind = {
        entry.strategy_kind: entry
        for entry in _default_target_decoy_strategy_definitions()
    }
    for entry in custom_entries:
        entries_by_kind[entry.strategy_kind] = entry
    entries = tuple(sorted(entries_by_kind.values(), key=lambda entry: entry.strategy_kind.value))
    payload = [entry.to_dict() for entry in entries]
    reproducibility_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return TargetDecoyStrategyRegistry(
        entries=entries,
        reproducibility_hash=reproducibility_hash,
    )


class EmpiricalScoreCalibrationBin(JsonModel):
    """One empirical score bin over normalized target-decoy evidence."""

    model_config = ConfigDict(extra="forbid")

    bin_index: int = Field(..., ge=1)
    lower_bound: float = Field(..., ge=0.0, le=1.0)
    upper_bound: float = Field(..., ge=0.0, le=1.0)
    total_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    decoy_fraction: float = Field(..., ge=0.0)


class EmpiricalScoreCalibrationReport(JsonModel):
    """Empirical score calibration summary across normalized ranking bins."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    total_records: int = Field(..., ge=0)
    bin_count: int = Field(..., ge=1)
    bins: tuple[EmpiricalScoreCalibrationBin, ...] = Field(default_factory=tuple)
    top_fraction: float = Field(..., ge=0.01, le=1.0)
    top_fraction_target_share: float = Field(..., ge=0.0, le=1.0)
    top_fraction_decoy_share: float = Field(..., ge=0.0, le=1.0)
    advisory: str = Field(..., min_length=1)


def build_empirical_score_calibration_report(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
    top_fraction: float = 0.1,
) -> EmpiricalScoreCalibrationReport:
    """Build empirical score calibration distributions and advisory context."""
    if bin_count < 1:
        raise ValueError("bin_count must be at least 1")
    if top_fraction < 0.01 or top_fraction > 1.0:
        raise ValueError("top_fraction must be between 0.01 and 1.0")
    normalized = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    total = len(normalized)
    buckets: list[list[tuple[TargetDecoyLabel, float]]] = [[] for _ in range(bin_count)]
    for entry in normalized:
        index = min(int(entry.normalized_score * bin_count), bin_count - 1)
        buckets[index].append((entry.target_decoy_label, entry.normalized_score))
    bins: list[EmpiricalScoreCalibrationBin] = []
    for index, bucket in enumerate(buckets, start=1):
        target_count = sum(label is TargetDecoyLabel.TARGET for label, _ in bucket)
        decoy_count = sum(label is TargetDecoyLabel.DECOY for label, _ in bucket)
        mixed_count = sum(label is TargetDecoyLabel.MIXED for label, _ in bucket)
        unknown_count = sum(label is TargetDecoyLabel.UNKNOWN for label, _ in bucket)
        total_count = len(bucket)
        bins.append(
            EmpiricalScoreCalibrationBin(
                bin_index=index,
                lower_bound=(index - 1) / bin_count,
                upper_bound=index / bin_count,
                total_count=total_count,
                target_count=target_count,
                decoy_count=decoy_count,
                mixed_count=mixed_count,
                unknown_count=unknown_count,
                decoy_fraction=decoy_count / total_count if total_count else 0.0,
            )
        )
    top_count = max(1, int(total * top_fraction)) if total else 0
    top_ranked = normalized[:top_count]
    top_targets = sum(
        entry.target_decoy_label is TargetDecoyLabel.TARGET for entry in top_ranked
    )
    top_decoys = sum(
        entry.target_decoy_label is TargetDecoyLabel.DECOY for entry in top_ranked
    )
    if not top_ranked:
        advisory = "no records are available for empirical calibration"
    elif top_decoys == 0:
        advisory = (
            "top-ranked evidence is target-dominant; retain calibration snapshots to verify stability across runs"
        )
    else:
        advisory = (
            "top-ranked evidence includes decoys; confidence cutoffs should be reviewed before biological promotion"
        )
    return EmpiricalScoreCalibrationReport(
        score_orientation=score_orientation,
        total_records=total,
        bin_count=bin_count,
        bins=tuple(bins),
        top_fraction=top_fraction,
        top_fraction_target_share=top_targets / len(top_ranked) if top_ranked else 0.0,
        top_fraction_decoy_share=top_decoys / len(top_ranked) if top_ranked else 0.0,
        advisory=advisory,
    )


class ProteinInferenceStrategyKind(StrEnum):
    """Named strategy families for protein inference comparison."""

    PARSIMONY = "parsimony"
    RAZOR = "razor"
    PICKED = "picked"
    GROUPED = "grouped"
    CONSERVATIVE = "conservative"


class ProteinInferenceStrategySelection(JsonModel):
    """Selected proteins and rationale for one inference strategy."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: ProteinInferenceStrategyKind
    strategy_label: str = Field(..., min_length=1)
    selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    selected_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class ProteinInferenceStrategyComparisonEntry(JsonModel):
    """Pairwise overlap comparison between two inference strategies."""

    model_config = ConfigDict(extra="forbid")

    left_strategy: str = Field(..., min_length=1)
    right_strategy: str = Field(..., min_length=1)
    shared_proteins: tuple[str, ...] = Field(default_factory=tuple)
    left_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    right_only_proteins: tuple[str, ...] = Field(default_factory=tuple)
    jaccard_similarity: float = Field(..., ge=0.0, le=1.0)


class ProteinInferenceStrategyComparisonReport(JsonModel):
    """Stable comparison report across multiple inference strategies."""

    model_config = ConfigDict(extra="forbid")

    selections: tuple[ProteinInferenceStrategySelection, ...] = Field(
        default_factory=tuple
    )
    comparisons: tuple[ProteinInferenceStrategyComparisonEntry, ...] = Field(
        default_factory=tuple
    )


def compare_protein_inference_strategies(
    records: tuple[PsmRecord, ...],
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceStrategyComparisonReport:
    """Compare named protein inference strategies on one evidence fixture."""
    parsimony = tuple(
        sorted(
            {
                entry.protein_ref
                for entry in infer_proteins_by_parsimony(
                    records,
                    variant=ParsimonyVariant.GREEDY_COVERAGE,
                )
            }
        )
    )
    razor = tuple(
        sorted(
            {
                entry.assigned_protein
                for entry in assign_razor_peptides(records)
            }
        )
    )
    picked = tuple(
        sorted(
            {
                entry.protein_ref
                for entry in calculate_picked_protein_fdr(
                    records,
                    threshold=picked_threshold,
                )
                if entry.accepted and entry.target_decoy_label is not TargetDecoyLabel.DECOY
            }
        )
    )
    grouped = tuple(
        sorted({group.representative_protein for group in build_protein_groups(records)})
    )
    conservative = tuple(
        sorted(
            {
                group.representative_protein
                for group in build_protein_groups(records)
                if group.unique_peptide_count > 0
            }
        )
    )
    selections = (
        ProteinInferenceStrategySelection(
            strategy_kind=ProteinInferenceStrategyKind.PARSIMONY,
            strategy_label="parsimony:greedy_coverage",
            selected_proteins=parsimony,
            selected_count=len(parsimony),
            note="greedy parsimony selects a minimal explaining set from grouped evidence",
        ),
        ProteinInferenceStrategySelection(
            strategy_kind=ProteinInferenceStrategyKind.RAZOR,
            strategy_label="razor",
            selected_proteins=razor,
            selected_count=len(razor),
            note="razor assigns shared peptides to one dominant protein candidate",
        ),
        ProteinInferenceStrategySelection(
            strategy_kind=ProteinInferenceStrategyKind.PICKED,
            strategy_label="picked",
            selected_proteins=picked,
            selected_count=len(picked),
            note="picked competition keeps only target winners against decoy partners",
        ),
        ProteinInferenceStrategySelection(
            strategy_kind=ProteinInferenceStrategyKind.GROUPED,
            strategy_label="grouped",
            selected_proteins=grouped,
            selected_count=len(grouped),
            note="grouped strategy reports all representative proteins from indistinguishable groups",
        ),
        ProteinInferenceStrategySelection(
            strategy_kind=ProteinInferenceStrategyKind.CONSERVATIVE,
            strategy_label="conservative_unique_only",
            selected_proteins=conservative,
            selected_count=len(conservative),
            note="conservative strategy retains only groups with unique peptide evidence",
        ),
    )
    comparisons: list[ProteinInferenceStrategyComparisonEntry] = []
    for left_index, left in enumerate(selections):
        for right in selections[left_index + 1 :]:
            left_set = set(left.selected_proteins)
            right_set = set(right.selected_proteins)
            intersection = left_set & right_set
            union = left_set | right_set
            comparisons.append(
                ProteinInferenceStrategyComparisonEntry(
                    left_strategy=left.strategy_label,
                    right_strategy=right.strategy_label,
                    shared_proteins=tuple(sorted(intersection)),
                    left_only_proteins=tuple(sorted(left_set - right_set)),
                    right_only_proteins=tuple(sorted(right_set - left_set)),
                    jaccard_similarity=(len(intersection) / len(union)) if union else 1.0,
                )
            )
    return ProteinInferenceStrategyComparisonReport(
        selections=selections,
        comparisons=tuple(comparisons),
    )


class PsmPeptideProteinTraceBundle(JsonModel):
    """Trace bundle that keeps protein decisions explainable from PSM evidence."""

    model_config = ConfigDict(extra="forbid")

    trace_entry_count: int = Field(..., ge=0)
    distinct_psm_count: int = Field(..., ge=0)
    distinct_peptide_count: int = Field(..., ge=0)
    distinct_protein_count: int = Field(..., ge=0)
    trace_hash: str = Field(..., min_length=64, max_length=64)
    trace_rows: tuple[dict[str, object], ...] = Field(default_factory=tuple)


def build_psm_peptide_protein_trace_bundle(
    records: tuple[PsmRecord, ...],
) -> PsmPeptideProteinTraceBundle:
    """Build a stable PSM-to-peptide-to-protein decision trace bundle."""
    trace_report = build_peptide_protein_trace_report(records)
    trace_rows = tuple(entry.to_dict() for entry in trace_report.entries)
    payload = json.dumps(trace_rows, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    psm_ids = {
        str(spectrum_id)
        for row in trace_rows
        for spectrum_id in row.get("spectrum_ids", [])
    }
    peptides = {row["canonical_peptide"] for row in trace_rows}
    proteins = {
        protein
        for row in trace_rows
        for protein in row.get("protein_refs", ())
    }
    return PsmPeptideProteinTraceBundle(
        trace_entry_count=len(trace_rows),
        distinct_psm_count=len(psm_ids),
        distinct_peptide_count=len(peptides),
        distinct_protein_count=len(proteins),
        trace_hash=hashlib.sha256(payload).hexdigest(),
        trace_rows=trace_rows,
    )


def export_psm_peptide_protein_trace_bundle(
    bundle: PsmPeptideProteinTraceBundle,
    destination: Path,
) -> None:
    """Write a JSON export of the trace bundle for scientific review."""
    destination.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


class ConfidenceThresholdBundleEntry(JsonModel):
    """Accepted evidence snapshot at one explicit confidence threshold."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0, le=1.0)
    accepted_psm_count: int = Field(..., ge=0)
    accepted_peptide_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    newly_accepted_psm_count: int = Field(..., ge=0)
    newly_accepted_peptide_count: int = Field(..., ge=0)
    newly_accepted_protein_count: int = Field(..., ge=0)


class ConfidenceThresholdSensitivityBundle(JsonModel):
    """Cross-threshold confidence bundle for review and inference reproducibility."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    entries: tuple[ConfidenceThresholdBundleEntry, ...] = Field(default_factory=tuple)
    source_reproducibility_hash: str = Field(..., min_length=64, max_length=64)


def build_confidence_threshold_sensitivity_bundle(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    thresholds: tuple[float, ...] = (0.001, 0.01, 0.05, 0.1),
) -> ConfidenceThresholdSensitivityBundle:
    """Build a reproducible multi-threshold confidence snapshot bundle."""
    sensitivity = build_confidence_threshold_sensitivity_report(
        records,
        thresholds=thresholds,
        score_orientation=score_orientation,
    )
    entries: list[ConfidenceThresholdBundleEntry] = []
    previous_psm_ids: set[str] = set()
    previous_peptides: set[str] = set()
    previous_proteins: set[str] = set()
    for threshold in sensitivity.thresholds:
        level_report = calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        accepted_psms = {
            entry.entity_id for entry in level_report.psm_entries if entry.accepted
        }
        accepted_peptides = {
            entry.entity_id for entry in level_report.peptide_entries if entry.accepted
        }
        accepted_proteins = {
            entry.entity_id for entry in level_report.protein_entries if entry.accepted
        }
        entries.append(
            ConfidenceThresholdBundleEntry(
                threshold=threshold,
                accepted_psm_count=len(accepted_psms),
                accepted_peptide_count=len(accepted_peptides),
                accepted_protein_count=len(accepted_proteins),
                newly_accepted_psm_count=len(accepted_psms - previous_psm_ids),
                newly_accepted_peptide_count=len(
                    accepted_peptides - previous_peptides
                ),
                newly_accepted_protein_count=len(
                    accepted_proteins - previous_proteins
                ),
            )
        )
        previous_psm_ids = accepted_psms
        previous_peptides = accepted_peptides
        previous_proteins = accepted_proteins
    payload = {
        "score_orientation": score_orientation,
        "thresholds": list(sensitivity.thresholds),
        "entries": [entry.to_dict() for entry in entries],
    }
    return ConfidenceThresholdSensitivityBundle(
        score_orientation=score_orientation,
        thresholds=sensitivity.thresholds,
        entries=tuple(entries),
        source_reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    )


class GroupedConfidenceCategory(StrEnum):
    """Category used to separate grouped confidence by protein evidence topology."""

    SINGLE_PROTEIN = "single_protein"
    PROTEIN_GROUP = "protein_group"
    PROTEIN_FAMILY = "protein_family"


class GroupedConfidenceSummaryEntry(JsonModel):
    """Summary metrics for one grouped-confidence category."""

    model_config = ConfigDict(extra="forbid")

    category: GroupedConfidenceCategory
    group_count: int = Field(..., ge=0)
    high_confidence_count: int = Field(..., ge=0)
    medium_confidence_count: int = Field(..., ge=0)
    low_confidence_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)


class GroupedConfidenceSummaryReport(JsonModel):
    """Grouped-confidence summary with explicit separation by evidence category."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[GroupedConfidenceSummaryEntry, ...] = Field(default_factory=tuple)


def build_grouped_confidence_summary_report(
    records: tuple[PsmRecord, ...],
) -> GroupedConfidenceSummaryReport:
    """Summarize grouped confidence by single proteins vs grouped/family evidence."""
    grouped = build_grouped_confidence_report(records)
    counters: dict[GroupedConfidenceCategory, dict[str, int]] = {
        category: {"group_count": 0, "high": 0, "medium": 0, "low": 0, "decoy": 0}
        for category in GroupedConfidenceCategory
    }
    for entry in grouped.entries:
        if len(entry.protein_refs) == 1 and entry.shared_peptide_count == 0:
            category = GroupedConfidenceCategory.SINGLE_PROTEIN
        elif entry.unique_peptide_count == 0:
            category = GroupedConfidenceCategory.PROTEIN_FAMILY
        else:
            category = GroupedConfidenceCategory.PROTEIN_GROUP
        counters[category]["group_count"] += 1
        if entry.confidence_label is ConfidenceLabel.HIGH:
            counters[category]["high"] += 1
        elif entry.confidence_label is ConfidenceLabel.MEDIUM:
            counters[category]["medium"] += 1
        elif entry.confidence_label is ConfidenceLabel.LOW:
            counters[category]["low"] += 1
        else:
            counters[category]["decoy"] += 1
    return GroupedConfidenceSummaryReport(
        entries=tuple(
            GroupedConfidenceSummaryEntry(
                category=category,
                group_count=data["group_count"],
                high_confidence_count=data["high"],
                medium_confidence_count=data["medium"],
                low_confidence_count=data["low"],
                decoy_count=data["decoy"],
            )
            for category, data in counters.items()
        )
    )


class CustomDecoyValidationReport(JsonModel):
    """Combined policy and collision validation for custom decoy construction."""

    model_config = ConfigDict(extra="forbid")

    valid: bool
    policy_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    collision_count: int = Field(..., ge=0)
    collision_accessions: tuple[str, ...] = Field(default_factory=tuple)
    risk_summary: str = Field(..., min_length=1)


def validate_custom_decoy_strategy(
    records: tuple[PsmRecord, ...],
    *,
    policy: TargetDecoyLabelPolicy,
) -> CustomDecoyValidationReport:
    """Validate custom decoy strategy and collision risks prior to FDR use."""
    sample_refs = tuple(
        sorted(
            {
                protein_ref
                for record in records
                for protein_ref in record.protein_refs
            }
        )
    )
    sample_labels = tuple(
        sorted(
            {
                record.target_decoy_label.value
                for record in records
                if record.target_decoy_label is not TargetDecoyLabel.UNKNOWN
            }
        )
    )
    policy_report = validate_target_decoy_policy(
        policy,
        sample_protein_refs=sample_refs,
        sample_explicit_labels=sample_labels,
    )
    collisions = validate_target_decoy_accession_collisions(
        records,
        decoy_policy=policy,
    )
    issue_codes = tuple(sorted(issue.code for issue in policy_report.issues))
    fatal_policy_issue = any(
        issue.severity == "error" or issue.code == "shared_base_accession_pairs"
        for issue in policy_report.issues
    )
    collision_accessions = tuple(
        sorted(collision.base_accession for collision in collisions.collisions)
    )
    valid = (not fatal_policy_issue) and collisions.valid
    if valid:
        risk_summary = (
            "custom decoy policy is internally consistent and no accession collisions were detected"
        )
    elif collision_accessions or "shared_base_accession_pairs" in issue_codes:
        risk_summary = (
            "custom decoy construction yields target-decoy accession collisions that must be resolved before FDR"
        )
    else:
        risk_summary = (
            "custom decoy policy has validation issues that should be resolved before confidence thresholds are applied"
        )
    return CustomDecoyValidationReport(
        valid=valid,
        policy_issue_codes=issue_codes,
        collision_count=len(collision_accessions),
        collision_accessions=collision_accessions,
        risk_summary=risk_summary,
    )
