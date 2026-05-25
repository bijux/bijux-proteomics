# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Identification, FDR, and inference capability surfaces."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    ConfidenceLabel,
    ParsimonyVariant,
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    assign_razor_peptides,
    build_confidence_threshold_sensitivity_report,
    build_grouped_confidence_report,
    build_peptide_protein_trace_report,
    build_protein_groups,
    calculate_basic_target_decoy_fdr,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    infer_proteins_by_parsimony,
    normalize_psm_score_orientation,
    validate_target_decoy_accession_collisions,
    validate_target_decoy_policy,
)
from bijux_proteomics.review.inference_packets import (
    InferenceDisagreementReviewEntry as InferenceDisagreementReviewEntry,
)
from bijux_proteomics.review.inference_packets import (
    InferenceDisagreementReviewPacket as InferenceDisagreementReviewPacket,
)
from bijux_proteomics.review.inference_packets import (
    InferenceDisagreementSeverity as InferenceDisagreementSeverity,
)
from bijux_proteomics.review.inference_packets import (
    build_inference_disagreement_review_packet as build_inference_disagreement_review_packet,
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


def _default_target_decoy_strategy_definitions() -> tuple[
    TargetDecoyStrategyDefinition, ...
]:
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
    entries = tuple(
        sorted(entries_by_kind.values(), key=lambda entry: entry.strategy_kind.value)
    )
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
    decoy_fraction_interval_low: float = Field(..., ge=0.0, le=1.0)
    decoy_fraction_interval_high: float = Field(..., ge=0.0, le=1.0)


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
    top_fraction_decoy_interval_low: float = Field(..., ge=0.0, le=1.0)
    top_fraction_decoy_interval_high: float = Field(..., ge=0.0, le=1.0)
    top_fraction_decoy_interval_width: float = Field(..., ge=0.0, le=1.0)
    advisory: str = Field(..., min_length=1)


def _wilson_interval(
    success_count: int,
    total_count: int,
    *,
    z_score: float = 1.96,
) -> tuple[float, float]:
    if total_count <= 0:
        return (0.0, 1.0)
    proportion = success_count / total_count
    z_squared = z_score * z_score
    denominator = 1.0 + (z_squared / total_count)
    center = (proportion + (z_squared / (2.0 * total_count))) / denominator
    margin = z_score * math.sqrt(
        (
            (proportion * (1.0 - proportion) / total_count)
            + (z_squared / (4.0 * total_count * total_count))
        )
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


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
            # Wilson intervals make calibration uncertainty quantitative instead of
            # leaving decoy fractions as point estimates only.
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
                decoy_fraction_interval_low=_wilson_interval(
                    decoy_count,
                    total_count,
                )[0],
                decoy_fraction_interval_high=_wilson_interval(
                    decoy_count,
                    total_count,
                )[1],
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
    top_decoy_interval = _wilson_interval(top_decoys, len(top_ranked))
    if not top_ranked:
        advisory = "no records are available for empirical calibration"
    elif top_decoys == 0:
        advisory = "top-ranked evidence is target-dominant; retain calibration snapshots to verify stability across runs"
    else:
        advisory = "top-ranked evidence includes decoys; confidence cutoffs should be reviewed before biological promotion"
    return EmpiricalScoreCalibrationReport(
        score_orientation=score_orientation,
        total_records=total,
        bin_count=bin_count,
        bins=tuple(bins),
        top_fraction=top_fraction,
        top_fraction_target_share=top_targets / len(top_ranked) if top_ranked else 0.0,
        top_fraction_decoy_share=top_decoys / len(top_ranked) if top_ranked else 0.0,
        top_fraction_decoy_interval_low=top_decoy_interval[0],
        top_fraction_decoy_interval_high=top_decoy_interval[1],
        top_fraction_decoy_interval_width=round(
            top_decoy_interval[1] - top_decoy_interval[0],
            4,
        ),
        advisory=advisory,
    )


class EntrapmentEvaluationReport(JsonModel):
    """Quantitative entrapment summary for calibration scrutiny."""

    model_config = ConfigDict(extra="forbid")

    entrapment_reference_count: int = Field(..., ge=0)
    matched_record_count: int = Field(..., ge=0)
    accepted_record_count: int = Field(..., ge=0)
    accepted_entrapment_count: int = Field(..., ge=0)
    accepted_entrapment_fraction: float = Field(..., ge=0.0, le=1.0)
    accepted_entrapment_interval_low: float = Field(..., ge=0.0, le=1.0)
    accepted_entrapment_interval_high: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


def build_entrapment_evaluation_report(
    records: tuple[PsmRecord, ...],
    *,
    entrapment_protein_refs: tuple[str, ...],
    accepted_q_value_threshold: float = 0.01,
) -> EntrapmentEvaluationReport:
    """Quantify entrapment hits instead of treating entrapment as prose-only support."""
    entrapment_set = {protein_ref.strip() for protein_ref in entrapment_protein_refs}
    matched_records = tuple(
        record for record in records if entrapment_set.intersection(record.protein_refs)
    )
    accepted_records = tuple(
        record
        for record in records
        if record.q_value is not None and record.q_value <= accepted_q_value_threshold
    )
    accepted_entrapment_count = sum(
        bool(entrapment_set.intersection(record.protein_refs))
        for record in accepted_records
    )
    interval = _wilson_interval(accepted_entrapment_count, len(accepted_records))
    note = (
        "accepted evidence includes entrapment-matched proteins and the calibration threshold should be reviewed"
        if accepted_entrapment_count > 0
        else "no accepted evidence matched the entrapment set under the requested threshold"
    )
    return EntrapmentEvaluationReport(
        entrapment_reference_count=len(entrapment_set),
        matched_record_count=len(matched_records),
        accepted_record_count=len(accepted_records),
        accepted_entrapment_count=accepted_entrapment_count,
        accepted_entrapment_fraction=(
            accepted_entrapment_count / len(accepted_records)
            if accepted_records
            else 0.0
        ),
        accepted_entrapment_interval_low=interval[0],
        accepted_entrapment_interval_high=interval[1],
        note=note,
    )


class FdrStressScenarioKind(StrEnum):
    """Stress scenarios that can expose over-trusted FDR summaries."""

    CLASS_IMBALANCED = "class_imbalanced"
    LOW_DECOY = "low_decoy"
    NO_DECOY = "no_decoy"


class FdrStressTrustState(StrEnum):
    """Trust posture for an FDR summary under stress."""

    FRAGILE = "fragile"
    REFUSED = "refused"
    TRUSTWORTHY = "trustworthy"


class FdrStressCaseReport(JsonModel):
    """Quantitative stress-case report for one target-decoy scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_kind: FdrStressScenarioKind
    total_record_count: int = Field(..., ge=0)
    accepted_record_count: int = Field(..., ge=0)
    accepted_decoy_count: int = Field(..., ge=0)
    accepted_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    accepted_decoy_interval_low: float = Field(..., ge=0.0, le=1.0)
    accepted_decoy_interval_high: float = Field(..., ge=0.0, le=1.0)
    trust_state: FdrStressTrustState
    note: str = Field(..., min_length=1)


def build_fdr_stress_case_report(
    records: tuple[PsmRecord, ...],
    *,
    scenario_kind: FdrStressScenarioKind,
    accepted_q_value_threshold: float = 0.01,
    low_decoy_cutoff: int = 2,
) -> FdrStressCaseReport:
    """Quantify whether stressed FDR conditions are trustworthy, fragile, or refused."""
    accepted_records = tuple(
        record
        for record in records
        if record.q_value is not None and record.q_value <= accepted_q_value_threshold
    )
    accepted_decoy_count = sum(
        record.target_decoy_label is TargetDecoyLabel.DECOY
        for record in accepted_records
    )
    total_decoy_count = sum(
        record.target_decoy_label is TargetDecoyLabel.DECOY for record in records
    )
    interval = _wilson_interval(accepted_decoy_count, len(accepted_records))
    if total_decoy_count == 0:
        trust_state = FdrStressTrustState.REFUSED
        note = "FDR trust is refused because no decoy evidence exists for the stressed scenario"
    elif scenario_kind is FdrStressScenarioKind.NO_DECOY:
        trust_state = FdrStressTrustState.REFUSED
        note = "FDR trust is refused because the scenario is explicitly no-decoy"
    elif total_decoy_count <= low_decoy_cutoff:
        trust_state = FdrStressTrustState.FRAGILE
        note = "FDR trust is fragile because too few decoys constrain the accepted-set estimate poorly"
    elif scenario_kind is FdrStressScenarioKind.CLASS_IMBALANCED and interval[1] > 0.2:
        trust_state = FdrStressTrustState.FRAGILE
        note = "FDR trust is fragile because class imbalance keeps accepted-set decoy uncertainty wide"
    else:
        trust_state = FdrStressTrustState.TRUSTWORTHY
        note = "FDR summary stays quantitatively bounded under the stressed scenario"
    return FdrStressCaseReport(
        scenario_kind=scenario_kind,
        total_record_count=len(records),
        accepted_record_count=len(accepted_records),
        accepted_decoy_count=accepted_decoy_count,
        accepted_decoy_fraction=(
            accepted_decoy_count / len(accepted_records) if accepted_records else 0.0
        ),
        accepted_decoy_interval_low=interval[0],
        accepted_decoy_interval_high=interval[1],
        trust_state=trust_state,
        note=note,
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
        sorted({entry.assigned_protein for entry in assign_razor_peptides(records)})
    )
    picked = tuple(
        sorted(
            {
                entry.protein_ref
                for entry in calculate_picked_protein_fdr(
                    records,
                    threshold=picked_threshold,
                )
                if entry.accepted
                and entry.target_decoy_label is not TargetDecoyLabel.DECOY
            }
        )
    )
    grouped = tuple(
        sorted(
            {group.representative_protein for group in build_protein_groups(records)}
        )
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
                    jaccard_similarity=(len(intersection) / len(union))
                    if union
                    else 1.0,
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
        protein for row in trace_rows for protein in row.get("protein_refs", ())
    }
    return PsmPeptideProteinTraceBundle(
        trace_entry_count=len(trace_rows),
        distinct_psm_count=len(psm_ids),
        distinct_peptide_count=len(peptides),
        distinct_protein_count=len(proteins),
        trace_hash=hashlib.sha256(payload).hexdigest(),
        trace_rows=trace_rows,
    )


def write_psm_peptide_protein_trace_bundle(
    bundle: PsmPeptideProteinTraceBundle,
    destination: Path,
) -> None:
    """Write a JSON export of the trace bundle for scientific review."""
    destination.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")


def export_psm_peptide_protein_trace_bundle(
    bundle: PsmPeptideProteinTraceBundle,
    destination: Path,
) -> None:
    """Compatibility wrapper for the legacy PSM trace bundle export name."""

    write_psm_peptide_protein_trace_bundle(bundle, destination)


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
                newly_accepted_peptide_count=len(accepted_peptides - previous_peptides),
                newly_accepted_protein_count=len(accepted_proteins - previous_proteins),
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
            {protein_ref for record in records for protein_ref in record.protein_refs}
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
        risk_summary = "custom decoy policy is internally consistent and no accession collisions were detected"
    elif collision_accessions or "shared_base_accession_pairs" in issue_codes:
        risk_summary = "custom decoy construction yields target-decoy accession collisions that must be resolved before FDR"
    else:
        risk_summary = "custom decoy policy has validation issues that should be resolved before confidence thresholds are applied"
    return CustomDecoyValidationReport(
        valid=valid,
        policy_issue_codes=issue_codes,
        collision_count=len(collision_accessions),
        collision_accessions=collision_accessions,
        risk_summary=risk_summary,
    )


class ConfidenceResultFamily(StrEnum):
    """Result-family boundary classes for confidence interpretation."""

    DATABASE_DDA = "database_dda"
    OPEN_SEARCH = "open_search"
    SPECTRAL_LIBRARY = "spectral_library"
    DIA_LIBRARY = "dia_library"


class LibrarySearchConfidenceBoundaryInput(JsonModel):
    """One result-set descriptor for confidence boundary classification."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    family_hint: str = Field(..., min_length=1)
    has_target_decoy: bool
    has_library_scores: bool
    is_dia: bool = False


class LibrarySearchConfidenceBoundaryIssue(JsonModel):
    """One issue raised while evaluating confidence-family boundaries."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LibrarySearchConfidenceBoundaryReport(JsonModel):
    """Boundary report over heterogeneous identification result families."""

    model_config = ConfigDict(extra="forbid")

    classified_families: dict[str, ConfidenceResultFamily] = Field(default_factory=dict)
    compatible: bool
    issues: tuple[LibrarySearchConfidenceBoundaryIssue, ...] = Field(
        default_factory=tuple
    )


def _classify_confidence_result_family(
    descriptor: LibrarySearchConfidenceBoundaryInput,
) -> ConfidenceResultFamily:
    hint = descriptor.family_hint.strip().lower()
    if descriptor.is_dia:
        return ConfidenceResultFamily.DIA_LIBRARY
    if "open" in hint:
        return ConfidenceResultFamily.OPEN_SEARCH
    if descriptor.has_library_scores or "library" in hint:
        return ConfidenceResultFamily.SPECTRAL_LIBRARY
    return ConfidenceResultFamily.DATABASE_DDA


def evaluate_library_search_confidence_boundary(
    descriptors: tuple[LibrarySearchConfidenceBoundaryInput, ...],
) -> LibrarySearchConfidenceBoundaryReport:
    """Classify and validate confidence boundaries across result families."""
    classified = {
        descriptor.run_id: _classify_confidence_result_family(descriptor)
        for descriptor in descriptors
    }
    family_set = set(classified.values())
    issues: list[LibrarySearchConfidenceBoundaryIssue] = []
    if (
        ConfidenceResultFamily.OPEN_SEARCH in family_set
        and ConfidenceResultFamily.SPECTRAL_LIBRARY in family_set
    ):
        issues.append(
            LibrarySearchConfidenceBoundaryIssue(
                code="open_vs_library_mixture",
                message="open-search and spectral-library confidence families must not be merged under one threshold policy",
            )
        )
    if (
        ConfidenceResultFamily.DIA_LIBRARY in family_set
        and ConfidenceResultFamily.DATABASE_DDA in family_set
    ):
        issues.append(
            LibrarySearchConfidenceBoundaryIssue(
                code="dia_vs_dda_mixture",
                message="DIA-library and database-DDA confidence families require separate calibration and FDR interpretation",
            )
        )
    for descriptor in descriptors:
        family = classified[descriptor.run_id]
        if (
            family is ConfidenceResultFamily.DATABASE_DDA
            and not descriptor.has_target_decoy
        ):
            issues.append(
                LibrarySearchConfidenceBoundaryIssue(
                    code="dda_missing_target_decoy",
                    message=f"run {descriptor.run_id} is classified as database DDA but lacks target-decoy evidence",
                )
            )
        if (
            family
            in {
                ConfidenceResultFamily.SPECTRAL_LIBRARY,
                ConfidenceResultFamily.DIA_LIBRARY,
            }
            and not descriptor.has_library_scores
        ):
            issues.append(
                LibrarySearchConfidenceBoundaryIssue(
                    code="library_missing_library_scores",
                    message=f"run {descriptor.run_id} is library-classified but lacks explicit library confidence scores",
                )
            )
    return LibrarySearchConfidenceBoundaryReport(
        classified_families=classified,
        compatible=not issues,
        issues=tuple(issues),
    )


class DiaFdrRefusalIssue(JsonModel):
    """Explicit refusal issue for DIA-native FDR modeling."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class DiaFdrThresholdSnapshot(JsonModel):
    """Accepted-entity snapshot at one threshold across DIA evidence levels."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(..., ge=0.0, le=1.0)
    accepted_precursor_count: int = Field(..., ge=0)
    accepted_peptide_count: int = Field(..., ge=0)
    accepted_protein_count: int = Field(..., ge=0)
    accepted_library_entry_count: int = Field(..., ge=0)


class DiaNativeFdrModelReport(JsonModel):
    """DIA-native FDR comparison report across evidence levels."""

    model_config = ConfigDict(extra="forbid")

    compatible: bool
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    thresholds: tuple[float, ...] = Field(default_factory=tuple)
    snapshots: tuple[DiaFdrThresholdSnapshot, ...] = Field(default_factory=tuple)
    refusal_issues: tuple[DiaFdrRefusalIssue, ...] = Field(default_factory=tuple)


def build_dia_native_fdr_model_report(
    records: tuple[PsmRecord, ...],
    *,
    is_dia_context: bool,
    score_orientation: str = "lower_better",
    thresholds: tuple[float, ...] = (0.01, 0.05, 0.1),
) -> DiaNativeFdrModelReport:
    """Compare DIA-native FDR behavior across precursor, peptide, protein, and library levels."""
    if not is_dia_context:
        return DiaNativeFdrModelReport(
            compatible=False,
            score_orientation=score_orientation,
            thresholds=thresholds,
            snapshots=(),
            refusal_issues=(
                DiaFdrRefusalIssue(
                    code="non_dia_context",
                    message="dia-native fdr modeling is refused because the input context is not declared as DIA",
                ),
            ),
        )

    normalized_thresholds = tuple(sorted(dict.fromkeys(thresholds)))
    snapshots: list[DiaFdrThresholdSnapshot] = []
    for threshold in normalized_thresholds:
        precursor = calculate_basic_target_decoy_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        accepted_precursors = {
            entry.psm.spectrum_id
            for entry in precursor
            if entry.accepted
            and entry.psm.target_decoy_label is not TargetDecoyLabel.DECOY
        }
        level = calculate_level_specific_fdr(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        accepted_peptides = {
            entry.entity_id
            for entry in level.peptide_entries
            if entry.accepted and entry.target_decoy_label is not TargetDecoyLabel.DECOY
        }
        accepted_proteins = {
            entry.entity_id
            for entry in level.protein_entries
            if entry.accepted and entry.target_decoy_label is not TargetDecoyLabel.DECOY
        }
        library_entries = {
            "|".join(record.protein_refs)
            if record.protein_refs
            else record.canonical_peptide
            for record in records
            if record.target_decoy_label is not TargetDecoyLabel.DECOY
            and (record.q_value is None or record.q_value <= threshold)
        }
        snapshots.append(
            DiaFdrThresholdSnapshot(
                threshold=threshold,
                accepted_precursor_count=len(accepted_precursors),
                accepted_peptide_count=len(accepted_peptides),
                accepted_protein_count=len(accepted_proteins),
                accepted_library_entry_count=len(library_entries),
            )
        )
    return DiaNativeFdrModelReport(
        compatible=True,
        score_orientation=score_orientation,
        thresholds=normalized_thresholds,
        snapshots=tuple(snapshots),
        refusal_issues=(),
    )
