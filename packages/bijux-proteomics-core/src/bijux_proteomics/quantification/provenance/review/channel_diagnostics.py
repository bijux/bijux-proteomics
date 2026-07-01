# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Channel-ledger and normalization-diagnostics review builders."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    LabelFreeQuantTable,
    MultiplexNormalizationPolicy,
    NormalizationMethod,
    build_label_based_quant_bundle,
    build_multiplex_channel_balance_report,
)
from bijux_proteomics.quantification.normalization import (
    build_normalization_strategy_comparison_report,
)
from bijux_proteomics.quantification.provenance.review.models import (
    LabelBasedQuantChannelLedgerEntry,
    LabelBasedQuantChannelLedgerReport,
    MultiplexChannelBalanceDiagnosticsReport,
    NormalizationPolicyComparisonEntry,
    NormalizationPolicyComparisonMatrixReport,
    QuantNormalizationPolicyKind,
)


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
        if entry.channel_role
        in {LabelBasedChannelRole.CARRIER, LabelBasedChannelRole.REFERENCE}
    )
    batch_by_sample = {
        entry.sample_id: entry.batch
        for entry in design_entries
        if entry.sample_id and entry.batch
    }
    batch_caveat_count = sum(
        1 for entry in flagged if batch_by_sample.get(entry.sample_id) is not None
    )
    caveats: list[str] = []
    if flagged:
        caveats.append(
            "one or more multiplex channels exceed configured balance ratio thresholds"
        )
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


def build_normalization_policy_comparison_matrix_report(
    table: LabelFreeQuantTable,
) -> NormalizationPolicyComparisonMatrixReport:
    """Compare normalization policies and preserve unsupported states explicitly."""
    strategy = build_normalization_strategy_comparison_report(
        table,
        methods=(
            NormalizationMethod.NONE,
            NormalizationMethod.TIC,
            NormalizationMethod.MEDIAN,
            NormalizationMethod.QUANTILE,
            NormalizationMethod.LOG2_MEDIAN_CENTERING,
            NormalizationMethod.VSN_LIKE,
        ),
    )
    score_by_method = {entry.method: entry.balance_score for entry in strategy.entries}
    entries = (
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.NONE,
            supported=True,
            mapped_method=NormalizationMethod.NONE,
            balance_score=score_by_method.get(NormalizationMethod.NONE),
            note="no-normalization policy is directly supported",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.TOTAL,
            supported=True,
            mapped_method=NormalizationMethod.TIC,
            balance_score=score_by_method.get(NormalizationMethod.TIC),
            note="total-intensity normalization is mapped to TIC support",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.MEDIAN,
            supported=True,
            mapped_method=NormalizationMethod.MEDIAN,
            balance_score=score_by_method.get(NormalizationMethod.MEDIAN),
            note="median normalization is supported natively",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.QUANTILE,
            supported=True,
            mapped_method=NormalizationMethod.QUANTILE,
            balance_score=score_by_method.get(NormalizationMethod.QUANTILE),
            note="quantile normalization is supported natively",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.LOG2_MEDIAN_CENTERING,
            supported=True,
            mapped_method=NormalizationMethod.LOG2_MEDIAN_CENTERING,
            balance_score=score_by_method.get(
                NormalizationMethod.LOG2_MEDIAN_CENTERING
            ),
            note="log2 median-centering is supported with explicit nonpositive-value handling before log transform",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.VSN_LIKE,
            supported=True,
            mapped_method=NormalizationMethod.VSN_LIKE,
            balance_score=score_by_method.get(NormalizationMethod.VSN_LIKE),
            note="vsn-like normalization is supported through log-scale median centering",
        ),
        NormalizationPolicyComparisonEntry(
            policy=QuantNormalizationPolicyKind.REFERENCE_CHANNEL,
            supported=False,
            mapped_method=None,
            balance_score=None,
            note="reference-channel normalization requires dedicated channel-aware transforms and is not currently supported",
        ),
    )
    recommended_supported = next(
        (
            entry.policy
            for entry in entries
            if entry.supported and entry.mapped_method is strategy.recommended_method
        ),
        None,
    )
    return NormalizationPolicyComparisonMatrixReport(
        entries=entries,
        recommended_supported_policy=recommended_supported,
    )


__all__ = [
    "build_label_based_quant_channel_ledger",
    "build_multiplex_channel_balance_diagnostics_report",
    "build_normalization_policy_comparison_matrix_report",
]
