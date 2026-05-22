# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned isotope-label validation over SILAC labels and multiplex channels."""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.isotope_labeling.silac_quantification import (
    SilacImportReport,
    SilacLabel,
)
from bijux_proteomics_foundation import JsonModel


class SilacValidationPolicy(JsonModel):
    """Policy for SILAC label-presence and pair-coverage validation."""

    model_config = ConfigDict(extra="forbid")

    expected_labels: tuple[SilacLabel, ...] = (
        SilacLabel.LIGHT,
        SilacLabel.HEAVY,
    )
    separate_charge_states: bool = True
    weak_label_ratio_floor: float = Field(default=0.5, gt=0.0)
    weak_group_coverage_floor: float = Field(default=0.6, gt=0.0, le=1.0)
    abnormal_distribution_floor: float = Field(default=0.7, gt=0.0)
    abnormal_distribution_ceiling: float = Field(default=1.5, gt=0.0)

    @model_validator(mode="after")
    def _validate_expected_labels(self) -> SilacValidationPolicy:
        normalized = tuple(dict.fromkeys(self.expected_labels))
        if len(normalized) < 2:
            raise ValueError("silac validation requires at least two expected labels")
        self.expected_labels = normalized
        return self


class SilacLabelValidationEntry(JsonModel):
    """One expected SILAC label ledger row for a sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    expected_group_count: int = Field(..., ge=0)
    observed_group_count: int = Field(..., ge=0)
    missing_group_count: int = Field(..., ge=0)
    observed_feature_count: int = Field(..., ge=0)
    total_intensity: float = Field(..., ge=0.0)
    present: bool
    note: str = Field(..., min_length=1)


class SilacValidationSummary(JsonModel):
    """Compact summary over one SILAC label-validation run."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    expected_label_count: int = Field(..., ge=0)
    label_entry_count: int = Field(..., ge=0)
    missing_label_count: int = Field(..., ge=0)
    missing_pair_member_count: int = Field(..., ge=0)
    abnormal_distribution_count: int = Field(..., ge=0)
    weak_label_count: int = Field(..., ge=0)


class SilacLabelDistributionEntry(JsonModel):
    """One SILAC label-intensity distribution row for a sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    total_intensity: float = Field(..., ge=0.0)
    sample_median_total_intensity: float | None = Field(default=None, ge=0.0)
    ratio_to_sample_median: float | None = Field(default=None, ge=0.0)
    abnormal_distribution: bool
    note: str = Field(..., min_length=1)


class SilacWeakEvidenceEntry(JsonModel):
    """One weak SILAC label-evidence finding."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    label: SilacLabel
    issue_kind: str = Field(..., min_length=1)
    observed_group_fraction: float = Field(..., ge=0.0)
    total_intensity_ratio_to_sample_max: float = Field(..., ge=0.0)
    note: str = Field(..., min_length=1)


class SilacValidationReport(JsonModel):
    """Owned SILAC label-validation surface."""

    model_config = ConfigDict(extra="forbid")

    import_report: SilacImportReport
    policy: SilacValidationPolicy
    label_entries: tuple[SilacLabelValidationEntry, ...] = Field(default_factory=tuple)
    distribution_entries: tuple[SilacLabelDistributionEntry, ...] = Field(default_factory=tuple)
    weak_evidence: tuple[SilacWeakEvidenceEntry, ...] = Field(default_factory=tuple)
    summary: SilacValidationSummary
    note: str = Field(..., min_length=1)


def build_silac_validation_report(
    import_report: SilacImportReport,
    *,
    policy: SilacValidationPolicy | None = None,
) -> SilacValidationReport:
    """Validate expected SILAC labels and pair coverage over imported feature rows."""

    active_policy = policy or SilacValidationPolicy()
    sample_groups: dict[str, set[tuple[str, int | None]]] = {}
    groups_by_sample_and_label: dict[tuple[str, SilacLabel], set[tuple[str, int | None]]] = {}
    rows_by_sample_and_label: dict[tuple[str, SilacLabel], list[float]] = {}

    for row in import_report.accepted_rows:
        group_key = (
            row.peptide,
            row.charge if active_policy.separate_charge_states else None,
        )
        sample_groups.setdefault(row.sample_id, set()).add(group_key)
        groups_by_sample_and_label.setdefault((row.sample_id, row.label), set()).add(group_key)
        rows_by_sample_and_label.setdefault((row.sample_id, row.label), []).append(row.intensity)

    label_entries: list[SilacLabelValidationEntry] = []
    for sample_id in sorted(sample_groups):
        expected_group_count = len(sample_groups[sample_id])
        for label in active_policy.expected_labels:
            observed_groups = groups_by_sample_and_label.get((sample_id, label), set())
            observed_rows = rows_by_sample_and_label.get((sample_id, label), [])
            missing_group_count = max(expected_group_count - len(observed_groups), 0)
            label_entries.append(
                SilacLabelValidationEntry(
                    sample_id=sample_id,
                    label=label,
                    expected_group_count=expected_group_count,
                    observed_group_count=len(observed_groups),
                    missing_group_count=missing_group_count,
                    observed_feature_count=len(observed_rows),
                    total_intensity=float(sum(observed_rows)),
                    present=bool(observed_rows),
                    note=(
                        "expected SILAC label is represented across all observed peptide groups"
                        if missing_group_count == 0 and observed_rows
                        else "expected SILAC label is preserved even though one or more peptide groups are missing that label state"
                    ),
                )
            )

    distribution_entries: list[SilacLabelDistributionEntry] = []
    weak_evidence: list[SilacWeakEvidenceEntry] = []
    entries_by_sample = {
        sample_id: tuple(
            entry for entry in label_entries if entry.sample_id == sample_id
        )
        for sample_id in sorted(sample_groups)
    }
    for sample_id, sample_entries in entries_by_sample.items():
        positive_totals = sorted(
            entry.total_intensity for entry in sample_entries if entry.total_intensity > 0.0
        )
        sample_median_total_intensity = (
            _median(positive_totals) if positive_totals else None
        )
        sample_max_total_intensity = max(
            (entry.total_intensity for entry in sample_entries),
            default=0.0,
        )
        for entry in sample_entries:
            ratio_to_sample_median = _ratio_or_none(
                numerator=entry.total_intensity,
                denominator=sample_median_total_intensity,
            )
            abnormal_distribution = (
                ratio_to_sample_median is not None
                and (
                    ratio_to_sample_median < active_policy.abnormal_distribution_floor
                    or ratio_to_sample_median > active_policy.abnormal_distribution_ceiling
                )
            )
            distribution_entries.append(
                SilacLabelDistributionEntry(
                    sample_id=sample_id,
                    label=entry.label,
                    total_intensity=entry.total_intensity,
                    sample_median_total_intensity=sample_median_total_intensity,
                    ratio_to_sample_median=ratio_to_sample_median,
                    abnormal_distribution=abnormal_distribution,
                    note=(
                        "label total intensity is within the sample-level isotope distribution envelope"
                        if not abnormal_distribution
                        else "label total intensity falls outside the sample-level isotope distribution envelope"
                    ),
                )
            )
            observed_group_fraction = (
                float(entry.observed_group_count) / float(entry.expected_group_count)
                if entry.expected_group_count > 0
                else 0.0
            )
            total_intensity_ratio_to_sample_max = (
                float(entry.total_intensity) / float(sample_max_total_intensity)
                if sample_max_total_intensity > 0.0
                else 0.0
            )
            if observed_group_fraction < active_policy.weak_group_coverage_floor:
                weak_evidence.append(
                    SilacWeakEvidenceEntry(
                        sample_id=sample_id,
                        label=entry.label,
                        issue_kind="incomplete_pair_coverage",
                        observed_group_fraction=observed_group_fraction,
                        total_intensity_ratio_to_sample_max=total_intensity_ratio_to_sample_max,
                        note="expected SILAC label is missing from too many peptide groups for this sample",
                    )
                )
            if total_intensity_ratio_to_sample_max < active_policy.weak_label_ratio_floor:
                weak_evidence.append(
                    SilacWeakEvidenceEntry(
                        sample_id=sample_id,
                        label=entry.label,
                        issue_kind="weak_total_intensity",
                        observed_group_fraction=observed_group_fraction,
                        total_intensity_ratio_to_sample_max=total_intensity_ratio_to_sample_max,
                        note="label total intensity is weak relative to the strongest observed label in the sample",
                    )
                )

    return SilacValidationReport(
        import_report=import_report,
        policy=active_policy,
        label_entries=tuple(label_entries),
        distribution_entries=tuple(distribution_entries),
        weak_evidence=tuple(weak_evidence),
        summary=SilacValidationSummary(
            sample_count=import_report.summary.sample_count,
            expected_label_count=len(active_policy.expected_labels),
            label_entry_count=len(label_entries),
            missing_label_count=sum(1 for entry in label_entries if not entry.present),
            missing_pair_member_count=sum(
                entry.missing_group_count for entry in label_entries
            ),
            abnormal_distribution_count=sum(
                1 for entry in distribution_entries if entry.abnormal_distribution
            ),
            weak_label_count=len(weak_evidence),
        ),
        note=(
            "silac validation preserves expected label coverage, intensity distribution, and weak-label evidence for isotope-health review"
        ),
    )


def _median(values: list[float]) -> float:
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return float(values[midpoint])
    return float(values[midpoint - 1] + values[midpoint]) / 2.0


def _ratio_or_none(
    *,
    numerator: float,
    denominator: float | None,
) -> float | None:
    if denominator is None or denominator <= 0.0:
        return None
    return float(numerator) / float(denominator)
