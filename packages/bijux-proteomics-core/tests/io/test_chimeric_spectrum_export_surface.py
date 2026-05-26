# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.io import (
    parse_mzml,
    render_chimeric_spectrum_competing_evidence_tsv,
    render_chimeric_spectrum_spectra_tsv,
    score_chimeric_spectra_from_psms,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "psm" / name


def _default_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value="q_value",
        protein_refs="proteins",
    )


def test_render_chimeric_spectrum_exports_keep_competing_evidence_visible() -> None:
    spectra = parse_mzml(_format_fixture("chimeric_spectrum_review.mzml")).accepted_spectra
    psm_records = parse_psm_tsv(
        _psm_fixture("chimeric_spectrum_candidates.tsv"),
        mapping=_default_mapping(),
    ).accepted_records

    report = score_chimeric_spectra_from_psms(spectra, psm_records)
    spectra_tsv = render_chimeric_spectrum_spectra_tsv(report)
    competition_tsv = render_chimeric_spectrum_competing_evidence_tsv(report)

    assert (
        "scan=9002\t400.687246\t400.687246\t399.687246\t401.687246\t2\tPEPTIDE\t2\t48.0000"
        in spectra_tsv
    )
    assert "\tTIDEPEP\t0.1500\t0.1500\tfalse\t" in spectra_tsv
    assert "scan=9002\tTIDEPEP\t2\tP22222\t45.0000\t400.687246\t" in competition_tsv
    assert "\ttrue\t0.0000\t0.0000\t0\t0\t0\t0.1500\t" in competition_tsv
