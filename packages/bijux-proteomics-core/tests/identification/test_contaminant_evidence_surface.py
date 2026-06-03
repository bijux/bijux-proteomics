# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.contaminant_evidence import (
    build_contaminant_evidence_report,
    render_contaminant_burden_tsv,
    render_contaminant_proteins_tsv,
)
from bijux_proteomics.identification.search_adapters import parse_psm_tsv

from .test_identification_surface import _default_mapping


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "psm" / name


def test_contaminant_evidence_report_separates_psms_peptides_proteins_and_burden() -> (
    None
):
    report = parse_psm_tsv(
        _psm_fixture("contaminant_burden_results.tsv"),
        mapping=_default_mapping().model_copy(
            update={"run_id": "run_id", "intensity": "intensity"}
        ),
    )

    evidence = build_contaminant_evidence_report(
        report.accepted_records,
        sample_id_by_run={"run-a": "sample-a", "run-b": "sample-b"},
        warning_psm_fraction=0.6,
        warning_intensity_fraction=0.4,
    )

    run_a = next(entry for entry in evidence.burden_entries if entry.run_id == "run-a")
    run_b = next(entry for entry in evidence.burden_entries if entry.run_id == "run-b")

    assert evidence.summary.contaminant_psm_count == 3
    assert evidence.summary.contaminant_peptide_count == 3
    assert evidence.summary.contaminant_protein_count == 2
    assert evidence.summary.burdened_run_count == 1
    assert evidence.summary.burdened_sample_count == 1
    assert evidence.summary.contaminant_intensity_fraction == 1050.0 / 2950.0
    assert run_a.sample_id == "sample-a"
    assert run_a.contaminant_psm_count == 2
    assert run_a.contaminant_intensity_fraction == 0.5
    assert run_a.heavy_contaminant_warning is True
    assert run_b.sample_id == "sample-b"
    assert run_b.contaminant_psm_count == 1
    assert run_b.contaminant_intensity_fraction == 50.0 / 950.0
    assert run_b.heavy_contaminant_warning is False
    top_protein = evidence.protein_entries[0]
    assert top_protein.protein_ref == "CON__K1C10_HUMAN"
    assert top_protein.psm_count == 2
    assert top_protein.intensity_sum == 850.0

    burden_tsv = render_contaminant_burden_tsv(evidence)
    proteins_tsv = render_contaminant_proteins_tsv(evidence)

    assert "run-a\tsample-a\t3\t2" in burden_tsv
    assert (
        "CON__K1C10_HUMAN\trun-a;run-b\tsample-a;sample-b\t2\t2\t850.0" in proteins_tsv
    )
