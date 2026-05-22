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


class SilacValidationReport(JsonModel):
    """Owned SILAC label-validation surface."""

    model_config = ConfigDict(extra="forbid")

    import_report: SilacImportReport
    policy: SilacValidationPolicy
    label_entries: tuple[SilacLabelValidationEntry, ...] = Field(default_factory=tuple)
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

    return SilacValidationReport(
        import_report=import_report,
        policy=active_policy,
        label_entries=tuple(label_entries),
        summary=SilacValidationSummary(
            sample_count=import_report.summary.sample_count,
            expected_label_count=len(active_policy.expected_labels),
            label_entry_count=len(label_entries),
            missing_label_count=sum(1 for entry in label_entries if not entry.present),
            missing_pair_member_count=sum(
                entry.missing_group_count for entry in label_entries
            ),
        ),
        note=(
            "silac validation preserves expected label coverage and missing pair-member evidence before intensity-health review is applied"
        ),
    )
