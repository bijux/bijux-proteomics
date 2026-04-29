# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from bijux_proteomics import (
    FastaParseMode,
    QcEvidenceInputFile,
    QuantEntityLevel,
    QuantRollupMethod,
    SearchResultColumnMapping,
    build_label_free_intensity_table,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_qc_evidence_manifest,
    build_run_qc_assessment,
    default_qc_threshold_policy,
    parse_experimental_design_table,
    parse_fasta_document,
    parse_mgf,
    parse_ms1_feature_table,
    parse_psm_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "production_run" / name


def test_production_run_fixture_covers_identify_quant_and_qc() -> None:
    design = parse_experimental_design_table(_fixture("design.tsv")).accepted_entries[0]
    fasta_report = parse_fasta_document(
        _fixture("proteins.fasta").read_text(), mode=FastaParseMode.STRICT
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    psm_report = parse_psm_tsv(
        _fixture("results.tsv"),
        mapping=SearchResultColumnMapping(
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            protein_refs="proteins",
        ),
    )
    spectrum_report = parse_mgf(_fixture("spectra.mgf"))
    feature_report = parse_ms1_feature_table(_fixture("ms1_features.tsv"))
    quant_table = build_label_free_intensity_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )

    run_report = build_lcms_run_qc_report(
        spectrum_report.accepted_spectra,
        psm_report.accepted_records,
        design_entry=design,
        protein_sequences=protein_sequences,
    )
    run_assessment = build_run_qc_assessment(
        run_report,
        policy=default_qc_threshold_policy().model_copy(
            update={"policy_name": "demo-policy"}
        ),
    )

    assert len(psm_report.accepted_records) == 2
    assert spectrum_report.accepted_spectra[0].spectrum_id == "scan=9001"
    assert quant_table.entity_ids == ("P00001",)
    assert run_report.run_id == "spectra"
    assert run_assessment.metric_assessments


def test_production_run_fixture_manifest_hashes_match_payload() -> None:
    manifest = json.loads(_fixture("fixture_manifest.json").read_text())
    for entry in manifest["files"]:
        path = _fixture(entry["path"])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"]


def test_production_run_builds_qc_manifest_and_benchmark_artifacts() -> None:
    design = parse_experimental_design_table(_fixture("design.tsv")).accepted_entries[0]
    fasta_report = parse_fasta_document(
        _fixture("proteins.fasta").read_text(), mode=FastaParseMode.STRICT
    )
    protein_sequences = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }

    started = time.perf_counter()
    psm_report = parse_psm_tsv(
        _fixture("results.tsv"),
        mapping=SearchResultColumnMapping(
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            protein_refs="proteins",
        ),
    )
    parse_psms_elapsed = time.perf_counter() - started

    started = time.perf_counter()
    spectrum_report = parse_mgf(_fixture("spectra.mgf"))
    parse_spectra_elapsed = time.perf_counter() - started

    started = time.perf_counter()
    run_report = build_lcms_run_qc_report(
        spectrum_report.accepted_spectra,
        psm_report.accepted_records,
        design_entry=design,
        protein_sequences=protein_sequences,
    )
    run_assessment = build_run_qc_assessment(
        run_report, policy=default_qc_threshold_policy()
    )
    build_qc_elapsed = time.perf_counter() - started

    benchmark = build_performance_snapshot(
        run_report.run_id,
        operations={
            "parse_psms": (parse_psms_elapsed, len(psm_report.accepted_records)),
            "parse_spectra": (
                parse_spectra_elapsed,
                len(spectrum_report.accepted_spectra),
            ),
            "build_run_qc": (build_qc_elapsed, len(run_assessment.metric_assessments)),
        },
    )
    manifest = build_qc_evidence_manifest(
        run_report=run_report,
        run_assessment=run_assessment,
        policy=default_qc_threshold_policy(),
        input_files=(
            QcEvidenceInputFile(path="spectra.mgf", sha256="a" * 64, role="spectra"),
            QcEvidenceInputFile(
                path="results.tsv", sha256="b" * 64, role="identifications"
            ),
            QcEvidenceInputFile(
                path="proteins.fasta", sha256="c" * 64, role="proteins"
            ),
        ),
        benchmark=benchmark,
    )

    assert benchmark.operations
    assert manifest.benchmark_sha256
