# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
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
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.workflow import (
    InteractiveResultComparisonReasonCode,
    build_biological_result_report_bundle,
    build_result_manifest_from_artifacts,
    export_biological_result_report_bundle,
)
from bijux_proteomics_runtime.diff import diff_completed_runs

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


def _rewrite_first_tsv_row(path: Path, updates: dict[str, str]) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        rows = list(reader)
        if not rows:
            raise ValueError(f"{path.name!r} must include at least one data row")
        rows[0].update(updates)
        fieldnames = list(reader.fieldnames)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _write_run_qc_tsv(
    path: Path,
    *,
    qc_status: str,
    severity: str,
    message: str,
) -> None:
    path.write_text(
        "\n".join(
            (
                "scope\tentity_id\tqc_status\tstatus_reason_codes\tmetric_key\tmetric_label\tobserved_value\tunit\tseverity\tdisposition\tenforced_violation\tmessage",
                (
                    "run\tt2.mzml\t"
                    f"{qc_status}\tidentification_rate_low\tidentification_rate\tIdentification rate\t0.05\tfraction\t"
                    f"{severity}\tblock\ttrue\t{message}"
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_biological_report_dir(
    tmp_path: Path,
    *,
    output_name: str,
    protein_updates: dict[str, str] | None = None,
    pathway_updates: dict[str, str] | None = None,
    hypothesis_updates: dict[str, str] | None = None,
) -> Path:
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
    output_dir = tmp_path / output_name
    manifest = export_biological_result_report_bundle(report, output_dir)
    (output_dir / "biological_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    if protein_updates is not None:
        _rewrite_first_tsv_row(
            output_dir / manifest.artifacts.protein_card_tsv, protein_updates
        )
    if (
        pathway_updates is not None
        and manifest.artifacts.pathway_activity_condition_comparison_tsv
    ):
        _rewrite_first_tsv_row(
            output_dir / manifest.artifacts.pathway_activity_condition_comparison_tsv,
            pathway_updates,
        )
    if hypothesis_updates is not None and manifest.artifacts.biological_hypothesis_tsv:
        _rewrite_first_tsv_row(
            output_dir / manifest.artifacts.biological_hypothesis_tsv,
            hypothesis_updates,
        )
    return output_dir


def _write_ptm_report_dir(
    tmp_path: Path,
    *,
    output_name: str,
    evidence_card_updates: dict[str, str] | None = None,
) -> Path:
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
    output_dir = tmp_path / output_name
    manifest = export_ptm_report_bundle(report, output_dir)
    (output_dir / "ptm_report_manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )
    if evidence_card_updates is not None and manifest.artifacts.evidence_card_tsv:
        _rewrite_first_tsv_row(
            output_dir / manifest.artifacts.evidence_card_tsv,
            evidence_card_updates,
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


def test_diff_completed_runs_reports_scientific_changes_across_rehydrated_outputs(
    tmp_path: Path,
) -> None:
    left_biological_report_dir = _write_biological_report_dir(
        tmp_path,
        output_name="left-biological-report",
        protein_updates={"log2_fold_change": "1.75", "evidence_tier": "high"},
        pathway_updates={
            "comparison_confidence_status": "supported",
            "activity_score_delta": "1.25",
        },
        hypothesis_updates={"confidence_tier": "high", "confidence_score": "0.91"},
    )
    right_biological_report_dir = _write_biological_report_dir(
        tmp_path,
        output_name="right-biological-report",
        protein_updates={"log2_fold_change": "0.25", "evidence_tier": "moderate"},
        pathway_updates={
            "comparison_confidence_status": "weak",
            "activity_score_delta": "0.10",
        },
        hypothesis_updates={"confidence_tier": "weak", "confidence_score": "0.31"},
    )
    left_ptm_report_dir = _write_ptm_report_dir(
        tmp_path,
        output_name="left-ptm-report",
        evidence_card_updates={
            "localization_tier": "localized",
            "protein_correction_status": "high_confidence_corrected",
        },
    )
    right_ptm_report_dir = _write_ptm_report_dir(
        tmp_path,
        output_name="right-ptm-report",
        evidence_card_updates={
            "localization_tier": "ambiguous",
            "protein_correction_status": "uncorrected",
        },
    )
    left_run_qc_path = tmp_path / "left-qc" / "run_qc.tsv"
    right_run_qc_path = tmp_path / "right-qc" / "run_qc.tsv"
    left_run_qc_path.parent.mkdir(parents=True, exist_ok=True)
    right_run_qc_path.parent.mkdir(parents=True, exist_ok=True)
    _write_run_qc_tsv(
        left_run_qc_path,
        qc_status="pass",
        severity="pass",
        message="identification rate stayed within threshold",
    )
    _write_run_qc_tsv(
        right_run_qc_path,
        qc_status="fail",
        severity="failed",
        message="identification rate fell below threshold",
    )
    left_run_dir = tmp_path / "artifacts" / "left-completed-run"
    right_run_dir = tmp_path / "artifacts" / "right-completed-run"
    _write_result_manifest_json(
        archive_dir=left_run_dir,
        biological_report_dir=left_biological_report_dir,
        ptm_report_dir=left_ptm_report_dir,
        run_qc_paths=(left_run_qc_path,),
    )
    _write_result_manifest_json(
        archive_dir=right_run_dir,
        biological_report_dir=right_biological_report_dir,
        ptm_report_dir=right_ptm_report_dir,
        run_qc_paths=(right_run_qc_path,),
    )

    report = diff_completed_runs(left_run_dir, right_run_dir)

    assert report.summary.changed_protein_count > 0
    assert report.summary.changed_ptm_site_count > 0
    assert report.summary.changed_pathway_count > 0
    assert report.summary.changed_qc_decision_count > 0
    assert report.summary.changed_confidence_tier_count > 0
    assert report.summary.total_change_count >= 5

    protein_entry = next(
        entry
        for entry in report.changed_proteins
        if entry.left_protein is not None and entry.right_protein is not None
    )
    assert {reason.code for reason in protein_entry.reasons} & {
        InteractiveResultComparisonReasonCode.LOG2_FOLD_CHANGE_CHANGED,
        InteractiveResultComparisonReasonCode.EVIDENCE_TIER_CHANGED,
    }

    ptm_entry = next(
        entry
        for entry in report.changed_ptm_sites
        if entry.left_site is not None and entry.right_site is not None
    )
    assert {reason.code for reason in ptm_entry.reasons} & {
        InteractiveResultComparisonReasonCode.LOCALIZATION_TIER_CHANGED,
        InteractiveResultComparisonReasonCode.PROTEIN_CORRECTION_STATUS_CHANGED,
    }

    pathway_entry = next(
        entry
        for entry in report.changed_pathways
        if entry.left_pathway is not None and entry.right_pathway is not None
    )
    assert {reason.code for reason in pathway_entry.reasons} & {
        InteractiveResultComparisonReasonCode.ACTIVITY_SCORE_CHANGED,
        InteractiveResultComparisonReasonCode.PATHWAY_CONFIDENCE_CHANGED,
    }

    qc_entry = next(
        entry
        for entry in report.changed_qc_decisions
        if entry.left_qc_entry is not None and entry.right_qc_entry is not None
    )
    assert qc_entry.left_qc_entry.status == "pass"
    assert qc_entry.right_qc_entry.status == "fail"

    confidence_entry = report.changed_confidence_tiers[0]
    assert confidence_entry.left_confidence_tier == "high"
    assert confidence_entry.right_confidence_tier == "weak"


def test_diff_completed_runs_ignores_timestamp_only_runtime_differences(
    tmp_path: Path,
) -> None:
    biological_report_dir = _write_biological_report_dir(
        tmp_path,
        output_name="shared-biological-report",
    )
    ptm_report_dir = _write_ptm_report_dir(
        tmp_path,
        output_name="shared-ptm-report",
    )
    run_qc_path = tmp_path / "shared-run-qc.tsv"
    _write_run_qc_tsv(
        run_qc_path,
        qc_status="pass",
        severity="pass",
        message="identification rate stayed within threshold",
    )
    left_run_dir = tmp_path / "artifacts" / "timestamp-left"
    right_run_dir = tmp_path / "artifacts" / "timestamp-right"
    _write_result_manifest_json(
        archive_dir=left_run_dir,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_paths=(run_qc_path,),
    )
    _write_result_manifest_json(
        archive_dir=right_run_dir,
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_paths=(run_qc_path,),
    )
    (left_run_dir / "timestamps").mkdir(parents=True, exist_ok=True)
    (right_run_dir / "timestamps").mkdir(parents=True, exist_ok=True)
    (left_run_dir / "timestamps" / "completed_at.txt").write_text(
        "2026-05-25T10:00:00Z\n",
        encoding="utf-8",
    )
    (right_run_dir / "timestamps" / "completed_at.txt").write_text(
        "2026-05-25T13:45:00Z\n",
        encoding="utf-8",
    )

    report = diff_completed_runs(left_run_dir, right_run_dir)

    assert report.summary.changed_protein_count == 0
    assert report.summary.changed_ptm_site_count == 0
    assert report.summary.changed_pathway_count == 0
    assert report.summary.changed_qc_decision_count == 0
    assert report.summary.changed_confidence_tier_count == 0
    assert report.summary.total_change_count == 0
