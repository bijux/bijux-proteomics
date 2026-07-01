# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark and demo facade ledgers for workflow compatibility surfaces."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)

BENCHMARK_SYNTHETIC_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.synthetic.synthetic_quant_truth",
        rationale="synthetic quantification truth ownership",
    ),
)

BENCHMARK_FIDELITY_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.fidelity.diann_benchmarks",
        rationale="DIA-NN benchmark ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.fidelity.maxquant_benchmarks",
        rationale="MaxQuant benchmark ownership",
    ),
)

BENCHMARK_DATASET_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_descriptors",
        rationale="public benchmark descriptor ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.benchmarks.datasets.public_benchmark_subset",
        rationale="public benchmark subset ownership",
    ),
)

BENCHMARK_FACADE_OWNERS = (
    *BENCHMARK_FIDELITY_FACADE_OWNERS,
    *BENCHMARK_DATASET_FACADE_OWNERS,
    *BENCHMARK_SYNTHETIC_FACADE_OWNERS,
)

BENCHMARK_SUBMODULES = {
    "datasets": "bijux_proteomics.workflow.benchmarks.datasets",
    "fidelity": "bijux_proteomics.workflow.benchmarks.fidelity",
    "synthetic": "bijux_proteomics.workflow.benchmarks.synthetic",
}

DEMO_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.scale_demo",
        rationale="generated scale demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo",
        rationale="shipped surprising demo ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.demo.surprising_demo_interrogation",
        rationale="surprising demo interrogation ownership",
    ),
)

WORKFLOW_ROOT_DEMO_HELPER_EXPORTS = (
    "render_scale_demo_stage_metrics_tsv",
    "render_scale_demo_summary_tsv",
    "render_scale_demo_validation_tsv",
    "load_surprising_demo_manifest",
    "render_surprising_demo_findings_tsv",
    "render_surprising_demo_summary_tsv",
    "render_surprising_demo_interrogation_answers_tsv",
    "render_surprising_demo_interrogation_summary_tsv",
)

WORKFLOW_ROOT_DEMO_OWNERS = copy_facade_owners(DEMO_FACADE_OWNERS)


__all__ = [
    "BENCHMARK_DATASET_FACADE_OWNERS",
    "BENCHMARK_FACADE_OWNERS",
    "BENCHMARK_FIDELITY_FACADE_OWNERS",
    "BENCHMARK_SUBMODULES",
    "BENCHMARK_SYNTHETIC_FACADE_OWNERS",
    "DEMO_FACADE_OWNERS",
    "WORKFLOW_ROOT_DEMO_HELPER_EXPORTS",
    "WORKFLOW_ROOT_DEMO_OWNERS",
    "WorkflowFacadeOwner",
]
