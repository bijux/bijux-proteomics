# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    build_ptm_report_bundle,
    export_ptm_report_bundle,
    parse_ptm_localization_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.review import query_protein_evidence_summary
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    ProteomicsStudyKind,
    build_biological_result_report_bundle,
    build_result_manifest_from_artifacts,
    export_biological_result_report_bundle,
    render_interactive_result_bundle_summary_tsv,
)
from bijux_proteomics_runtime.rehydrate import load_completed_run

_RUNTIME_TESTS_DIR = Path(__file__).resolve().parents[1]
_CORE_FIXTURES_DIR = (
    _RUNTIME_TESTS_DIR.parents[2]
    / "packages"
    / "bijux-proteomics-core"
    / "tests"
    / "fixtures"
)


def _workflow_fixture(name: str) -> Path:
    return _CORE_FIXTURES_DIR / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return _CORE_FIXTURES_DIR / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return _CORE_FIXTURES_DIR / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _ptm_design_entries():
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def _write_run_qc_tsv(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                "run\tt2.mzml\tfail\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\tfailed\tblock\ttrue\tidentification rate fell below enforced threshold",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_biological_report_dir(tmp_path: Path) -> Path:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    output_dir = tmp_path / "biological_report"
    manifest = export_biological_result_report_bundle(report, output_dir)
    (output_dir / "biological_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return output_dir


def _write_ptm_report_dir(tmp_path: Path) -> Path:
    ptm_evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    ptm_features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    ptm_annotations = parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    report = build_ptm_report_bundle(
        ptm_evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=ptm_features.accepted_records,
        design_entries=_ptm_design_entries(),
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        condition_a="control",
        condition_b="treated",
        annotation_records=ptm_annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )
    output_dir = tmp_path / "ptm_report"
    manifest = export_ptm_report_bundle(report, output_dir)
    (output_dir / "ptm_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return output_dir


def _write_result_manifest_json(
    *,
    archive_dir: Path,
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_paths: tuple[Path, ...] = (),
) -> Path:
    report = build_result_manifest_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_paths,
        input_paths=(
            _workflow_fixture("biological_report_features.tsv"),
            _workflow_fixture("biological_report.design.tsv"),
        ),
        commands=(
            "biological-report biological_report_features.tsv biological_report.design.tsv biological_report_reference.fasta",
            "ptm-site-report localization_results.tsv ptm_features.tsv ptm.design.tsv",
        ),
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_dir / "result_manifest.json"
    manifest_path.write_text(report.to_stable_json() + "\n", encoding="utf-8")
    return manifest_path


def test_load_completed_run_rehydrates_queries_and_regenerates_bundle_summary_without_workflow_rerun(
    tmp_path: Path,
    monkeypatch,
) -> None:
    biological_report_dir = _write_biological_report_dir(tmp_path)
    ptm_report_dir = _write_ptm_report_dir(tmp_path)
    run_qc_path = tmp_path / "run_qc.tsv"
    _write_run_qc_tsv(run_qc_path)
    run_dir = tmp_path / "artifacts" / "completed-run"
    manifest_path = _write_result_manifest_json(
        archive_dir=run_dir,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_paths=(run_qc_path,),
    )

    def _forbid_rerun(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("scientific report builders must not rerun during rehydration")

    monkeypatch.setattr(
        "bijux_proteomics.workflow.build_biological_result_report_bundle",
        _forbid_rerun,
    )
    monkeypatch.setattr(
        "bijux_proteomics.workflow.build_ptm_report_bundle",
        _forbid_rerun,
    )

    result = load_completed_run(run_dir)

    assert result.study_kind is ProteomicsStudyKind.ARCHIVED
    assert result.archive_manifest is not None
    assert result.interactive_result_bundle is not None
    assert result.archived_evidence_graph is not None
    assert result.query_archived_protein(
        object_id=result.interactive_result_bundle.proteins[0].object_id
    ).representative_protein_ref
    graph = result.archived_evidence_graph
    protein_node_id = next(
        node.entity_ref for node in graph.nodes if node.entity_type.value == "protein"
    )
    assert query_protein_evidence_summary(graph, protein_id=protein_node_id).support_edge_count > 0
    summary_tsv = render_interactive_result_bundle_summary_tsv(
        result.interactive_result_bundle
    )
    assert "sample_count" in summary_tsv
    assert manifest_path.exists()


def test_load_completed_run_resolves_nested_archive_manifest_directory(tmp_path: Path) -> None:
    biological_report_dir = _write_biological_report_dir(tmp_path)
    run_dir = tmp_path / "artifacts" / "completed-run"
    _write_result_manifest_json(
        archive_dir=run_dir / "archive",
        biological_report_dir=biological_report_dir,
        ptm_report_dir=None,
    )

    result = load_completed_run(run_dir)

    assert result.interactive_result_bundle is not None
    assert result.interactive_result_bundle.summary.protein_count > 0
