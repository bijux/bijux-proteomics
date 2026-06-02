from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows import (
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
    run_benchmark_dda_generalization_import_path,
    run_benchmark_dda_import_path,
    run_benchmark_dia_generalization_review_path,
    run_benchmark_dia_import_path,
    run_benchmark_dia_review_path,
    run_benchmark_lfq_generalization_review_path,
    run_benchmark_lfq_review_path,
    run_benchmark_multiplex_generalization_review_path,
    run_benchmark_multiplex_review_path,
    run_benchmark_ptm_generalization_review_path,
    run_benchmark_ptm_review_path,
    run_benchmark_sequence_path,
    run_benchmark_targeted_generalization_review_path,
    run_benchmark_targeted_review_path,
)


def test_benchmark_run_specs_keep_real_runtime_packages_visible() -> None:
    specs = {spec.package_id: spec for spec in build_benchmark_run_specs()}

    assert tuple(specs) == (
        "sequence-first-useful-corpus",
        "dda-maxquant-pipeline-corpus",
        "dda-comet-cross-engine-corpus",
        "dia-diann-pipeline-corpus",
        "dia-matrix-shift-review-corpus",
        "lfq-cohort-review-corpus",
        "lfq-sparse-contrast-review-corpus",
        "multiplex-tmtpro-review-corpus",
        "multiplex-channel-stress-review-corpus",
        "ptm-localization-review-corpus",
        "ptm-ambiguity-stress-review-corpus",
        "targeted-transition-review-corpus",
        "targeted-carryover-review-corpus",
    )
    assert specs["sequence-first-useful-corpus"].run_mode.value == "raw_executable"
    assert specs["dda-maxquant-pipeline-corpus"].engine_name == "maxquant"
    assert any(
        path.endswith(
            "benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json"
        )
        for path in specs["dda-maxquant-pipeline-corpus"].public_package_paths
    )
    assert specs["dia-diann-pipeline-corpus"].run_mode.value == "raw_executable"
    assert any(
        path.endswith(
            "benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json"
        )
        for path in specs["dia-diann-pipeline-corpus"].public_package_paths
    )
    assert specs["lfq-cohort-review-corpus"].run_mode.value == "raw_executable"
    assert specs["lfq-sparse-contrast-review-corpus"].run_mode.value == "raw_executable"
    assert specs["multiplex-tmtpro-review-corpus"].workflow_family == "multiplex_review"
    assert (
        specs["multiplex-channel-stress-review-corpus"].workflow_family
        == "multiplex_generalization_review"
    )
    assert specs["ptm-localization-review-corpus"].workflow_family == "ptm_review"
    assert (
        specs["ptm-ambiguity-stress-review-corpus"].workflow_family
        == "ptm_generalization_review"
    )
    assert specs["targeted-transition-review-corpus"].run_mode.value == "raw_executable"
    assert specs["targeted-carryover-review-corpus"].run_mode.value == "raw_executable"


def test_run_benchmark_sequence_path_executes_real_runtime_path(tmp_path: Path) -> None:
    manifest = run_benchmark_sequence_path(tmp_path)

    assert manifest.command == "run"
    assert manifest.import_only is False
    assert manifest.workflow_family == "sequence_to_digest"
    assert Path(manifest.summary_path).exists()
    assert Path(manifest.integrity_report_path).exists()


def test_run_benchmark_import_paths_ingest_real_comparator_tables(
    tmp_path: Path,
) -> None:
    dda_manifest = run_benchmark_dda_import_path(tmp_path / "dda")
    dda_companion_manifest = run_benchmark_dda_generalization_import_path(
        tmp_path / "dda-companion"
    )
    dia_manifest = run_benchmark_dia_import_path(tmp_path / "dia")

    dda_workspace = RunWorkspace.for_run(tmp_path / "dda", dda_manifest.run_id)
    dda_companion_workspace = RunWorkspace.for_run(
        tmp_path / "dda-companion", dda_companion_manifest.run_id
    )
    dia_workspace = RunWorkspace.for_run(tmp_path / "dia", dia_manifest.run_id)
    dda_payload = (
        dda_workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")
    dda_companion_payload = (
        dda_companion_workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")
    dia_payload = (
        dia_workspace.artifact_items_dir / "imported_evidence.json"
    ).read_text(encoding="utf-8")

    assert '"row_count": 3' in dda_payload
    assert '"scan_number"' in dda_payload
    assert '"row_count": 2' in dda_companion_payload
    assert '"row_count": 3' in dia_payload
    assert '"EG.PrecursorId"' in dia_payload


def test_run_benchmark_dia_review_path_executes_raw_executable_dia_lane() -> None:
    report = run_benchmark_dia_review_path()
    companion = run_benchmark_dia_generalization_review_path()

    assert report.precursor_count == 6
    assert report.peptide_count >= 3
    assert report.protein_count >= 3
    assert report.qc_missing_intensity_count == 6
    assert companion.precursor_count == 4
    assert companion.peptide_count >= 2


def test_runtime_wrappers_cover_flagship_lfq_multiplex_ptm_and_targeted() -> None:
    lfq = run_benchmark_lfq_review_path()
    lfq_companion = run_benchmark_lfq_generalization_review_path()
    multiplex = run_benchmark_multiplex_review_path()
    multiplex_companion = run_benchmark_multiplex_generalization_review_path()
    ptm = run_benchmark_ptm_review_path()
    ptm_companion = run_benchmark_ptm_generalization_review_path()
    targeted = run_benchmark_targeted_review_path()
    targeted_companion = run_benchmark_targeted_generalization_review_path()

    assert lfq.condition_count == 2
    assert lfq_companion.condition_count == 2
    assert multiplex.channel_count >= 1
    assert multiplex.missing_channel_count == 2
    assert multiplex_companion.channel_count >= 1
    assert ptm.mapped_site_count >= 1
    assert ptm_companion.mapped_site_count >= 1
    assert targeted.qc_point_count >= 1
    assert targeted_companion.qc_point_count >= 1


def test_benchmark_runtime_truth_surface_tracks_all_flagship_run_families() -> None:
    rows = {row.workflow_family: row for row in build_benchmark_runtime_truth_surface()}

    assert rows["sequence_to_digest"].run_mode.value == "raw_executable"
    assert rows["sequence_to_digest"].proof_class.value == "raw_execution"
    assert rows["dda_import"].externally_cross_checked is True
    assert rows["dda_import"].proof_class.value == "import_backed_execution"
    assert rows["dia_import"].artifact_browser_ready is True
    assert rows["dia_import"].run_mode.value == "raw_executable"
    assert rows["quant_review"].run_mode.value == "raw_executable"
    assert rows["multiplex_review"].run_mode.value == "raw_executable"
    assert rows["ptm_review"].run_mode.value == "raw_executable"
    assert rows["targeted_review"].run_mode.value == "raw_executable"
