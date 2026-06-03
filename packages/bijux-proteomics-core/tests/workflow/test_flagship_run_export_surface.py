# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    ProteomicsRunEngine,
    build_proteomics_run_bundle,
    export_proteomics_run_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _fixture("maxquant_biological") / name


def test_export_proteomics_run_bundle_writes_canonical_outputs_for_diann(
    tmp_path: Path,
) -> None:
    metadata_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.DIANN,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_fixture("diann_biological_report.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
    )

    manifest = export_proteomics_run_bundle(report, tmp_path)

    assert manifest.summary.engine is ProteomicsRunEngine.DIANN
    assert (tmp_path / manifest.artifacts.summary_tsv).exists()
    assert (tmp_path / manifest.artifacts.qc_summary_tsv).exists()
    assert (tmp_path / manifest.artifacts.normalized_matrix_tsv).exists()
    assert (tmp_path / manifest.artifacts.differential_tsv).exists()
    assert (tmp_path / manifest.artifacts.enrichment_tsv).exists()
    assert (tmp_path / manifest.artifacts.report_html).exists()
    assert (tmp_path / manifest.artifacts.workflow_manifest_json).exists()
    assert "entity_id\tprotein_refs\tmember_peptides\tC1" in (
        tmp_path / manifest.artifacts.normalized_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "source_kind\tsource_name\tentry_id\tentry_name" in (
        tmp_path / manifest.artifacts.enrichment_tsv
    ).read_text(encoding="utf-8")
    assert (
        "<html"
        in (tmp_path / manifest.artifacts.report_html)
        .read_text(encoding="utf-8")
        .lower()
    )


def test_export_proteomics_run_bundle_writes_canonical_outputs_for_fragpipe(
    tmp_path: Path,
) -> None:
    metadata_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.FRAGPIPE,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_fixture("fragpipe_biological_psms.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
    )

    manifest = export_proteomics_run_bundle(report, tmp_path)

    assert manifest.summary.engine is ProteomicsRunEngine.FRAGPIPE
    assert (tmp_path / manifest.artifacts.summary_tsv).exists()
    assert (tmp_path / manifest.artifacts.qc_summary_tsv).exists()
    assert (tmp_path / manifest.artifacts.normalized_matrix_tsv).exists()
    assert (tmp_path / manifest.artifacts.differential_tsv).exists()
    assert (tmp_path / manifest.artifacts.enrichment_tsv).exists()
    assert (tmp_path / manifest.artifacts.report_html).exists()
    assert "P04637" in (tmp_path / manifest.artifacts.normalized_matrix_tsv).read_text(
        encoding="utf-8"
    )
    assert "go\tgene_ontology" in (
        tmp_path / manifest.artifacts.enrichment_tsv
    ).read_text(encoding="utf-8")
