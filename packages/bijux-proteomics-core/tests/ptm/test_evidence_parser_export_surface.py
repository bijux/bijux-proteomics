# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    parse_ptm_localization_tsv,
    render_ptm_evidence_site_candidate_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def test_ptm_evidence_candidate_renderer_keeps_multi_modified_sites_separate() -> None:
    report = parse_ptm_localization_tsv(_fixture_path("multi_localization_results.tsv"))

    candidate_tsv = render_ptm_evidence_site_candidate_tsv(report)

    assert (
        "C1\tscan=ptm-multi-001\tAS[Phospho]TY[Phospho]K\tAS[Phospho]TY[Phospho]K\tP11111;P22222\tPhospho\tUNIMOD:21\tS\t2"
        in candidate_tsv
    )
    assert (
        "C1\tscan=ptm-multi-001\tAS[Phospho]TY[Phospho]K\tAS[Phospho]TY[Phospho]K\tP11111;P22222\tPhospho\tUNIMOD:21\tY\t4"
        in candidate_tsv
    )
