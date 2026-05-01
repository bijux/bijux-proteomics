# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Iteration-05 quantification and QC capability surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    LabelFreeProvenanceBundle,
    LabelFreeQuantTable,
    MultiplexNormalizationPolicy,
    MissingChannelPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
    build_label_based_quant_bundle,
    build_multiplex_channel_balance_report,
    normalize_label_free_table,
    summarize_missing_values,
)
from bijux_proteomics_foundation import JsonModel


class LfqFeaturePeptideProteinProvenanceReport(JsonModel):
    """Review-focused LFQ provenance with feature, peptide, and protein traceability."""

    model_config = ConfigDict(extra="forbid")

    provenance_bundle: LabelFreeProvenanceBundle
    peptide_missingness: MissingValueSummaryReport
    protein_missingness: MissingValueSummaryReport
    feature_entry_count: int = Field(..., ge=0)
    peptide_entry_count: int = Field(..., ge=0)
    protein_entry_count: int = Field(..., ge=0)
    normalization_method: NormalizationMethod
    note: str = Field(..., min_length=1)


def build_lfq_feature_peptide_protein_provenance_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    top_n: int = 3,
) -> LfqFeaturePeptideProteinProvenanceReport:
    """Build LFQ provenance preserving feature, peptide, protein, and missingness context."""
    bundle = build_label_free_provenance_bundle(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        top_n=top_n,
    )
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(peptide_table, method=normalization_method)
        protein_table = normalize_label_free_table(protein_table, method=normalization_method)

    peptide_missingness = summarize_missing_values(peptide_table)
    protein_missingness = summarize_missing_values(protein_table)
    return LfqFeaturePeptideProteinProvenanceReport(
        provenance_bundle=bundle,
        peptide_missingness=peptide_missingness,
        protein_missingness=protein_missingness,
        feature_entry_count=len(bundle.feature_entries),
        peptide_entry_count=len(bundle.peptide_entries),
        protein_entry_count=len(bundle.protein_entries),
        normalization_method=normalization_method,
        note=(
            "lfq provenance preserves feature-to-peptide-to-protein evidence while retaining missingness and normalization context"
        ),
    )


class LabelBasedQuantChannelLedgerEntry(JsonModel):
    """Ledger row for one multiplex channel and its review-critical context."""

    model_config = ConfigDict(extra="forbid")

    multiplex_group: str = Field(..., min_length=1)
    multiplex_channel: str = Field(..., min_length=1)
    normalization_group: str = Field(..., min_length=1)
    channel_role: LabelBasedChannelRole
    sample_id: str | None = None
    condition: str | None = None
    missing_channel: bool
    present_in_table: bool
    reagent_lot: str | None = None
    note: str = Field(..., min_length=1)


class LabelBasedQuantChannelLedgerReport(JsonModel):
    """Channel ledger for multiplex quantification review and handoff."""

    model_config = ConfigDict(extra="forbid")

    missing_channel_policy: MissingChannelPolicy
    entries: tuple[LabelBasedQuantChannelLedgerEntry, ...] = Field(default_factory=tuple)
    missing_channel_count: int = Field(..., ge=0)


def build_label_based_quant_channel_ledger(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: LabelBasedQuantPolicy,
    reagent_lot_by_channel: dict[tuple[str, str], str] | None = None,
) -> LabelBasedQuantChannelLedgerReport:
    """Build a channel-level ledger with role, missingness, and lot provenance."""
    lots = reagent_lot_by_channel or {}
    bundle = build_label_based_quant_bundle(
        table,
        design_entries=design_entries,
        policy=policy,
    )
    entries: list[LabelBasedQuantChannelLedgerEntry] = []
    for channel in bundle.channels:
        key = (channel.multiplex_group, channel.multiplex_channel)
        entries.append(
            LabelBasedQuantChannelLedgerEntry(
                multiplex_group=channel.multiplex_group,
                multiplex_channel=channel.multiplex_channel,
                normalization_group=channel.multiplex_group,
                channel_role=channel.channel_role,
                sample_id=channel.sample_id,
                condition=channel.condition,
                missing_channel=not channel.present_in_table,
                present_in_table=channel.present_in_table,
                reagent_lot=lots.get(key),
                note=channel.note,
            )
        )
    for missing in bundle.missing_channels:
        key = (missing.multiplex_group, missing.multiplex_channel)
        entries.append(
            LabelBasedQuantChannelLedgerEntry(
                multiplex_group=missing.multiplex_group,
                multiplex_channel=missing.multiplex_channel,
                normalization_group=missing.multiplex_group,
                channel_role=missing.expected_role,
                sample_id=None,
                condition=None,
                missing_channel=True,
                present_in_table=False,
                reagent_lot=lots.get(key),
                note=missing.message,
            )
        )
    deduped = {
        (entry.multiplex_group, entry.multiplex_channel, entry.sample_id): entry
        for entry in entries
    }
    ordered = tuple(
        sorted(
            deduped.values(),
            key=lambda entry: (
                entry.multiplex_group,
                entry.multiplex_channel,
                entry.sample_id or "",
            ),
        )
    )
    return LabelBasedQuantChannelLedgerReport(
        missing_channel_policy=policy.missing_channel_policy,
        entries=ordered,
        missing_channel_count=sum(1 for entry in ordered if entry.missing_channel),
    )


class MultiplexChannelBalanceDiagnosticsReport(JsonModel):
    """Expanded multiplex balance diagnostics with carrier and batch caveats."""

    model_config = ConfigDict(extra="forbid")

    policy: MultiplexNormalizationPolicy
    total_channel_count: int = Field(..., ge=0)
    flagged_imbalance_count: int = Field(..., ge=0)
    carrier_effect_channel_count: int = Field(..., ge=0)
    missing_channel_count: int = Field(..., ge=0)
    batch_caveat_count: int = Field(..., ge=0)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


def build_multiplex_channel_balance_diagnostics_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    quant_policy: LabelBasedQuantPolicy,
    normalization_policy: MultiplexNormalizationPolicy | None = None,
) -> MultiplexChannelBalanceDiagnosticsReport:
    """Build multiplex balance diagnostics with role-aware and batch-aware caveats."""
    active_norm_policy = normalization_policy or MultiplexNormalizationPolicy()
    balance = build_multiplex_channel_balance_report(
        table,
        design_entries=design_entries,
        policy=active_norm_policy,
    )
    ledger = build_label_based_quant_channel_ledger(
        table,
        design_entries=design_entries,
        policy=quant_policy,
    )
    flagged = tuple(entry for entry in balance.entries if entry.flagged)
    carrier_effect = tuple(
        entry
        for entry in flagged
        if entry.channel_role in {LabelBasedChannelRole.CARRIER, LabelBasedChannelRole.REFERENCE}
    )
    batch_by_sample = {
        entry.sample_id: entry.batch
        for entry in design_entries
        if entry.sample_id and entry.batch
    }
    batch_caveat_count = sum(
        1
        for entry in flagged
        if batch_by_sample.get(entry.sample_id) is not None
    )
    caveats: list[str] = []
    if flagged:
        caveats.append("one or more multiplex channels exceed configured balance ratio thresholds")
    if carrier_effect:
        caveats.append(
            "carrier/reference channels are among flagged channels and may distort ratio interpretation"
        )
    if ledger.missing_channel_count > 0:
        caveats.append(
            "missing multiplex channels were detected and should be reviewed alongside balance metrics"
        )
    if batch_caveat_count > 0:
        caveats.append(
            "some flagged channels map to batched samples; inspect potential batch-driven multiplex imbalance"
        )
    if not caveats:
        caveats.append("no multiplex balance caveats detected under the current policy")
    return MultiplexChannelBalanceDiagnosticsReport(
        policy=active_norm_policy,
        total_channel_count=len(balance.entries),
        flagged_imbalance_count=len(flagged),
        carrier_effect_channel_count=len(carrier_effect),
        missing_channel_count=ledger.missing_channel_count,
        batch_caveat_count=batch_caveat_count,
        caveats=tuple(caveats),
    )
