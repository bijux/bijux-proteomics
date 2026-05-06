# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.corpora import (
    ContradictionMiniStudyEntry,
    build_contradiction_mini_study_bundle,
)


def test_build_contradiction_mini_study_bundle_preserves_multi_surface_disagreement() -> (
    None
):
    bundle = build_contradiction_mini_study_bundle(
        study_id="contradiction-mini-01",
        entries=(
            ContradictionMiniStudyEntry(
                contradiction_id="cx-1",
                engine_disagreement="engine-a supports peptide, engine-b rejects peptide",
                quant_disagreement="lfq upregulated while dia unchanged",
                ptm_disagreement="site S34 localized in one run only",
                qc_disagreement="batch-2 fails precursor error threshold",
                lab_disagreement="validation assay did not confirm enrichment",
            ),
        ),
    )

    assert bundle.entries[0].contradiction_id == "cx-1"
    assert "did not confirm" in bundle.entries[0].lab_disagreement
