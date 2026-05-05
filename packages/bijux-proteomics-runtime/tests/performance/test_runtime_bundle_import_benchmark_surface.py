# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.runs.replay import load_local_run_bundle
from bijux_proteomics_runtime.workflows.plans import (
    build_workflow_runtime_export_bundle,
    import_workflow_runtime_archive_bundle,
)

from .runtime_benchmark_fixtures import (
    build_medium_local_bundle_workspace,
    build_medium_workflow_archive_payload,
    build_medium_workflow_runtime_bundle_fixture,
)


def test_runtime_bundle_load_benchmark_reads_medium_local_bundle(
    benchmark,
    tmp_path,
) -> None:
    workspace = build_medium_local_bundle_workspace(tmp_path)

    bundle = benchmark(lambda: load_local_run_bundle(workspace))

    assert bundle.run_context.run_id == workspace.run_id
    assert len(bundle.run_summary["report"]["protein_groups"]) == 72


def test_runtime_bundle_export_benchmark_serializes_medium_workflow_bundle(
    benchmark,
) -> None:
    runtime_bundle = build_medium_workflow_runtime_bundle_fixture()

    export_bundle = benchmark(lambda: build_workflow_runtime_export_bundle(runtime_bundle))

    assert export_bundle.workflow_id == runtime_bundle.manifest.workflow_id
    assert export_bundle.export_bundle_sha256


def test_runtime_import_normalization_benchmark_restores_medium_archive_payload(
    benchmark,
) -> None:
    payload = build_medium_workflow_archive_payload()

    export_bundle, report = benchmark(
        lambda: import_workflow_runtime_archive_bundle(payload)
    )

    assert export_bundle.workflow_id == report.workflow_id
    assert report.preserved_artifact_count > 0
