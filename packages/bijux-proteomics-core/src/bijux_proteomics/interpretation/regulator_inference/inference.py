# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Upstream regulator inference from explicit target evidence and observed signal."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.interpretation.pathway_activity import (
    PathwayActivityConfidenceStatus,
    PathwayActivityReport,
)
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinAnnotationMappingReport,
)
from bijux_proteomics.interpretation.regulator_inference.models import (
    RegulatorEvidenceRecord,
    RegulatorEvidenceTargetField,
    RegulatorEvidenceType,
    RegulatorInferenceDirection,
    RegulatorInferenceEntry,
    RegulatorInferencePolicy,
    RegulatorInferenceReport,
    RegulatorInferenceSummary,
    RegulatorSignalSurface,
    RegulatorSiteSignalEntry,
    UnresolvedRegulatorTargetEntry,
)
from bijux_proteomics.io.stable_outputs import sort_strings
from bijux_proteomics.quantification.contracts.differential import (
    DifferentialAbundanceReport,
)
from bijux_proteomics.sequences.fasta import canonicalize_protein_reference


def build_regulator_inference_report(
    evidence_records: tuple[RegulatorEvidenceRecord, ...],
    differential_report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None = None,
    annotation_report: ProteinAnnotationMappingReport | None = None,
    pathway_activity_report: PathwayActivityReport | None = None,
    site_signal_entries: tuple[RegulatorSiteSignalEntry, ...] = (),
    policy: RegulatorInferencePolicy | None = None,
) -> RegulatorInferenceReport:
    """Infer upstream regulator support from explicit user-supplied evidence rows."""

    active_policy = policy or RegulatorInferencePolicy()
    differential_by_protein_ref = _protein_signal_lookup(
        differential_report,
        protein_refs_by_entity=protein_refs_by_entity,
    )
    gene_symbol_to_protein_refs = _gene_symbol_lookup(annotation_report)
    pathway_lookup = _pathway_signal_lookup(
        pathway_activity_report,
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
    )
    site_signal_lookup = {entry.site_key: entry for entry in site_signal_entries}
    pathway_support_proteins = _pathway_supporting_protein_lookup(
        pathway_activity_report
    )

    grouped_records: dict[
        tuple[str, RegulatorEvidenceType, str | None, str | None],
        list[RegulatorEvidenceRecord],
    ] = defaultdict(list)
    for record in evidence_records:
        grouped_records[
            (
                record.regulator,
                record.evidence_type,
                record.source_name,
                record.source_accession,
            )
        ].append(record)

    entries: list[RegulatorInferenceEntry] = []
    unresolved_targets: list[UnresolvedRegulatorTargetEntry] = []
    for key in sorted(
        grouped_records,
        key=lambda item: (item[0], item[1].value, item[2] or "", item[3] or ""),
    ):
        regulator, evidence_type, source_name, source_accession = key
        records = grouped_records[key]
        if evidence_type is RegulatorEvidenceType.KINASE_SUBSTRATE:
            entry, unresolved = _build_site_regulation_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                site_signal_lookup=site_signal_lookup,
                policy=active_policy,
            )
        elif evidence_type is RegulatorEvidenceType.PATHWAY:
            entry, unresolved = _build_pathway_activity_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                pathway_lookup=pathway_lookup,
                pathway_support_proteins=pathway_support_proteins,
                policy=active_policy,
            )
        else:
            entry, unresolved = _build_protein_abundance_entry(
                regulator=regulator,
                evidence_type=evidence_type,
                source_name=source_name,
                source_accession=source_accession,
                records=records,
                differential_by_protein_ref=differential_by_protein_ref,
                gene_symbol_to_protein_refs=gene_symbol_to_protein_refs,
                policy=active_policy,
            )
        entries.append(entry)
        unresolved_targets.extend(unresolved)

    entry_tuple = tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                entry.regulator,
                entry.evidence_type.value,
                entry.signal_surface.value,
                entry.source_name or "",
                entry.source_accession or "",
            ),
        )
    )
    unresolved_tuple = tuple(
        sorted(
            unresolved_targets,
            key=lambda entry: (
                entry.regulator,
                entry.evidence_type.value,
                entry.target_field.value,
                entry.target_value,
                entry.reason,
            ),
        )
    )
    summary = RegulatorInferenceSummary(
        regulator_count=len({entry.regulator for entry in entry_tuple}),
        entry_count=len(entry_tuple),
        site_regulation_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.SITE_REGULATION
        ),
        protein_abundance_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.PROTEIN_ABUNDANCE
        ),
        pathway_activity_entry_count=sum(
            1
            for entry in entry_tuple
            if entry.signal_surface is RegulatorSignalSurface.PATHWAY_ACTIVITY
        ),
        unresolved_target_count=len(unresolved_tuple),
        high_scoring_entry_count=sum(1 for entry in entry_tuple if entry.score >= 0.7),
    )
    return RegulatorInferenceReport(
        condition_a=differential_report.condition_a,
        condition_b=differential_report.condition_b,
        entries=entry_tuple,
        unresolved_targets=unresolved_tuple,
        summary=summary,
        note=(
            "regulator inference preserves site-regulation, protein-abundance, and "
            "pathway-activity support as separate evidence surfaces instead of "
            "collapsing kinase-site evidence into generic abundance support"
        ),
    )


def _build_site_regulation_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    site_signal_lookup: dict[str, RegulatorSiteSignalEntry],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    supporting_site_keys: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        if record.site_key is None:
            raise RuntimeError(
                "site-regulation regulator inference requires evidence records with site keys"
            )
        signal = site_signal_lookup.get(record.site_key)
        if signal is None:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=RegulatorEvidenceTargetField.SITE_KEY,
                    target_value=record.site_key,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="site_key was not present in the supplied site regulation surface",
                )
            )
            continue
        matched_target_count += 1
        values.append(signal.log2_fold_change)
        significance.append(_significance_score(signal.adjusted_p_value))
        supporting_site_keys.add(signal.site_key)
        if signal.protein_ref is not None:
            supporting_protein_refs.add(
                canonicalize_protein_reference(signal.protein_ref)
            )
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.SITE_REGULATION,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=supporting_site_keys,
            supporting_pathway_ids=set(),
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_protein_abundance_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    differential_by_protein_ref: dict[str, tuple[float, float | None]],
    gene_symbol_to_protein_refs: dict[str, tuple[str, ...]],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        resolved_protein_refs: tuple[str, ...]
        if record.protein_ref is not None:
            resolved_protein_refs = (record.protein_ref,)
            target_field = RegulatorEvidenceTargetField.PROTEIN_REF
            target_value = record.protein_ref
        else:
            if record.gene_symbol is None:
                raise RuntimeError(
                    "protein-abundance regulator inference requires a gene symbol when no protein ref is provided"
                )
            resolved_protein_refs = gene_symbol_to_protein_refs.get(
                record.gene_symbol.upper(),
                (),
            )
            target_field = RegulatorEvidenceTargetField.GENE_SYMBOL
            target_value = record.gene_symbol
        if not resolved_protein_refs:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=target_field,
                    target_value=target_value,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="target did not resolve onto the observed protein differential surface",
                )
            )
            continue
        matched_for_target = False
        for protein_ref in resolved_protein_refs:
            signal = differential_by_protein_ref.get(protein_ref)
            if signal is None:
                continue
            matched_for_target = True
            supporting_protein_refs.add(protein_ref)
            values.append(signal[0])
            significance.append(_significance_score(signal[1]))
        if matched_for_target:
            matched_target_count += 1
        else:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=target_field,
                    target_value=target_value,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="target resolved to annotations but none of those proteins carried observed differential signal",
                )
            )
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.PROTEIN_ABUNDANCE,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=set(),
            supporting_pathway_ids=set(),
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_pathway_activity_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    source_name: str | None,
    source_accession: str | None,
    records: list[RegulatorEvidenceRecord],
    pathway_lookup: dict[str, tuple[float | None, PathwayActivityConfidenceStatus]],
    pathway_support_proteins: dict[str, tuple[str, ...]],
    policy: RegulatorInferencePolicy,
) -> tuple[RegulatorInferenceEntry, list[UnresolvedRegulatorTargetEntry]]:
    values: list[float] = []
    significance: list[float] = []
    supporting_protein_refs: set[str] = set()
    supporting_pathway_ids: set[str] = set()
    unresolved: list[UnresolvedRegulatorTargetEntry] = []
    matched_target_count = 0
    for record in records:
        if record.pathway_id is None:
            raise RuntimeError(
                "pathway regulator inference requires evidence records with pathway ids"
            )
        pathway_signal = pathway_lookup.get(record.pathway_id)
        if pathway_signal is None or pathway_signal[0] is None:
            unresolved.append(
                UnresolvedRegulatorTargetEntry(
                    regulator=regulator,
                    evidence_type=evidence_type,
                    target_field=RegulatorEvidenceTargetField.PATHWAY_ID,
                    target_value=record.pathway_id,
                    source_name=source_name,
                    source_accession=source_accession,
                    reason="pathway_id was not present in the supplied pathway activity surface",
                )
            )
            continue
        matched_target_count += 1
        delta_value, confidence = pathway_signal
        if delta_value is None:
            raise RuntimeError("validated pathway signal unexpectedly lost its delta")
        values.append(delta_value)
        significance.append(
            1.0
            if confidence is PathwayActivityConfidenceStatus.HIGH_CONFIDENCE
            else 0.5
        )
        supporting_pathway_ids.add(record.pathway_id)
        supporting_protein_refs.update(
            pathway_support_proteins.get(record.pathway_id, ())
        )
    return (
        _build_inference_entry(
            regulator=regulator,
            evidence_type=evidence_type,
            signal_surface=RegulatorSignalSurface.PATHWAY_ACTIVITY,
            source_name=source_name,
            source_accession=source_accession,
            target_count=len(records),
            matched_target_count=matched_target_count,
            supporting_protein_refs=supporting_protein_refs,
            supporting_site_keys=set(),
            supporting_pathway_ids=supporting_pathway_ids,
            signal_values=values,
            significance_scores=significance,
            policy=policy,
        ),
        unresolved,
    )


def _build_inference_entry(
    *,
    regulator: str,
    evidence_type: RegulatorEvidenceType,
    signal_surface: RegulatorSignalSurface,
    source_name: str | None,
    source_accession: str | None,
    target_count: int,
    matched_target_count: int,
    supporting_protein_refs: set[str],
    supporting_site_keys: set[str],
    supporting_pathway_ids: set[str],
    signal_values: list[float],
    significance_scores: list[float],
    policy: RegulatorInferencePolicy,
) -> RegulatorInferenceEntry:
    coverage_fraction = (
        0.0 if target_count == 0 else matched_target_count / target_count
    )
    direction = _resolve_direction(signal_values)
    mean_log2_fold_change = None
    mean_activity_score_delta = None
    if signal_surface is RegulatorSignalSurface.PATHWAY_ACTIVITY:
        if signal_values:
            mean_activity_score_delta = sum(signal_values) / len(signal_values)
    elif signal_values:
        mean_log2_fold_change = sum(signal_values) / len(signal_values)
    score = _score_regulator_support(
        coverage_fraction=coverage_fraction,
        matched_signal_count=len(signal_values),
        signal_values=signal_values,
        significance_scores=significance_scores,
        direction=direction,
    )
    if coverage_fraction < policy.minimum_target_coverage_fraction:
        score = min(score, policy.low_coverage_score_cap)
    note = _build_inference_note(
        evidence_type=evidence_type,
        signal_surface=signal_surface,
        target_count=target_count,
        matched_target_count=matched_target_count,
        direction=direction,
        coverage_fraction=coverage_fraction,
        policy=policy,
    )
    return RegulatorInferenceEntry(
        regulator=regulator,
        evidence_type=evidence_type,
        signal_surface=signal_surface,
        source_name=source_name,
        source_accession=source_accession,
        target_count=target_count,
        matched_target_count=matched_target_count,
        coverage_fraction=round(coverage_fraction, 4),
        supporting_protein_refs=sort_strings(tuple(supporting_protein_refs)),
        supporting_site_keys=sort_strings(tuple(supporting_site_keys)),
        supporting_pathway_ids=sort_strings(tuple(supporting_pathway_ids)),
        direction=direction,
        score=round(score, 4),
        mean_log2_fold_change=None
        if mean_log2_fold_change is None
        else round(mean_log2_fold_change, 4),
        mean_activity_score_delta=None
        if mean_activity_score_delta is None
        else round(mean_activity_score_delta, 4),
        note=note,
    )


def _protein_signal_lookup(
    report: DifferentialAbundanceReport,
    *,
    protein_refs_by_entity: dict[str, tuple[str, ...]] | None,
) -> dict[str, tuple[float, float | None]]:
    lookup: dict[str, tuple[float, float | None]] = {}
    for entry in report.entries:
        protein_refs = (
            protein_refs_by_entity.get(entry.entity_id, (entry.entity_id,))
            if protein_refs_by_entity is not None
            else (entry.entity_id,)
        )
        for protein_ref in protein_refs:
            protein_ref = canonicalize_protein_reference(protein_ref)
            existing = lookup.get(protein_ref)
            if existing is None or _is_better_signal(
                candidate_adjusted_p_value=entry.adjusted_p_value,
                candidate_log2_fold_change=entry.log2_fold_change,
                current_adjusted_p_value=existing[1],
                current_log2_fold_change=existing[0],
            ):
                lookup[protein_ref] = (entry.log2_fold_change, entry.adjusted_p_value)
    return lookup


def _gene_symbol_lookup(
    annotation_report: ProteinAnnotationMappingReport | None,
) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, set[str]] = defaultdict(set)
    if annotation_report is None:
        return {}
    for entry in annotation_report.mapped_entries:
        if entry.gene_symbol:
            mapping[entry.gene_symbol.upper()].add(entry.protein_ref)
    return {
        gene_symbol: sort_strings(tuple(protein_refs))
        for gene_symbol, protein_refs in mapping.items()
    }


def _pathway_signal_lookup(
    report: PathwayActivityReport | None,
    *,
    condition_a: str,
    condition_b: str,
) -> dict[str, tuple[float | None, PathwayActivityConfidenceStatus]]:
    if report is None:
        return {}
    return {
        entry.pathway_id: (
            entry.activity_score_delta,
            entry.comparison_confidence_status,
        )
        for entry in report.condition_comparisons
        if entry.condition_a == condition_a and entry.condition_b == condition_b
    }


def _pathway_supporting_protein_lookup(
    report: PathwayActivityReport | None,
) -> dict[str, tuple[str, ...]]:
    if report is None:
        return {}
    proteins_by_pathway: dict[str, set[str]] = defaultdict(set)
    for entry in report.member_contributions:
        proteins_by_pathway[entry.pathway_id].update(entry.observed_protein_refs)
    return {
        pathway_id: sort_strings(tuple(protein_refs))
        for pathway_id, protein_refs in proteins_by_pathway.items()
    }


def _score_regulator_support(
    *,
    coverage_fraction: float,
    matched_signal_count: int,
    signal_values: list[float],
    significance_scores: list[float],
    direction: RegulatorInferenceDirection,
) -> float:
    support_count_score = min(1.0, matched_signal_count / 3.0)
    effect_score = (
        0.0
        if not signal_values
        else min(
            1.0, sum(abs(value) for value in signal_values) / len(signal_values) / 2.0
        )
    )
    significance_score = (
        0.0
        if not significance_scores
        else sum(significance_scores) / len(significance_scores)
    )
    score = (
        (0.35 * coverage_fraction)
        + (0.20 * support_count_score)
        + (0.25 * effect_score)
        + (0.20 * significance_score)
    )
    if direction is RegulatorInferenceDirection.MIXED:
        score -= 0.15
    return max(0.0, min(1.0, score))


def _resolve_direction(values: list[float]) -> RegulatorInferenceDirection:
    positive = any(value > 0.0 for value in values)
    negative = any(value < 0.0 for value in values)
    if positive and negative:
        return RegulatorInferenceDirection.MIXED
    if positive:
        return RegulatorInferenceDirection.UP
    if negative:
        return RegulatorInferenceDirection.DOWN
    return RegulatorInferenceDirection.UNSUPPORTED


def _build_inference_note(
    *,
    evidence_type: RegulatorEvidenceType,
    signal_surface: RegulatorSignalSurface,
    target_count: int,
    matched_target_count: int,
    direction: RegulatorInferenceDirection,
    coverage_fraction: float,
    policy: RegulatorInferencePolicy,
) -> str:
    coverage_note = _build_low_coverage_note(
        coverage_fraction=coverage_fraction,
        policy=policy,
    )
    if matched_target_count == 0:
        note = (
            f"{evidence_type.value} evidence did not resolve onto the supplied "
            f"{signal_surface.value} surface"
        )
        return note if coverage_note is None else f"{note}; {coverage_note}"
    if direction is RegulatorInferenceDirection.MIXED:
        note = (
            f"{matched_target_count} of {target_count} explicit {evidence_type.value} "
            "targets were observed with conflicting directions"
        )
        return note if coverage_note is None else f"{note}; {coverage_note}"
    note = (
        f"{matched_target_count} of {target_count} explicit {evidence_type.value} "
        f"targets were observed on the {signal_surface.value} surface"
    )
    return note if coverage_note is None else f"{note}; {coverage_note}"


def _build_low_coverage_note(
    *,
    coverage_fraction: float,
    policy: RegulatorInferencePolicy,
) -> str | None:
    if coverage_fraction >= policy.minimum_target_coverage_fraction:
        return None
    return (
        "target coverage "
        f"{coverage_fraction:g} was below minimum {policy.minimum_target_coverage_fraction:g}"
    )


def _significance_score(adjusted_p_value: float | None) -> float:
    if adjusted_p_value is None:
        return 0.5
    return max(0.0, min(1.0, 1.0 - adjusted_p_value))


def _is_better_signal(
    *,
    candidate_adjusted_p_value: float | None,
    candidate_log2_fold_change: float,
    current_adjusted_p_value: float | None,
    current_log2_fold_change: float,
) -> bool:
    candidate_key = (
        1.0 if candidate_adjusted_p_value is None else candidate_adjusted_p_value,
        -abs(candidate_log2_fold_change),
    )
    current_key = (
        1.0 if current_adjusted_p_value is None else current_adjusted_p_value,
        -abs(current_log2_fold_change),
    )
    return candidate_key < current_key


__all__ = [
    "RegulatorEvidenceRecord",
    "RegulatorEvidenceTargetField",
    "RegulatorEvidenceType",
    "RegulatorInferenceDirection",
    "RegulatorInferenceEntry",
    "RegulatorInferencePolicy",
    "RegulatorInferenceReport",
    "RegulatorInferenceSummary",
    "RegulatorSignalSurface",
    "RegulatorSiteSignalEntry",
    "UnresolvedRegulatorTargetEntry",
    "build_regulator_inference_report",
]
