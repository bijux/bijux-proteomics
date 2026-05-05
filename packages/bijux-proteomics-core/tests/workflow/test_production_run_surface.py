# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from bijux_proteomics.identification import SearchResultColumnMapping, parse_psm_tsv
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.spectra import parse_mgf
from bijux_proteomics.qc import (
    QcEvidenceInputFile,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_qc_evidence_manifest,
    build_run_qc_assessment,
    default_qc_threshold_policy,
)
from bijux_proteomics.quantification import (
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_runtime.workflows.plans import (
    WorkflowTemplateKind,
    build_proteomics_workflow_runtime_bundle,
    build_proteomics_workflow_template,
    build_reproducible_workflow_blueprint,
    build_workflow_runtime_validation_report,
    instantiate_proteomics_workflow_template,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "production_run" / name


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


def test_production_run_workflow_fixtures_validate_imported_and_external_paths() -> (
    None
):
    expectations = json.loads(
        _fixture("workflow_end_to_end_expectations.json").read_text(encoding="utf-8")
    )

    imported_template = build_proteomics_workflow_template(
        WorkflowTemplateKind.IMPORTED_LFQ_REVIEW
    )
    imported_manifest = instantiate_proteomics_workflow_template(
        imported_template,
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
    )
    imported_blueprint = build_reproducible_workflow_blueprint(imported_manifest)
    imported_bundle = build_proteomics_workflow_runtime_bundle(
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        identifications_path=_fixture("results.tsv"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
    )
    imported_validation = build_workflow_runtime_validation_report(imported_bundle)

    external_template = build_proteomics_workflow_template(
        WorkflowTemplateKind.EXTERNAL_SEARCH_LFQ_REVIEW
    )
    external_manifest = instantiate_proteomics_workflow_template(
        external_template,
        proteins_path=_fixture("proteins.fasta"),
        spectra_path=_fixture("spectra.mgf"),
        features_path=_fixture("ms1_features.tsv"),
        design_path=_fixture("design.tsv"),
        sample_id="sample-A",
    )
    external_blueprint = build_reproducible_workflow_blueprint(external_manifest)

    imported_expected = expectations["imported_lfq_review"]
    external_expected = expectations["external_search_lfq_review"]

    assert imported_manifest.execution_mode.value == imported_expected["execution_mode"]
    assert [step.kind.value for step in imported_manifest.steps] == imported_expected[
        "step_kinds"
    ]
    assert sorted(
        {step.scientific_surface.value for step in imported_blueprint.steps}
    ) == sorted(imported_expected["scientific_surfaces"])
    assert imported_validation.valid is True

    assert external_manifest.execution_mode.value == external_expected["execution_mode"]
    assert [step.kind.value for step in external_manifest.steps] == external_expected[
        "step_kinds"
    ]
    assert sorted(
        {step.scientific_surface.value for step in external_blueprint.steps}
    ) == sorted(external_expected["scientific_surfaces"])
