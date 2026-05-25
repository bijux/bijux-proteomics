# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.ptm import (
    PtmOxidationSampleQcEntry,
    PtmOxidationSiteConfidence,
    PtmOxidizedPeptideObservation,
    detect_oxidation_artifacts,
    render_ptm_oxidation_artifact_tsv,
)


def test_detect_oxidation_artifacts_downgrades_site_specific_claims_under_high_global_oxidation() -> None:
    entries = detect_oxidation_artifacts(
        (
            PtmOxidizedPeptideObservation(
                sample_id="S1",
                peptide_id="pep-1",
                methionine_count=10,
                oxidized_methionine_count=1,
                site_localized=True,
            ),
            PtmOxidizedPeptideObservation(
                sample_id="S1",
                peptide_id="pep-2",
                methionine_count=10,
                oxidized_methionine_count=1,
                site_localized=True,
            ),
            PtmOxidizedPeptideObservation(
                sample_id="S2",
                peptide_id="pep-1",
                methionine_count=10,
                oxidized_methionine_count=5,
                site_localized=True,
            ),
            PtmOxidizedPeptideObservation(
                sample_id="S2",
                peptide_id="pep-2",
                methionine_count=10,
                oxidized_methionine_count=4,
                site_localized=True,
            ),
        ),
        (
            PtmOxidationSampleQcEntry(sample_id="S1", qc_score=0.92),
            PtmOxidationSampleQcEntry(sample_id="S2", qc_score=0.92),
        ),
    )
    by_sample = {entry.sample_id: entry for entry in entries}

    assert by_sample["S1"].methionine_oxidation_fraction == 0.1
    assert by_sample["S1"].global_oxidation_warning is False
    assert by_sample["S1"].site_specific_confidence is PtmOxidationSiteConfidence.SUPPORTED

    assert by_sample["S2"].methionine_oxidation_fraction == 0.45
    assert by_sample["S2"].global_oxidation_warning is True
    assert by_sample["S2"].site_specific_confidence is PtmOxidationSiteConfidence.DOWNGRADED


def test_detect_oxidation_artifacts_renders_surface_and_honors_sample_qc_blocks() -> None:
    entries = detect_oxidation_artifacts(
        (
            PtmOxidizedPeptideObservation(
                sample_id="blocked",
                peptide_id="pep-1",
                methionine_count=8,
                oxidized_methionine_count=1,
                site_localized=True,
            ),
            PtmOxidizedPeptideObservation(
                sample_id="blocked",
                peptide_id="pep-2",
                methionine_count=8,
                oxidized_methionine_count=1,
                site_localized=True,
            ),
        ),
        (
            PtmOxidationSampleQcEntry(
                sample_id="blocked",
                qc_score=0.8,
                blocked=True,
            ),
        ),
    )
    rendered = render_ptm_oxidation_artifact_tsv(entries)

    assert len(entries) == 1
    assert entries[0].site_specific_confidence is PtmOxidationSiteConfidence.DOWNGRADED
    assert rendered.startswith(
        "sample_id\tmethionine_oxidation_fraction\tglobal_oxidation_warning\tsite_specific_confidence\n"
    )
    assert "blocked\t0.125000\tfalse\tdowngraded\n" in rendered


def test_detect_oxidation_artifacts_requires_unique_sample_qc_rows() -> None:
    with pytest.raises(
        ValueError,
        match="oxidation artifact detection requires unique sample_qc rows",
    ):
        detect_oxidation_artifacts(
            (
                PtmOxidizedPeptideObservation(
                    sample_id="S1",
                    peptide_id="pep-1",
                    methionine_count=4,
                    oxidized_methionine_count=1,
                    site_localized=True,
                ),
            ),
            (
                PtmOxidationSampleQcEntry(sample_id="S1", qc_score=0.9),
                PtmOxidationSampleQcEntry(sample_id="S1", qc_score=0.8),
            ),
        )
