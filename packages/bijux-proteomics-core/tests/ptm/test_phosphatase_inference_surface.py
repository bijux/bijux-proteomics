# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm import (
    PtmPhosphataseSiteDirection,
    PtmPhosphataseSiteResult,
    PtmPhosphataseSubstrateAnnotation,
    infer_phosphatases,
    render_ptm_phosphatase_inference_tsv,
)


def test_infer_phosphatases_requires_exact_site_evidence_and_ignores_gene_only_rows() -> (
    None
):
    entries = infer_phosphatases(
        (
            PtmPhosphataseSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                signed_effect=-1.4,
            ),
        ),
        (
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PPP2CA",
                site_id="P11111:S5:Phospho",
                substrate_protein_id="P11111",
            ),
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PTPN11",
                substrate_protein_id="P11111",
            ),
        ),
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.phosphatase == "PPP2CA"
    assert entry.supporting_sites == ("P11111:S5:Phospho",)
    assert entry.site_directions == (PtmPhosphataseSiteDirection.DOWNREGULATED,)
    assert entry.annotation_coverage == 1.0


def test_infer_phosphatases_renders_required_surface_and_adjusts_q_values() -> None:
    entries = infer_phosphatases(
        (
            PtmPhosphataseSiteResult(
                site_id="P22222:S3:Phospho",
                protein_id="P22222",
                signed_effect=-1.1,
            ),
            PtmPhosphataseSiteResult(
                site_id="P22222:S8:Phospho",
                protein_id="P22222",
                signed_effect=-1.0,
            ),
            PtmPhosphataseSiteResult(
                site_id="P33333:T9:Phospho",
                protein_id="P33333",
                signed_effect=1.2,
            ),
            PtmPhosphataseSiteResult(
                site_id="P33333:Y12:Phospho",
                protein_id="P33333",
                signed_effect=-0.9,
            ),
        ),
        (
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PPP2CA",
                site_id="P22222:S3:Phospho",
            ),
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PPP2CA",
                site_id="P22222:S8:Phospho",
            ),
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PPP2CA",
                site_id="P99999:S40:Phospho",
            ),
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PTPN11",
                site_id="P33333:T9:Phospho",
            ),
            PtmPhosphataseSubstrateAnnotation(
                phosphatase="PTPN11",
                site_id="P33333:Y12:Phospho",
            ),
        ),
    )
    rendered = render_ptm_phosphatase_inference_tsv(entries)

    assert tuple(entry.phosphatase for entry in entries) == ("PPP2CA", "PTPN11")
    assert entries[0].p_value == 0.5
    assert entries[0].q_value == 1.0
    assert entries[0].annotation_coverage == 0.666667
    assert entries[1].site_directions == (
        PtmPhosphataseSiteDirection.UPREGULATED,
        PtmPhosphataseSiteDirection.DOWNREGULATED,
    )
    assert rendered.startswith(
        "phosphatase\tsupporting_sites\tsite_directions\tp_value\tq_value\tannotation_coverage\n"
    )
    assert (
        "PPP2CA\tP22222:S3:Phospho;P22222:S8:Phospho\tdownregulated;downregulated\t0.5\t1\t0.666667\n"
        in rendered
    )
