# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Materialize checked challenge-corpus assets for flagship holdouts and perturbations."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from bijux_proteomics.benchmarks.flagship.challenge_corpora import (
    BlindedHoldoutReport,
    ChallengeKind,
    PerturbationReactionReport,
    build_blinded_holdout_reports,
    build_flagship_challenge_registry,
    build_perturbation_reports,
    flagship_challenge_registry_path,
)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _write_text(repo_relative_path: str, content: str) -> None:
    path = _repo_root() / repo_relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(repo_relative_path: str, payload: object) -> None:
    _write_text(
        repo_relative_path, json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


def _read_tsv_rows(repo_relative_path: str) -> list[dict[str, str]]:
    with (_repo_root() / repo_relative_path).open(
        newline="", encoding="utf-8"
    ) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _write_tsv(repo_relative_path: str, rows: list[dict[str, str]]) -> None:
    path = _repo_root() / repo_relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _holdout_readme(report: BlindedHoldoutReport) -> str:
    return (
        "\n".join(
            (
                f"# {report.workflow_family.upper()} Blinded Holdout",
                "",
                "This challenge root freezes the main package and review surfaces first, then reveals",
                "whether the withheld family-transfer findings still support the same workflow claims.",
                "",
                f"- challenge id: `{report.challenge_id}`",
                f"- primary package id: `{report.primary_package_id}`",
                f"- holdout package id: `{report.holdout_package_id}`",
                f"- revealed report: `{report.artifact_path}`",
            )
        )
        + "\n"
    )


def _perturbation_readme(report: PerturbationReactionReport) -> str:
    return (
        "\n".join(
            (
                f"# {report.workflow_family.upper()} Perturbation Corpus",
                "",
                "This challenge root keeps the perturbed evidence files and the measured",
                "workflow, comparator, and review reactions together.",
                "",
                f"- challenge id: `{report.challenge_id}`",
                f"- revealed report: `{report.artifact_path}`",
            )
        )
        + "\n"
    )


def _refresh_dda_dia_lfq_perturbation_assets() -> tuple[str, ...]:
    written: list[str] = []

    dda_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dda_reviewable_run/primary/maxquant_pipeline_export.tsv"
    )
    dda_rows[0]["pep_value"] = "0.0120"
    dda_rows[1]["pep_value"] = "0.0180"
    dda_rows[2]["pep_value"] = "0.0090"
    dda_rows.append(
        {
            "scan_number": "mq-pipe-corpus-1004",
            "sequence_with_mods": "CONTPEP",
            "precursor_charge": "2",
            "score_value": "77.0",
            "leading_proteins": "CON__P00001",
            "reverse_flag": "",
            "pep_value": "0.0080",
        }
    )
    dda_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "dda_calibration_decoy_perturbation/evidence/perturbed_maxquant_pipeline_export.tsv"
    )
    _write_tsv(dda_path, dda_rows)
    written.append(dda_path)

    dia_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dia_matrix_shift_review_package/primary/diann_report.tsv"
    )
    dia_rows[0]["Q.Value"] = "0.045"
    dia_rows[0]["Protein.Ids"] = "P12345;Q33333"
    dia_rows[1]["Q.Value"] = "0.020"
    dia_primary_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "dia_library_dropout_perturbation/evidence/perturbed_diann_report.tsv"
    )
    _write_tsv(dia_primary_path, dia_rows)
    written.append(dia_primary_path)

    spectronaut_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "dia_matrix_shift_review_package/comparator/spectronaut_pipeline_export.tsv"
    )
    spectronaut_rows[0]["stripped_sequence"] = "SHIFTEDPEP"
    spectronaut_rows[0]["protein_accessions"] = "P77777"
    dia_comparator_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "dia_library_dropout_perturbation/evidence/perturbed_spectronaut_pipeline_export.tsv"
    )
    _write_tsv(dia_comparator_path, spectronaut_rows)
    written.append(dia_comparator_path)

    lfq_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv"
    )
    for row in lfq_rows:
        if row["sample_id"].startswith("T") and row["peptide"] == "CPEPTIDE":
            row["intensity"] = ""
            row["missing_reason"] = "batch_drift"
        elif row["sample_id"].startswith("T") and row["peptide"] == "APEPTIDE":
            row["intensity"] = str(round(float(row["intensity"]) * 0.45, 2))
        elif row["sample_id"] in {"C3", "C4"} and row["peptide"] == "BPEPTIDE":
            row["intensity"] = ""
            row["missing_reason"] = "low_signal"
    lfq_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "lfq_missingness_drift_perturbation/evidence/perturbed_study_scale_ms1_features.tsv"
    )
    _write_tsv(lfq_path, lfq_rows)
    written.append(lfq_path)

    return tuple(written)


def _refresh_multiplex_and_ptm_perturbation_assets() -> tuple[str, ...]:
    written: list[str] = []

    multiplex_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv"
    )
    for row in multiplex_rows:
        if row["sample_id"] in {"plex_a_128N", "plex_b_128N"}:
            row["intensity"] = ""
            row["missing_reason"] = "reference_dropout"
        elif row["sample_id"] in {"plex_a_126", "plex_b_126"}:
            row["intensity"] = str(round(float(row["intensity"]) * 0.35, 2))
        elif row["sample_id"] in {"plex_a_127N", "plex_b_127N"}:
            row["intensity"] = str(round(float(row["intensity"]) * 1.65, 2))
    multiplex_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "multiplex_reference_bleed_perturbation/evidence/perturbed_multiplex_ms1_features.tsv"
    )
    _write_tsv(multiplex_path, multiplex_rows)
    written.append(multiplex_path)

    localization_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "ptm_localization_review_package/evidence/localization_results.tsv"
    )
    for row in localization_rows:
        if row["spectrum_id"] in {"scan=ptm-003", "scan=ptm-004"}:
            row["q_value"] = "0.024"
            row["localization_score"] = "0.680"
            row["candidate_sites"] = "1;5"
        elif row["spectrum_id"] == "scan=ptm-007":
            row["q_value"] = "0.028"
            row["localization_score"] = "0.610"
            row["candidate_sites"] = "8;9"
    localization_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "ptm_ambiguity_occupancy_perturbation/evidence/perturbed_localization_results.tsv"
    )
    _write_tsv(localization_path, localization_rows)
    written.append(localization_path)

    feature_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "ptm_localization_review_package/evidence/ptm_features.tsv"
    )
    for row in feature_rows:
        if row["feature_id"] in {"ptm-f005", "ptm-f007", "ptm-f011"}:
            row["intensity"] = ""
            row["missing_reason"] = "interference_filtered"
        elif row["feature_id"] == "ptm-f006":
            row["intensity"] = "540"
        elif row["feature_id"] == "ptm-f008":
            row["intensity"] = "610"
    feature_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "ptm_ambiguity_occupancy_perturbation/evidence/perturbed_ptm_features.tsv"
    )
    _write_tsv(feature_path, feature_rows)
    written.append(feature_path)

    return tuple(written)


def _refresh_targeted_perturbation_assets() -> tuple[str, ...]:
    written: list[str] = []

    qc_rows = _read_tsv_rows(
        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        "targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv"
    )
    for row in qc_rows:
        row["tic"] = str(round(float(row["tic"]) * 0.38, 2))
        row["bpc"] = str(round(float(row["bpc"]) * 0.44, 2))
    qc_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "targeted_interference_carryover_perturbation/evidence/perturbed_targeted_benchmark_qc.tsv"
    )
    _write_tsv(qc_path, qc_rows)
    written.append(qc_path)

    follow_up_path = (
        _repo_root()
        / "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/"
        / "targeted_transition_review_package/follow_up/supported_targeted_follow_up.json"
    )
    follow_up_payload = json.loads(follow_up_path.read_text(encoding="utf-8"))
    follow_up_payload["review_queue_decision"]["state"] = "blocked"
    follow_up_payload["review_queue_decision"]["summary"] = (
        "calibrant drift, transition interference, and carryover block direct targeted execution"
    )
    follow_up_payload["workflow_readiness_summary"]["ready_step_count"] = 2
    follow_up_payload["workflow_readiness_summary"]["blocked_step_count"] = 3
    follow_up_payload["workflow_readiness_summary"]["missing_evidence_needs"] = [
        "fresh calibrant curve",
        "transition interference cleanup",
    ]
    follow_up_payload["workflow_readiness_summary"]["blocking_assay_ids"] = [
        "assay-egfr-prm",
        "assay-egfr-orthogonal",
    ]
    follow_up_payload["handoff_validation"]["accepted"] = False
    follow_up_payload["handoff_validation"]["accepted_assay_ids"] = []
    follow_up_payload["handoff_validation"]["blockers"] = [
        "heavy-light mismatch above tolerance",
        "carryover remains visible in blank injections",
    ]
    follow_up_payload["transition_review"]["approved_transition_ids"] = []
    follow_up_payload["transition_review"]["exploratory_transition_ids"] = [
        "tr-egfr-y7",
    ]
    follow_up_payload["transition_review"]["refused_transition_ids"] = [
        "tr-egfr-y5",
        "tr-egfr-y8",
    ]
    follow_up_payload["transition_review"]["readiness_score"] = 0.1
    follow_up_payload["review_packet"]["ready_for_synthesis"] = False
    follow_up_payload["review_packet"]["blocking_findings"] = [
        "calibration drift exceeds supported handoff range",
        "transition interference remains above reviewable threshold",
        "carryover invalidates direct progression to assay execution",
    ]
    follow_up_payload["review_packet"]["recommended_actions"] = [
        "rerun calibrant standards",
        "redesign transitions with stronger selectivity",
    ]
    follow_up_payload["executable_plan"]["plan_kind"] = "blocked_review"
    follow_up_payload["executable_plan"]["blocked_by"] = [
        "transition interference audit",
        "carryover remediation",
    ]
    follow_up_payload["outcome"]["assay_outcomes"] = [
        {
            "assay_id": "assay-egfr-prm",
            "status": "blocked",
            "reason": "carryover and heavy-light mismatch remain unresolved",
        }
    ]
    perturbed_follow_up_path = (
        "packages/bijux-proteomics-core/benchmark-assets/flagship-challenge-corpora/"
        "targeted_interference_carryover_perturbation/follow_up/perturbed_supported_targeted_follow_up.json"
    )
    _write_json(perturbed_follow_up_path, follow_up_payload)
    written.append(perturbed_follow_up_path)

    return tuple(written)


def refresh_flagship_challenge_assets() -> tuple[str, ...]:
    """Write checked challenge assets to the product-owned challenge root."""

    written: list[str] = []
    for report in build_blinded_holdout_reports():
        challenge_root = report.artifact_path.rsplit("/", 1)[0]
        manifest_path = f"{challenge_root}/challenge_manifest.json"
        readme_path = f"{challenge_root}/README.md"
        _write_json(
            manifest_path,
            {
                "challenge_id": report.challenge_id,
                "challenge_kind": ChallengeKind.BLINDED_HOLDOUT.value,
                "workflow_family": report.workflow_family,
                "primary_package_id": report.primary_package_id,
                "holdout_package_id": report.holdout_package_id,
                "frozen_surface_paths": list(report.frozen_surface_paths),
                "revealed_report_path": report.artifact_path,
                "note": report.note,
            },
        )
        _write_json(report.artifact_path, report.model_dump(mode="json"))
        _write_text(readme_path, _holdout_readme(report))
        written.extend((manifest_path, report.artifact_path, readme_path))

    written.extend(_refresh_dda_dia_lfq_perturbation_assets())
    written.extend(_refresh_multiplex_and_ptm_perturbation_assets())
    written.extend(_refresh_targeted_perturbation_assets())

    for perturbation_report in build_perturbation_reports():
        challenge_root = perturbation_report.artifact_path.rsplit("/", 1)[0]
        manifest_path = f"{challenge_root}/challenge_manifest.json"
        readme_path = f"{challenge_root}/README.md"
        _write_json(
            manifest_path,
            {
                "challenge_id": perturbation_report.challenge_id,
                "challenge_kind": ChallengeKind.PERTURBATION.value,
                "workflow_family": perturbation_report.workflow_family,
                "perturbation_axes": list(perturbation_report.perturbation_axes),
                "evidence_paths": list(perturbation_report.evidence_paths),
                "revealed_report_path": perturbation_report.artifact_path,
                "note": perturbation_report.note,
            },
        )
        _write_json(
            perturbation_report.artifact_path,
            perturbation_report.model_dump(mode="json"),
        )
        _write_text(readme_path, _perturbation_readme(perturbation_report))
        written.extend((manifest_path, perturbation_report.artifact_path, readme_path))

    registry = build_flagship_challenge_registry()
    _write_json(flagship_challenge_registry_path(), registry.model_dump(mode="json"))
    written.append(flagship_challenge_registry_path())
    return tuple(written)


def main(argv: list[str] | None = None) -> int:
    """Refresh checked flagship challenge assets."""

    parser = argparse.ArgumentParser(
        description="Materialize flagship blinded holdout and perturbation assets."
    )
    parser.add_argument(
        "command",
        choices=("refresh",),
        help="refresh checked challenge-corpus assets",
    )
    args = parser.parse_args(argv)
    if args.command == "refresh":
        for path in refresh_flagship_challenge_assets():
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
