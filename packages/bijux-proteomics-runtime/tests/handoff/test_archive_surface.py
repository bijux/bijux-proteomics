# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import shutil

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
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
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    ProteomicsStudyKind,
    build_biological_result_report_bundle,
    build_result_manifest_from_artifacts,
    export_biological_result_report_bundle,
)
from bijux_proteomics_runtime.handoff import (
    build_handoff_archive,
    load_handoff_archive,
)

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


def _ptm_design_entries() -> tuple[ExperimentalDesignEntry, ...]:
    return tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )


def _write_run_qc_tsv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
        complex_membership_tsv_path=_workflow_fixture(
            "biological_report_complexes.tsv"
        ),
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
    ptm_annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
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


def test_build_handoff_archive_loads_and_queries_without_original_run_tree(
    tmp_path: Path,
) -> None:
    biological_report_dir = _write_biological_report_dir(tmp_path)
    ptm_report_dir = _write_ptm_report_dir(tmp_path)
    run_qc_path = tmp_path / "qc" / "run_qc.tsv"
    _write_run_qc_tsv(run_qc_path)
    run_dir = tmp_path / "artifacts" / "completed-run"
    _write_result_manifest_json(
        archive_dir=run_dir,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_paths=(run_qc_path,),
    )
    archive_path = tmp_path / "portable" / "collaborator_handoff_archive.json"

    built_archive = build_handoff_archive(run_dir, archive_path)

    assert built_archive.result.study_kind is ProteomicsStudyKind.ARCHIVED
    assert built_archive.cards
    assert built_archive.qc_packets
    assert built_archive.claims
    assert built_archive.belief_audit.entries
    assert built_archive.manifest.summary.protein_count > 0
    assert archive_path.exists()

    shutil.rmtree(run_dir)
    shutil.rmtree(biological_report_dir)
    shutil.rmtree(ptm_report_dir)
    run_qc_path.unlink()

    loaded_archive = load_handoff_archive(archive_path)

    protein = loaded_archive.query_archived_protein(
        object_id=loaded_archive.result.interactive_result_bundle.proteins[0].object_id
    )
    pathway = loaded_archive.query_archived_pathway(
        pathway_id=loaded_archive.result.interactive_result_bundle.pathways[
            0
        ].pathway_id
    )

    assert protein.representative_protein_ref
    assert pathway.pathway_id
    assert loaded_archive.graph.nodes
    assert loaded_archive.summary.belief_audit_entry_count > 0


def test_load_handoff_archive_rejects_tampered_archive_sha256(tmp_path: Path) -> None:
    biological_report_dir = _write_biological_report_dir(tmp_path)
    run_dir = tmp_path / "artifacts" / "completed-run"
    _write_result_manifest_json(
        archive_dir=run_dir,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=None,
    )
    archive_path = tmp_path / "portable" / "collaborator_handoff_archive.json"
    build_handoff_archive(run_dir, archive_path)
    payload = json.loads(archive_path.read_text(encoding="utf-8"))
    archive_sha256 = payload["summary"]["archive_sha256"]
    replacement_prefix = "0" if archive_sha256[0] != "0" else "1"
    payload["summary"]["archive_sha256"] = replacement_prefix + archive_sha256[1:]
    archive_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        load_handoff_archive(archive_path)
    except ValueError as exc:
        assert "handoff archive sha256" in str(exc)
    else:
        raise AssertionError("tampered handoff archive must be rejected")
