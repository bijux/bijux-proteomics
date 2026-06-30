# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public workflow facade catalogs and compatibility targets."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_benchmark_catalog import (
    BENCHMARK_DATASET_FACADE_OWNERS,
    BENCHMARK_FACADE_OWNERS,
    BENCHMARK_FIDELITY_FACADE_OWNERS,
    BENCHMARK_SUBMODULES,
    BENCHMARK_SYNTHETIC_FACADE_OWNERS,
    DEMO_FACADE_OWNERS,
    WORKFLOW_ROOT_DEMO_HELPER_EXPORTS,
    WORKFLOW_ROOT_DEMO_OWNERS,
)
from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)
from bijux_proteomics.workflow.facade_export_catalog import (
    EXPORT_FACADE_OWNERS,
    WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS,
    WORKFLOW_ROOT_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_EXPORT_OWNERS,
)
from bijux_proteomics.workflow.facade_pipeline_catalog import (
    ADVANCED_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_OWNER_MODULES,
    COMPARATIVE_PIPELINE_FACADE_OWNERS,
    COMPARATIVE_PIPELINE_OWNER_MODULES,
    ENGINE_PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_OWNER_MODULES,
    PIPELINE_FACADE_OWNERS,
    PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES,
    PIPELINE_ROOT_OWNERS,
    PIPELINE_SUBMODULES,
    SYNTHESIS_PIPELINE_FACADE_OWNERS,
    SYNTHESIS_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS,
    WORKFLOW_ROOT_PIPELINE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS,
)
from bijux_proteomics.workflow.facade_runtime import (
    build_lazy_export_index,
    list_owned_public_names,
    load_public_export,
    load_public_submodule,
    module_directory,
    ordered_facade_owners,
)
from bijux_proteomics.workflow.facade_report_catalog import (
    REPORT_FACADE_OWNERS,
    WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_REPORT_HELPER_EXPORTS,
    WORKFLOW_ROOT_REPORT_OWNERS,
)
from bijux_proteomics.workflow.facade_study_catalog import (
    STUDY_FACADE_OWNERS,
    WORKFLOW_ROOT_STUDY_OWNERS,
    WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS,
)
from bijux_proteomics.workflow.facade_targets import (
    WORKFLOW_BENCHMARK_ROOT_OWNER_FILES,
    WORKFLOW_BENCHMARK_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS,
    WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS,
    WORKFLOW_ROOT_OWNER_FILES,
    WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS,
    WORKFLOW_ROOT_WRAPPER_TARGETS,
)


CARD_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.cross_study_evidence_cards",
        rationale="cross-study evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.mechanisms",
        rationale="mechanism card workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.pathway_evidence_cards",
        rationale="pathway evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_evidence_cards",
        rationale="protein evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_mechanism_cards",
        rationale="protein mechanism card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.sample_evidence_cards",
        rationale="sample evidence card ownership",
    ),
)

WORKFLOW_ROOT_CARD_HELPER_EXPORTS = (
    "render_cross_study_evidence_card_summary_tsv",
    "render_cross_study_evidence_card_tsv",
    "render_cross_study_evidence_dataset_tsv",
    "render_mechanism_card_summary_tsv",
    "render_mechanism_cards_tsv",
    "export_pathway_evidence_card_tsv",
    "render_pathway_evidence_card_tsv",
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
    "export_protein_mechanism_card_summary_tsv",
    "export_protein_mechanism_card_tsv",
    "render_protein_mechanism_card_summary_tsv",
    "render_protein_mechanism_card_tsv",
    "export_sample_evidence_card_tsv",
    "render_sample_evidence_card_tsv",
)

WORKFLOW_ROOT_CARD_OWNERS = copy_facade_owners(CARD_FACADE_OWNERS)

WORKFLOW_ROOT_SUBMODULES = {
    "benchmarks": "bijux_proteomics.workflow.benchmarks",
    "cards": "bijux_proteomics.workflow.cards",
    "cross_study_protein_harmonization": "bijux_proteomics.workflow.cross_study_protein_harmonization",
    "demo": "bijux_proteomics.workflow.demo",
    "exports": "bijux_proteomics.workflow.exports",
    "pipelines": "bijux_proteomics.workflow.pipelines",
    "public_benchmark_descriptors": "bijux_proteomics.workflow.public_benchmark_descriptors",
    "reports": "bijux_proteomics.workflow.reports",
    "studies": "bijux_proteomics.workflow.studies",
}

WORKFLOW_ROOT_SHARED_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.result_types",
        rationale="shared workflow result record ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.blueprint",
        rationale="workflow blueprint ownership",
    ),
)

WORKFLOW_ROOT_OWNERS = (
    *WORKFLOW_ROOT_SHARED_OWNERS,
    *WORKFLOW_ROOT_REPORT_OWNERS,
    *WORKFLOW_ROOT_EXPORT_OWNERS,
    *WORKFLOW_ROOT_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_STUDY_OWNERS,
    *WORKFLOW_ROOT_CARD_OWNERS,
    *BENCHMARK_FACADE_OWNERS,
    *WORKFLOW_ROOT_DEMO_OWNERS,
)

__all__ = [
    "ADVANCED_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_FACADE_OWNERS",
    "BENCHMARKING_PIPELINE_OWNER_MODULES",
    "BENCHMARK_FIDELITY_FACADE_OWNERS",
    "BENCHMARK_DATASET_FACADE_OWNERS",
    "BENCHMARK_FACADE_OWNERS",
    "BENCHMARK_SYNTHETIC_FACADE_OWNERS",
    "BENCHMARK_SUBMODULES",
    "CARD_FACADE_OWNERS",
    "COMPARATIVE_PIPELINE_FACADE_OWNERS",
    "COMPARATIVE_PIPELINE_OWNER_MODULES",
    "DEMO_FACADE_OWNERS",
    "EXPORT_FACADE_OWNERS",
    "ENGINE_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_FACADE_OWNERS",
    "OPERATIONS_PIPELINE_OWNER_MODULES",
    "PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES",
    "PIPELINE_ROOT_OWNERS",
    "PIPELINE_SUBMODULES",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS",
    "WORKFLOW_BENCHMARK_ROOT_OWNER_FILES",
    "WORKFLOW_BENCHMARK_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_CARD_HELPER_EXPORTS",
    "WORKFLOW_ROOT_CARD_OWNERS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_DEMO_HELPER_EXPORTS",
    "WORKFLOW_ROOT_DEMO_OWNERS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_RENDER_EXPORTS",
    "WORKFLOW_ROOT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_ADVANCED_PIPELINE_VALIDATION_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_EXPORT_OWNERS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS",
    "WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_OWNER_FILES",
    "WORKFLOW_PIPELINE_ADVANCED_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_DEMO_WRAPPER_TARGETS",
    "WORKFLOW_PIPELINE_ENGINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_REPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_REPORT_OWNERS",
    "WORKFLOW_ROOT_SHARED_OWNERS",
    "PIPELINE_FACADE_OWNERS",
    "REPORT_FACADE_OWNERS",
    "STUDY_FACADE_OWNERS",
    "SYNTHESIS_PIPELINE_FACADE_OWNERS",
    "SYNTHESIS_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_OWNERS",
    "WORKFLOW_ROOT_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNER_MODULES",
    "WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS",
    "WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS",
    "WORKFLOW_ROOT_STUDY_OWNERS",
    "WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS",
    "WORKFLOW_ROOT_SUBMODULES",
    "WORKFLOW_ROOT_PIPELINE_WRAPPER_TARGETS",
    "WORKFLOW_ROOT_WRAPPER_TARGETS",
    "WorkflowFacadeOwner",
    "build_lazy_export_index",
    "list_owned_public_names",
    "load_public_export",
    "load_public_submodule",
    "module_directory",
    "ordered_facade_owners",
]
