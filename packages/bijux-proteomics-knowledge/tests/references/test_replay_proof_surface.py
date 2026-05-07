# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
)
from bijux_proteomics_knowledge.references.workflows.replay_proof import (
    build_workflow_replay_proof_ledger,
    build_workflow_replay_proof_report,
)


def test_replay_proof_report_keeps_governed_artifacts_and_tests_visible() -> None:
    manifest = DEFAULT_BENCHMARK_MANIFESTS[0]
    report = build_workflow_replay_proof_report(manifest)

    assert report.replay_supported is True
    assert report.benchmark_package_id == manifest.benchmark_package.package_id
    assert report.validating_tests
    assert report.artifact_proofs
    assert report.replay_steps
    assert any(artifact.required_for_replay for artifact in report.artifact_proofs)
    assert report.bounded_by_external_execution is True


def test_replay_proof_ledger_covers_every_curated_workflow_family() -> None:
    ledger = build_workflow_replay_proof_ledger()

    assert len(ledger.reports) == len(DEFAULT_BENCHMARK_MANIFESTS)
    assert {report.workflow_family for report in ledger.reports} == {
        manifest.workflow_family for manifest in DEFAULT_BENCHMARK_MANIFESTS
    }
