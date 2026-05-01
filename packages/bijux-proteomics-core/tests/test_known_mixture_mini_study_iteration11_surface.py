# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus_iteration11 import (
    KnownMixtureTruthBoundary,
    build_known_mixture_mini_study_bundle,
)


def test_build_known_mixture_mini_study_bundle_keeps_truth_boundaries_explicit() -> None:
    bundle = build_known_mixture_mini_study_bundle(
        study_id="mix-mini-01",
        mixture_asset_path="inputs/mixture.mzml",
        truth_reference_path="inputs/truth.tsv",
        boundaries=(
            KnownMixtureTruthBoundary(
                claim="relative abundance ordering is preserved for top 20 proteins",
                supported=True,
                caveat="does not imply absolute concentration calibration",
            ),
        ),
    )

    assert bundle.boundaries[0].supported is True
    assert "absolute concentration" in bundle.boundaries[0].caveat
