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
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.quantification.review import (
    build_label_based_quant_channel_ledger,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="lfq-001",
            sample_id="sample-a",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=1000.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="lfq-002",
            sample_id="sample-b",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            intensity=1100.0,
            protein_refs=("P11111",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="sample-a",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="a.mzml",
            multiplex_group="plex-1",
            multiplex_channel="126",
            sample_role=ExperimentalDesignSampleRole.SAMPLE,
        ),
        ExperimentalDesignEntry(
            sample_id="sample-b",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="b.mzml",
            multiplex_group="plex-1",
            multiplex_channel="127",
            sample_role=ExperimentalDesignSampleRole.POOLED_REFERENCE,
        ),
    )


def test_label_based_quant_channel_ledger_tracks_channel_roles_and_missing_channels() -> (
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
                multiplex_group="plex-1",
                multiplex_channel="126",
                channel_role=LabelBasedChannelRole.SAMPLE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-1",
                multiplex_channel="127",
                channel_role=LabelBasedChannelRole.REFERENCE,
            ),
            LabelBasedChannelPolicyEntry(
                multiplex_group="plex-1",
                multiplex_channel="128",
                channel_role=LabelBasedChannelRole.CARRIER,
            ),
        ),
    )
    ledger = build_label_based_quant_channel_ledger(
        table,
        design_entries=_design(),
        policy=policy,
        reagent_lot_by_channel={("plex-1", "127"): "LOT-42"},
    )

    assert len(ledger.entries) >= 3
    assert ledger.missing_channel_count >= 1
    reference_row = next(
        entry for entry in ledger.entries if entry.multiplex_channel == "127"
    )
    assert reference_row.channel_role is LabelBasedChannelRole.REFERENCE
    assert reference_row.reagent_lot == "LOT-42"
