# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.chemistry.stable_isotope_labeling import (
    StableIsotopeLabelChannel,
    StableIsotopeLabelChemistry,
    build_stable_isotope_labeling_model,
)


def test_build_stable_isotope_labeling_model_supports_tmt_channels() -> None:
    model = build_stable_isotope_labeling_model(
        chemistry=StableIsotopeLabelChemistry.TMT,
        channels=(
            StableIsotopeLabelChannel(
                channel_id="126",
                sample_id="sample_a",
                label_name="TMT126",
                reporter_mz=126.127726,
                normalization_group="plex_1",
            ),
            StableIsotopeLabelChannel(
                channel_id="127N",
                sample_id="sample_b",
                label_name="TMT127N",
                reporter_mz=127.124761,
                normalization_group="plex_1",
            ),
        ),
        quant_rule="reporter_ion_ratio",
        reference_channel_id="126",
    )

    assert model.chemistry is StableIsotopeLabelChemistry.TMT
    assert model.reference_channel_id == "126"
    assert len(model.channels) == 2


def test_build_stable_isotope_labeling_model_rejects_missing_reporter_mz_for_tmt() -> (
    None
):
    with pytest.raises(ValueError, match="reporter_mz"):
        build_stable_isotope_labeling_model(
            chemistry=StableIsotopeLabelChemistry.TMT,
            channels=(
                StableIsotopeLabelChannel(
                    channel_id="126",
                    sample_id="sample_a",
                    label_name="TMT126",
                    normalization_group="plex_1",
                ),
            ),
            quant_rule="reporter_ion_ratio",
        )
