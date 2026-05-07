from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows import (
    build_benchmark_failure_recovery_bundle,
    build_benchmark_replay_audit,
    run_benchmark_dda_import_path,
)


def test_benchmark_replay_audit_proves_reuse_and_invalidation_boundaries(
    tmp_path: Path,
) -> None:
    manifest = run_benchmark_dda_import_path(tmp_path)
    audit = build_benchmark_replay_audit(
        tmp_path,
        package_id="dda-maxquant-pipeline-corpus",
        manifest=manifest,
    )

    assert audit.exact_reuse.eligible is True
    assert audit.tool_change.invalidation_reasons == ("tools_changed",)
    assert audit.input_change.invalidation_reasons == ("input_changed",)
    assert "imported_evidence" in audit.exact_reuse.reused_nodes
    assert "review" in audit.tool_change.rerun_nodes


def test_benchmark_failure_recovery_bundle_separates_engineering_and_scientific_drift(
    tmp_path: Path,
) -> None:
    manifest = run_benchmark_dda_import_path(tmp_path)
    workspace = RunWorkspace.for_run(tmp_path, manifest.run_id)
    review_packet_path = workspace.artifact_items_dir / "review_packet.json"
    review_packet_path.write_text('{"corrupted": true}', encoding="utf-8")

    bundle = build_benchmark_failure_recovery_bundle(
        tmp_path,
        package_id="dda-maxquant-pipeline-corpus",
        manifest=manifest,
    )

    assert "runtime-review-packet" in bundle.blocked_artifact_kinds
    assert "runtime-import-trace" in bundle.preserved_artifact_kinds
    assert bundle.scientific_invalidation_reasons == ("input_changed",)
