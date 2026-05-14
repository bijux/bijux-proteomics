# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.quantification import (
    LabelBasedChannelPolicyEntry,
    LabelBasedChannelRole,
    LabelBasedQuantPolicy,
    MissingChannelPolicy,
    MissingValueKind,
    Ms1FeatureRecord,
    MultiplexNormalizationPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.review import (
    build_multiplex_channel_balance_diagnostics_report,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="mx-001",
            sample_id="s-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=1000.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="mx-002",
            sample_id="s-b",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=3000.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="s-a",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="a.mzml",
            batch="b1",
            multiplex_group="plex-a",
            multiplex_channel="126",
            sample_role=ExperimentalDesignSampleRole.SAMPLE,
        ),
        ExperimentalDesignEntry(
            sample_id="s-b",
            condition="ctrl",
            replicate=1,
            fraction=1,
            spectra_file="b.mzml",
            batch="b1",
            multiplex_group="plex-a",
            multiplex_channel="127",
            sample_role=ExperimentalDesignSampleRole.POOLED_REFERENCE,
        ),
    )


def test_multiplex_channel_balance_diagnostics_report_flags_imbalance_and_caveats() -> (
    None
):
    table = build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=QuantRollupMethod.SUM,
    )
    policy = LabelBasedQuantPolicy(
        missing_channel_policy=MissingChannelPolicy.PRESERVE,
        channel_entries=(
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="127",
                channel_role=LabelBasedChannelRole.REFERENCE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-a",
                multiplex_channel="128",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
        ),
    )
    diagnostics = build_multiplex_channel_balance_diagnostics_report(
        table,
        design_entries=_design(),
        quant_policy=policy,
        normalization_policy=MultiplexNormalizationPolicy(balance_ratio_threshold=1.1),
    )

    assert diagnostics.total_channel_count == 2
    assert diagnostics.flagged_imbalance_count >= 1
    assert diagnostics.missing_channel_count >= 1
    assert len(diagnostics.caveats) >= 1
