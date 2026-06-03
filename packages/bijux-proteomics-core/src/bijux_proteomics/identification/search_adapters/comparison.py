# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Cross-engine comparison and disagreement review over search-adapter outputs."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    normalize_psm_records,
    normalize_psm_score_orientation,
    select_best_psm_per_spectrum,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    ExternalEngineDisagreementEntry,
    ExternalEngineDisagreementKind,
    ExternalEngineDisagreementReport,
    MergedSearchSpectrumEntry,
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchEngineObservation,
    SearchMergeAgreementStatus,
    SearchMergeCompatibilityIssue,
    SearchMergeCompatibilityReport,
    SearchResultComparabilityReport,
    SearchResultMergeReport,
    SearchScoreFamily,
)


def _score_families_compatible(
    left: SearchScoreFamily,
    right: SearchScoreFamily,
) -> tuple[bool, str]:
    if left is right:
        return True, f"both reports use the same score family {left.value}"
    if SearchScoreFamily.GENERIC_NUMERIC in {left, right}:
        return (
            True,
            "one report uses generic numeric scores, so normalized ranking is comparable but native semantics remain partially unspecified",
        )
    return (
        False,
        f"score families {left.value} and {right.value} are orientation-normalizable but not natively interchangeable",
    )


def compare_search_result_reports(
    left: SearchAdapterNormalizationReport,
    right: SearchAdapterNormalizationReport,
) -> SearchResultComparabilityReport:
    """Compare two normalized search-result reports on a shared score scale."""
    score_family_compatible, score_family_note = _score_families_compatible(
        left.adapter_manifest.score_family,
        right.adapter_manifest.score_family,
    )
    left_by_spectrum = {
        record.spectrum_id: record
        for record in normalize_psm_records(left.normalized_records)
    }
    right_by_spectrum = {
        record.spectrum_id: record
        for record in normalize_psm_records(right.normalized_records)
    }
    shared_spectra = sorted(set(left_by_spectrum) & set(right_by_spectrum))
    left_only = set(left_by_spectrum) - set(right_by_spectrum)
    right_only = set(right_by_spectrum) - set(left_by_spectrum)
    left_normalized = {
        (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
        for entry in normalize_psm_score_orientation(
            left.normalized_records,
            score_orientation=left.adapter_manifest.score_orientation.value,
        )
    }
    right_normalized = {
        (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
        for entry in normalize_psm_score_orientation(
            right.normalized_records,
            score_orientation=right.adapter_manifest.score_orientation.value,
        )
    }
    exact_match_count = 0
    label_conflict_count = 0
    shared_peptides: set[str] = set()
    total_score_delta = 0.0
    for spectrum_id in shared_spectra:
        left_record = left_by_spectrum[spectrum_id]
        right_record = right_by_spectrum[spectrum_id]
        shared_peptides.add(left_record.canonical_peptide)
        shared_peptides.add(right_record.canonical_peptide)
        if (
            left_record.canonical_peptide == right_record.canonical_peptide
            and left_record.charge == right_record.charge
        ):
            exact_match_count += 1
        if left_record.target_decoy_label is not right_record.target_decoy_label:
            label_conflict_count += 1
        left_score = left_normalized.get(
            (left_record.spectrum_id, left_record.canonical_peptide), 0.0
        )
        right_score = right_normalized.get(
            (right_record.spectrum_id, right_record.canonical_peptide), 0.0
        )
        total_score_delta += abs(left_score - right_score)
    shared_count = len(shared_spectra)
    return SearchResultComparabilityReport(
        left_adapter_kind=left.adapter_manifest.adapter_kind,
        right_adapter_kind=right.adapter_manifest.adapter_kind,
        left_score_family=left.adapter_manifest.score_family,
        right_score_family=right.adapter_manifest.score_family,
        left_result_family=left.adapter_manifest.result_family,
        right_result_family=right.adapter_manifest.result_family,
        score_family_compatible=score_family_compatible,
        score_family_note=score_family_note,
        left_total_psms=len(left.normalized_records),
        right_total_psms=len(right.normalized_records),
        shared_spectrum_count=shared_count,
        left_only_spectrum_count=len(left_only),
        right_only_spectrum_count=len(right_only),
        shared_peptide_count=len(shared_peptides),
        exact_match_count=exact_match_count,
        label_conflict_count=label_conflict_count,
        peptide_agreement_fraction=exact_match_count / shared_count
        if shared_count
        else 0.0,
        mean_normalized_score_delta=total_score_delta / shared_count
        if shared_count
        else 0.0,
    )


def merge_search_result_reports(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchResultMergeReport:
    """Merge multiple engine reports without flattening engine-specific uncertainty."""
    if not reports:
        return SearchResultMergeReport(
            adapter_kinds=(),
            merged_entries=(),
            exact_agreement_count=0,
            conflict_count=0,
            partial_coverage_count=0,
        )
    adapter_kinds = tuple(report.adapter_manifest.adapter_kind for report in reports)
    if len(set(adapter_kinds)) != len(adapter_kinds):
        raise ValueError("multi-engine merge requires distinct adapter kinds")

    normalized_scores_by_adapter: dict[
        SearchAdapterKind, dict[tuple[str, str], float]
    ] = {}
    per_report_best: list[
        tuple[SearchAdapterNormalizationReport, dict[str, PsmRecord]]
    ] = []
    for report in reports:
        normalized_scores_by_adapter[report.adapter_manifest.adapter_kind] = {
            (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
            for entry in normalize_psm_score_orientation(
                report.normalized_records,
                score_orientation=report.adapter_manifest.score_orientation.value,
            )
        }
        best = {
            record.spectrum_id: record
            for record in select_best_psm_per_spectrum(report.normalized_records)
        }
        per_report_best.append((report, best))

    all_spectra = sorted(
        {spectrum_id for _, best in per_report_best for spectrum_id in best}
    )
    merged_entries: list[MergedSearchSpectrumEntry] = []
    for spectrum_id in all_spectra:
        observations: list[SearchEngineObservation] = []
        for report, best in per_report_best:
            record = best.get(spectrum_id)
            if record is None:
                continue
            observations.append(
                SearchEngineObservation(
                    adapter_kind=report.adapter_manifest.adapter_kind,
                    adapter_name=report.adapter_manifest.display_name,
                    score_family=report.adapter_manifest.score_family,
                    result_family=report.adapter_manifest.result_family,
                    normalized_score=normalized_scores_by_adapter[
                        report.adapter_manifest.adapter_kind
                    ].get((record.spectrum_id, record.canonical_peptide), 0.0),
                    q_value=record.q_value,
                    record=record,
                )
            )
        peptide_set = {entry.record.canonical_peptide for entry in observations}
        charge_set = {entry.record.charge for entry in observations}
        label_set = {entry.record.target_decoy_label for entry in observations}
        if len(observations) < len(reports):
            status = SearchMergeAgreementStatus.PARTIAL_COVERAGE
            note = "not every engine produced an accepted observation for this spectrum"
        elif len(peptide_set) > 1:
            status = SearchMergeAgreementStatus.PEPTIDE_CONFLICT
            note = "engines disagree on the peptide assignment for this spectrum"
        elif len(charge_set) > 1:
            status = SearchMergeAgreementStatus.CHARGE_CONFLICT
            note = "engines agree on the peptide but disagree on precursor charge"
        elif len(label_set) > 1:
            status = SearchMergeAgreementStatus.LABEL_CONFLICT
            note = (
                "engines disagree on the target-decoy interpretation for this spectrum"
            )
        else:
            status = SearchMergeAgreementStatus.EXACT_MATCH
            note = "all engines agree on peptide, charge, and target-decoy label"
        merged_entries.append(
            MergedSearchSpectrumEntry(
                spectrum_id=spectrum_id,
                observations=tuple(
                    sorted(observations, key=lambda entry: entry.adapter_kind.value)
                ),
                agreement_status=status,
                consensus_peptide=observations[0].record.canonical_peptide
                if len(peptide_set) == 1
                else None,
                consensus_charge=observations[0].record.charge
                if len(charge_set) == 1
                else None,
                uncertainty_note=note,
            )
        )
    return SearchResultMergeReport(
        adapter_kinds=tuple(sorted(adapter_kinds, key=lambda kind: kind.value)),
        merged_entries=tuple(merged_entries),
        exact_agreement_count=sum(
            entry.agreement_status is SearchMergeAgreementStatus.EXACT_MATCH
            for entry in merged_entries
        ),
        conflict_count=sum(
            entry.agreement_status
            in {
                SearchMergeAgreementStatus.PEPTIDE_CONFLICT,
                SearchMergeAgreementStatus.CHARGE_CONFLICT,
                SearchMergeAgreementStatus.LABEL_CONFLICT,
            }
            for entry in merged_entries
        ),
        partial_coverage_count=sum(
            entry.agreement_status is SearchMergeAgreementStatus.PARTIAL_COVERAGE
            for entry in merged_entries
        ),
    )


def _peptide_definition_style(
    records: tuple[PsmRecord, ...],
) -> str:
    if any(
        any(marker in record.canonical_peptide for marker in ("[", "]", "(", ")", "."))
        for record in records
    ):
        return "modified_or_annotated"
    return "stripped_sequence"


def assess_search_merge_compatibility(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchMergeCompatibilityReport:
    """Assess whether reports are compatible for mixed-engine evidence merging."""
    adapter_kinds = tuple(report.adapter_manifest.adapter_kind for report in reports)
    issues: list[SearchMergeCompatibilityIssue] = []
    if len(set(adapter_kinds)) != len(adapter_kinds):
        issues.append(
            SearchMergeCompatibilityIssue(
                code="duplicate_adapter_kind",
                message="mixed-engine merge requires distinct adapter kinds",
                severity="error",
                adapter_kinds=adapter_kinds,
            )
        )
    result_families = {report.adapter_manifest.result_family for report in reports}
    if len(result_families) > 1:
        issues.append(
            SearchMergeCompatibilityIssue(
                code="result_family_mismatch",
                message="mixed-engine merge requires a single compatible result family",
                severity="error",
                adapter_kinds=adapter_kinds,
            )
        )

    for left_index, left in enumerate(reports):
        for right in reports[left_index + 1 :]:
            compatible, note = _score_families_compatible(
                left.adapter_manifest.score_family,
                right.adapter_manifest.score_family,
            )
            if not compatible:
                issues.append(
                    SearchMergeCompatibilityIssue(
                        code="score_family_mismatch",
                        message=note,
                        severity="error",
                        adapter_kinds=(
                            left.adapter_manifest.adapter_kind,
                            right.adapter_manifest.adapter_kind,
                        ),
                    )
                )
            left_policy = left.adapter_manifest.default_decoy_policy
            right_policy = right.adapter_manifest.default_decoy_policy
            left_signature = (
                left_policy.protein_prefix,
                left_policy.protein_suffix,
                tuple(left_policy.explicit_decoy_values),
                tuple(left_policy.explicit_target_values),
            )
            right_signature = (
                right_policy.protein_prefix,
                right_policy.protein_suffix,
                tuple(right_policy.explicit_decoy_values),
                tuple(right_policy.explicit_target_values),
            )
            if (
                left_signature != right_signature
                and all(
                    bool(signature[0] or signature[1] or signature[2] or signature[3])
                    for signature in (left_signature, right_signature)
                )
                and SearchAdapterKind.GENERIC
                not in {
                    left.adapter_manifest.adapter_kind,
                    right.adapter_manifest.adapter_kind,
                }
            ):
                issues.append(
                    SearchMergeCompatibilityIssue(
                        code="decoy_policy_mismatch",
                        message="engine decoy policies differ and may produce non-comparable target-decoy interpretation",
                        severity="error",
                        adapter_kinds=(
                            left.adapter_manifest.adapter_kind,
                            right.adapter_manifest.adapter_kind,
                        ),
                    )
                )

    peptide_styles = {
        report.adapter_manifest.adapter_kind: _peptide_definition_style(
            report.normalized_records
        )
        for report in reports
    }
    if len(set(peptide_styles.values())) > 1:
        issues.append(
            SearchMergeCompatibilityIssue(
                code="peptide_definition_mismatch",
                message="engine peptide definitions differ between stripped and modified sequence representations",
                severity="error",
                adapter_kinds=tuple(
                    sorted(peptide_styles.keys(), key=lambda kind: kind.value)
                ),
            )
        )

    return SearchMergeCompatibilityReport(
        adapter_kinds=tuple(sorted(adapter_kinds, key=lambda kind: kind.value)),
        compatible=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def merge_search_result_reports_with_compatibility(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchResultMergeReport:
    """Merge reports only when compatibility checks succeed."""
    compatibility = assess_search_merge_compatibility(reports)
    if not compatibility.compatible:
        rendered = "; ".join(
            f"{issue.code}: {issue.message}" for issue in compatibility.issues
        )
        raise ValueError(
            f"multi-engine merge refused due to compatibility errors: {rendered}"
        )
    return merge_search_result_reports(reports)


def build_external_engine_disagreement_report(
    reports: tuple[SearchAdapterNormalizationReport, ...],
    *,
    confidence_delta_threshold: float = 0.35,
) -> ExternalEngineDisagreementReport:
    """Build disagreement diagnostics across external engine outputs."""
    if not reports:
        return ExternalEngineDisagreementReport(
            adapter_kinds=(),
            entries=(),
            disagreement_counts={},
        )
    per_report_best: list[
        tuple[SearchAdapterNormalizationReport, dict[str, PsmRecord]]
    ] = []
    normalized_scores: dict[SearchAdapterKind, dict[tuple[str, str], float]] = {}
    for report in reports:
        best = {
            record.spectrum_id: record
            for record in select_best_psm_per_spectrum(report.normalized_records)
        }
        per_report_best.append((report, best))
        normalized_scores[report.adapter_manifest.adapter_kind] = {
            (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
            for entry in normalize_psm_score_orientation(
                report.normalized_records,
                score_orientation=report.adapter_manifest.score_orientation.value,
            )
        }
    all_spectrum_ids = sorted(
        {spectrum_id for _, best in per_report_best for spectrum_id in best}
    )
    entries: list[ExternalEngineDisagreementEntry] = []
    for spectrum_id in all_spectrum_ids:
        observations: list[tuple[SearchAdapterKind, PsmRecord, float]] = []
        for report, best in per_report_best:
            record = best.get(spectrum_id)
            if record is None:
                continue
            adapter_kind = report.adapter_manifest.adapter_kind
            observations.append(
                (
                    adapter_kind,
                    record,
                    normalized_scores[adapter_kind].get(
                        (record.spectrum_id, record.canonical_peptide), 0.0
                    ),
                )
            )
        if len(observations) < len(reports):
            missing_kinds = tuple(
                sorted(
                    {
                        report.adapter_manifest.adapter_kind
                        for report, best in per_report_best
                        if spectrum_id not in best
                    },
                    key=lambda kind: kind.value,
                )
            )
            present_kinds = tuple(
                sorted(
                    {entry[0] for entry in observations},
                    key=lambda kind: kind.value,
                )
            )
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.MISSING_EVIDENCE,
                    adapter_kinds=tuple(
                        sorted(
                            set(missing_kinds + present_kinds),
                            key=lambda kind: kind.value,
                        )
                    ),
                    message="at least one engine is missing accepted evidence for this spectrum id",
                    normalized_score_delta=None,
                )
            )
        if len(observations) < 2:
            continue
        peptides = {entry[1].canonical_peptide for entry in observations}
        charges = {entry[1].charge for entry in observations}
        labels = {entry[1].target_decoy_label for entry in observations}
        adapter_kinds = tuple(
            sorted({entry[0] for entry in observations}, key=lambda kind: kind.value)
        )
        if len(peptides) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.PEPTIDE_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on the accepted peptide assignment",
                    normalized_score_delta=None,
                )
            )
        if len(charges) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.CHARGE_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on precursor charge assignment",
                    normalized_score_delta=None,
                )
            )
        if len(labels) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.LABEL_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on target-decoy interpretation",
                    normalized_score_delta=None,
                )
            )
        score_values = [entry[2] for entry in observations]
        score_delta = max(score_values) - min(score_values)
        if score_delta >= confidence_delta_threshold:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.CONFIDENCE_GAP,
                    adapter_kinds=adapter_kinds,
                    message="engine confidence differs materially after orientation normalization",
                    normalized_score_delta=score_delta,
                )
            )
    disagreement_counts: dict[str, int] = {}
    for entry in entries:
        disagreement_counts[entry.kind.value] = (
            disagreement_counts.get(entry.kind.value, 0) + 1
        )
    return ExternalEngineDisagreementReport(
        adapter_kinds=tuple(
            sorted(
                {report.adapter_manifest.adapter_kind for report in reports},
                key=lambda kind: kind.value,
            )
        ),
        entries=tuple(entries),
        disagreement_counts=dict(sorted(disagreement_counts.items())),
    )
