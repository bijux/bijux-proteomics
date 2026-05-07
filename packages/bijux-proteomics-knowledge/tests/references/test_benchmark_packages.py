# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_promoted_benchmark_packages_keep_realism_pressure_and_replay_steps_explicit() -> (
    None
):
    promoted_ids = {
        "benchmark:dda_search_reproducibility",
        "benchmark:dia_library_extraction_consistency",
        "benchmark:lfq_quantification_repeatability",
        "benchmark:multiplex_tmtpro_quantification",
        "benchmark:targeted_transition_quality_control",
    }

    for manifest in DEFAULT_BENCHMARK_MANIFESTS:
        if manifest.benchmark_id not in promoted_ids:
            continue
        package = manifest.benchmark_package
        assert package is not None
        assert len(package.realism_pressures) >= 2
        assert len(package.transparent_assumptions) >= 2
        assert len(package.reproduction_steps) >= 3
        assert package.governed_output_surfaces
        assert any(step.outside_repo_execution for step in package.reproduction_steps) or (
            manifest.workflow_family
            in {
                KnowledgeWorkflowFamily.LFQ,
                KnowledgeWorkflowFamily.MULTIPLEX,
                KnowledgeWorkflowFamily.TARGETED,
            }
        )
        for artifact in package.package_artifacts:
            assert (REPO_ROOT / artifact.repo_relative_path).exists()
