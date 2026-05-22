# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned multi-plex TMT integration over governed bridge/reference channels."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.multiplex.normalization import (
    TmtNormalizationMethod,
    TmtNormalizationPolicy,
    TmtNormalizationReport,
    build_tmt_normalization_report,
)
from bijux_proteomics.multiplex.reporter_matrix import TmtReporterFeatureBundle
from bijux_proteomics.quantification import LabelBasedChannelRole, QuantEntityLevel
from bijux_proteomics.quantification.contracts import (
    MissingValueSummaryEntry,
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinIntensityMatrixReport,
    ProteinIntensityMatrixRow,
    ProteinIntensityMatrixSummary,
)
from bijux_proteomics_foundation import JsonModel


class TmtPlexIntegrationPolicy(JsonModel):
    """Policy for integrating multiple TMT plexes into one protein matrix."""

    model_config = ConfigDict(extra="forbid")

    normalization_policy: TmtNormalizationPolicy = Field(
        default_factory=lambda: TmtNormalizationPolicy(
            method=TmtNormalizationMethod.REFERENCE_CHANNEL
        )
    )
    included_roles: tuple[LabelBasedChannelRole, ...] = (
        LabelBasedChannelRole.SAMPLE,
    )
    plex_effect_ratio_threshold: float = Field(default=1.25, ge=1.0)


class TmtPlexIntegrationSummary(JsonModel):
    """Compact summary over one multi-plex TMT integration run."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group_count: int = Field(..., ge=0)
    bridge_group_count: int = Field(..., ge=0)
    integrated_sample_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    missing_bridge_value_count: int = Field(..., ge=0)
    flagged_plex_effect_count: int = Field(..., ge=0)


class TmtPlexSampleAlignmentEntry(JsonModel):
    """One sample-metadata alignment row inside a multi-plex TMT integration run."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate: int = Field(..., ge=1)
    batch: str | None = None
    sample_role: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    analysis_included: bool
    bridge_sample_id: str | None = None
    bridge_channel: str | None = None
    note: str = Field(..., min_length=1)


class TmtPlexIntegrationReport(JsonModel):
    """Owned TMT plex-integration report over bridge-normalized protein values."""

    model_config = ConfigDict(extra="forbid")

    policy: TmtPlexIntegrationPolicy
    normalization_report: TmtNormalizationReport
    sample_alignment: tuple[TmtPlexSampleAlignmentEntry, ...] = Field(default_factory=tuple)
    integrated_protein_matrix: ProteinIntensityMatrixReport
    summary: TmtPlexIntegrationSummary
    note: str = Field(..., min_length=1)


def build_tmt_plex_integration_report(
    feature_bundle: TmtReporterFeatureBundle,
    *,
    policy: TmtPlexIntegrationPolicy | None = None,
) -> TmtPlexIntegrationReport:
    """Integrate governed TMT plexes through reference-channel protein ratios."""

    active_policy = policy or TmtPlexIntegrationPolicy()
    if (
        active_policy.normalization_policy.method
        is not TmtNormalizationMethod.REFERENCE_CHANNEL
    ):
        raise ValueError(
            "tmt plex integration currently requires reference-channel normalization"
        )
    normalization_report = build_tmt_normalization_report(
        feature_bundle,
        policy=active_policy.normalization_policy,
    )
    included_sample_ids = tuple(
        entry.sample_id
        for entry in sorted(
            feature_bundle.channel_mapping,
            key=lambda item: (item.multiplex_group, item.multiplex_channel),
        )
        if entry.mapped_to_design
        and entry.sample_id is not None
        and entry.channel_role in active_policy.included_roles
    )
    integrated_protein_matrix = _filter_protein_matrix_samples(
        normalization_report.after_report.protein_matrix,
        sample_ids=included_sample_ids,
    )
    sample_alignment = _build_sample_alignment_entries(
        feature_bundle=feature_bundle,
        included_sample_ids=included_sample_ids,
        normalization_report=normalization_report,
    )
    missing_bridge_value_count = sum(
        1
        for row in integrated_protein_matrix.rows
        for value in row.values
        if value.abundance is None
    )
    bridge_group_count = len(
        {
            transform.multiplex_group
            for transform in normalization_report.transforms
            if transform.reference_sample_id is not None
        }
    )
    return TmtPlexIntegrationReport(
        policy=active_policy,
        normalization_report=normalization_report,
        sample_alignment=sample_alignment,
        integrated_protein_matrix=integrated_protein_matrix,
        summary=TmtPlexIntegrationSummary(
            multiplex_group_count=len(
                {
                    entry.multiplex_group
                    for entry in feature_bundle.channel_mapping
                    if entry.mapped_to_design
                }
            ),
            bridge_group_count=bridge_group_count,
            integrated_sample_count=len(integrated_protein_matrix.sample_ids),
            protein_row_count=integrated_protein_matrix.summary.protein_row_count,
            missing_bridge_value_count=missing_bridge_value_count,
            flagged_plex_effect_count=0,
        ),
        note=(
            "tmt plex integration expresses protein abundances as bridge-normalized sample values across multiplex groups"
        ),
    )


def _build_sample_alignment_entries(
    *,
    feature_bundle: TmtReporterFeatureBundle,
    included_sample_ids: tuple[str, ...],
    normalization_report: TmtNormalizationReport,
) -> tuple[TmtPlexSampleAlignmentEntry, ...]:
    included_sample_id_set = set(included_sample_ids)
    bridge_by_group = {
        transform.multiplex_group: (transform.reference_sample_id, transform.reference_channel)
        for transform in normalization_report.transforms
        if transform.reference_sample_id is not None and transform.reference_channel is not None
    }
    mapping_by_sample = {
        entry.sample_id: entry
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design and entry.sample_id is not None
    }
    rows: list[TmtPlexSampleAlignmentEntry] = []
    for design_entry in sorted(
        feature_bundle.design_entries,
        key=lambda item: (item.multiplex_group or "", item.multiplex_channel or ""),
    ):
        mapping_entry = mapping_by_sample.get(design_entry.sample_id)
        if mapping_entry is None:
            continue
        bridge_sample_id, bridge_channel = bridge_by_group.get(
            design_entry.multiplex_group or "",
            (None, None),
        )
        analysis_included = design_entry.sample_id in included_sample_id_set
        rows.append(
            TmtPlexSampleAlignmentEntry(
                sample_id=design_entry.sample_id,
                multiplex_group=design_entry.multiplex_group or "",
                multiplex_channel=design_entry.multiplex_channel or "",
                condition=design_entry.condition,
                replicate=design_entry.replicate,
                batch=design_entry.batch,
                sample_role=design_entry.sample_role.value,
                channel_role=mapping_entry.channel_role or LabelBasedChannelRole.SAMPLE,
                analysis_included=analysis_included,
                bridge_sample_id=bridge_sample_id,
                bridge_channel=bridge_channel,
                note=(
                    "sample channel is aligned into the integrated matrix through the governed bridge/reference channel"
                    if analysis_included
                    else "non-sample channel metadata is preserved for plex integration review but excluded from the integrated analysis matrix"
                ),
            )
        )
    return tuple(rows)


def _filter_protein_matrix_samples(
    report: ProteinIntensityMatrixReport,
    *,
    sample_ids: tuple[str, ...],
) -> ProteinIntensityMatrixReport:
    sample_id_set = set(sample_ids)
    rows = tuple(
        ProteinIntensityMatrixRow(
            entity_id=row.entity_id,
            target_kind=row.target_kind,
            protein_refs=row.protein_refs,
            peptide_count=row.peptide_count,
            unique_peptide_count=row.unique_peptide_count,
            shared_peptide_count=row.shared_peptide_count,
            contributing_peptides=row.contributing_peptides,
            values=tuple(
                value for value in row.values if value.sample_id in sample_id_set
            ),
        )
        for row in report.rows
    )
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0
    missing_entries: list[MissingValueSummaryEntry] = []
    for sample_id in sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for row in rows:
            value = next(value for value in row.values if value.sample_id == sample_id)
            if value.missing_value_kind.value == "observed":
                observed += 1
                observed_cell_count += 1
            elif value.missing_value_kind.value == "zero":
                zero += 1
                zero_cell_count += 1
            elif value.missing_value_kind.value == "filtered":
                filtered += 1
                filtered_cell_count += 1
            else:
                not_observed += 1
                missing_cell_count += 1
        missing_entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=observed,
                zero_count=zero,
                not_observed_count=not_observed,
                filtered_count=filtered,
            )
        )
    return report.model_copy(
        update={
            "sample_ids": sample_ids,
            "rows": rows,
            "missing_summary": MissingValueSummaryReport(
                entity_level=QuantEntityLevel.PROTEIN,
                policy=report.missing_summary.policy,
                entries=tuple(missing_entries),
                included_entity_ids=report.missing_summary.included_entity_ids,
                excluded_entity_ids=report.missing_summary.excluded_entity_ids,
            ),
            "summary": ProteinIntensityMatrixSummary(
                peptide_row_count=report.summary.peptide_row_count,
                protein_row_count=report.summary.protein_row_count,
                sample_count=len(sample_ids),
                unique_only=report.summary.unique_only,
                observed_cell_count=observed_cell_count,
                zero_cell_count=zero_cell_count,
                missing_cell_count=missing_cell_count,
                filtered_cell_count=filtered_cell_count,
            ),
            "note": (
                "protein matrix is filtered to analysis sample channels after bridge-normalized plex integration"
            ),
        }
    )
