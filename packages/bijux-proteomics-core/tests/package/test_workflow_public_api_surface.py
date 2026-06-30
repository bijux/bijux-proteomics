# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import workflow
from bijux_proteomics.workflow import (
    benchmarks,
    cards,
    demo,
    exports,
    pipelines,
    reports,
    studies,
)
from bijux_proteomics.workflow import cross_study_protein_harmonization
from bijux_proteomics.workflow import public_benchmark_descriptors
from bijux_proteomics.workflow.public_api import (
    ADVANCED_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_FACADE_OWNERS,
    BENCHMARKING_PIPELINE_OWNER_MODULES,
    BENCHMARK_DATASET_FACADE_OWNERS,
    BENCHMARK_FACADE_OWNERS,
    BENCHMARK_FIDELITY_FACADE_OWNERS,
    BENCHMARK_SYNTHETIC_FACADE_OWNERS,
    BENCHMARK_SUBMODULES,
    CARD_FACADE_OWNERS,
    COMPARATIVE_PIPELINE_FACADE_OWNERS,
    COMPARATIVE_PIPELINE_OWNER_MODULES,
    DEMO_FACADE_OWNERS,
    ENGINE_PIPELINE_FACADE_OWNERS,
    EXPORT_FACADE_OWNERS,
    OPERATIONS_PIPELINE_FACADE_OWNERS,
    OPERATIONS_PIPELINE_OWNER_MODULES,
    PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES,
    PIPELINE_ROOT_OWNERS,
    PIPELINE_FACADE_OWNERS,
    PIPELINE_SUBMODULES,
    REPORT_FACADE_OWNERS,
    STUDY_FACADE_OWNERS,
    SYNTHESIS_PIPELINE_FACADE_OWNERS,
    SYNTHESIS_PIPELINE_OWNER_MODULES,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS,
    WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_CARD_HELPER_EXPORTS,
    WORKFLOW_ROOT_CARD_OWNERS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_DEMO_HELPER_EXPORTS,
    WORKFLOW_ROOT_DEMO_OWNERS,
    WORKFLOW_ROOT_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS,
    WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS,
    WORKFLOW_ROOT_EXPORT_OWNERS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS,
    WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS,
    WORKFLOW_ROOT_OWNERS,
    WORKFLOW_ROOT_PIPELINE_OWNERS,
    WORKFLOW_ROOT_REPORT_HELPER_EXPORTS,
    WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS,
    WORKFLOW_ROOT_REPORT_OWNERS,
    WORKFLOW_ROOT_SHARED_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS,
    WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS,
    WORKFLOW_ROOT_STUDY_OWNERS,
    WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS,
    WORKFLOW_ROOT_SUBMODULES,
    build_lazy_export_index,
    ordered_facade_owners,
)
from bijux_proteomics.workflow.result_types import WorkflowResult


def test_workflow_root_public_api_matches_governed_owner_ledger() -> None:
    expected_names, _ = build_lazy_export_index(
        ordered_facade_owners(WORKFLOW_ROOT_OWNERS)
    )

    assert tuple(workflow.__all__) == expected_names
    assert set(WORKFLOW_ROOT_SUBMODULES).isdisjoint(workflow.__all__)
    assert all(hasattr(workflow, name) for name in WORKFLOW_ROOT_SUBMODULES)


def test_workflow_root_owner_ledger_is_composed_from_shared_and_subpackage_ledgers() -> (
    None
):
    assert WORKFLOW_ROOT_OWNERS == (
        *WORKFLOW_ROOT_SHARED_OWNERS,
        *WORKFLOW_ROOT_REPORT_OWNERS,
        *WORKFLOW_ROOT_EXPORT_OWNERS,
        *WORKFLOW_ROOT_PIPELINE_OWNERS,
        *WORKFLOW_ROOT_STUDY_OWNERS,
        *WORKFLOW_ROOT_CARD_OWNERS,
        *BENCHMARK_FACADE_OWNERS,
        *WORKFLOW_ROOT_DEMO_OWNERS,
    )


def test_workflow_root_pipeline_owners_exclude_demo_surfaces() -> None:
    assert all(
        not owner.owner_module.startswith("bijux_proteomics.workflow.demo.")
        for owner in WORKFLOW_ROOT_PIPELINE_OWNERS
    )


def test_workflow_root_pipeline_owners_exclude_advanced_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(
        hasattr(pipelines.advanced, name)
        for name in WORKFLOW_ROOT_ADVANCED_PIPELINE_HELPER_EXPORTS
    )
    assert WORKFLOW_ROOT_PIPELINE_OWNERS[
        : len(WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS)
    ] == (WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS)


def test_workflow_root_pipeline_owners_exclude_engine_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(
        hasattr(pipelines.engines, name)
        for name in WORKFLOW_ROOT_ENGINE_PIPELINE_HELPER_EXPORTS
    )
    engine_owner_offset = len(WORKFLOW_ROOT_ADVANCED_PIPELINE_OWNERS)
    assert WORKFLOW_ROOT_PIPELINE_OWNERS[
        engine_owner_offset : engine_owner_offset
        + len(WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS)
    ] == (WORKFLOW_ROOT_ENGINE_PIPELINE_OWNERS)


def test_workflow_root_pipeline_owners_expose_engine_export_operations() -> None:
    assert all(
        hasattr(workflow, name)
        for name in WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS
    )
    assert all(
        hasattr(pipelines.engines, name)
        for name in WORKFLOW_ROOT_ENGINE_PIPELINE_EXPORT_OPERATIONS
    )


def test_workflow_root_pipeline_owners_expose_study_pipeline_reports() -> None:
    assert all(
        hasattr(workflow, name)
        for name in WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS
    )
    assert all(
        hasattr(pipelines.synthesis, name)
        for name in WORKFLOW_ROOT_STUDY_PIPELINE_REPORT_EXPORTS
    )
    assert WORKFLOW_ROOT_PIPELINE_OWNERS[
        -len(WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS) :
    ] == (WORKFLOW_ROOT_STUDY_PIPELINE_OWNERS)


def test_workflow_root_pipeline_owners_exclude_benchmark_pipeline_reports() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(
        hasattr(pipelines.benchmarking, name)
        for name in WORKFLOW_ROOT_BENCHMARK_PIPELINE_REPORT_EXPORTS
    )
    assert all(
        owner in WORKFLOW_ROOT_PIPELINE_OWNERS
        for owner in WORKFLOW_ROOT_BENCHMARK_PIPELINE_OWNERS
    )


def test_workflow_root_pipeline_owners_expose_comparative_pipeline_reports() -> None:
    assert all(
        hasattr(workflow, name)
        for name in WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS
    )
    assert all(
        hasattr(pipelines.comparative, name)
        for name in WORKFLOW_ROOT_COMPARATIVE_PIPELINE_REPORT_EXPORTS
    )
    assert all(
        owner in WORKFLOW_ROOT_PIPELINE_OWNERS
        for owner in WORKFLOW_ROOT_COMPARATIVE_PIPELINE_OWNERS
    )


def test_workflow_root_pipeline_owners_exclude_flagship_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(
        hasattr(pipelines.operations, name)
        for name in WORKFLOW_ROOT_FLAGSHIP_PIPELINE_HELPER_EXPORTS
    )
    assert all(
        owner in WORKFLOW_ROOT_PIPELINE_OWNERS
        for owner in WORKFLOW_ROOT_FLAGSHIP_PIPELINE_OWNERS
    )


def test_workflow_root_study_owners_expose_study_serialization_exports() -> None:
    assert all(
        hasattr(workflow, name) for name in WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS
    )
    assert all(
        hasattr(studies, name) for name in WORKFLOW_ROOT_STUDY_SERIALIZATION_EXPORTS
    )


def test_workflow_root_export_owners_exclude_export_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(hasattr(exports, name) for name in WORKFLOW_ROOT_EXPORT_HELPER_EXPORTS)


def test_workflow_root_export_owners_expose_export_operations() -> None:
    assert all(hasattr(workflow, name) for name in WORKFLOW_ROOT_EXPORT_OPERATIONS)
    assert all(hasattr(exports, name) for name in WORKFLOW_ROOT_EXPORT_OPERATIONS)


def test_workflow_root_card_owners_exclude_card_serialization_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_CARD_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(hasattr(cards, name) for name in WORKFLOW_ROOT_CARD_HELPER_EXPORTS)


def test_workflow_root_report_owners_exclude_report_serialization_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_REPORT_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(hasattr(reports, name) for name in WORKFLOW_ROOT_REPORT_HELPER_EXPORTS)


def test_workflow_root_report_owners_expose_report_export_operations() -> None:
    assert all(
        hasattr(workflow, name) for name in WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS
    )
    assert all(
        hasattr(reports, name) for name in WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS
    )


def test_workflow_root_demo_owners_exclude_demo_helpers() -> None:
    assert (
        tuple(
            name
            for name in WORKFLOW_ROOT_DEMO_HELPER_EXPORTS
            if hasattr(workflow, name)
        )
        == ()
    )
    assert all(hasattr(demo, name) for name in WORKFLOW_ROOT_DEMO_HELPER_EXPORTS)


def test_workflow_owner_subfacades_match_governed_owner_ledgers() -> None:
    expected_benchmark_synthetic, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARK_SYNTHETIC_FACADE_OWNERS)
    )
    expected_benchmark_fidelity, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARK_FIDELITY_FACADE_OWNERS)
    )
    expected_benchmark_datasets, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARK_DATASET_FACADE_OWNERS)
    )
    expected_benchmarks, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARK_FACADE_OWNERS)
    )
    expected_cards, _ = build_lazy_export_index(
        ordered_facade_owners(CARD_FACADE_OWNERS)
    )
    expected_demo, _ = build_lazy_export_index(
        ordered_facade_owners(DEMO_FACADE_OWNERS)
    )
    expected_exports, _ = build_lazy_export_index(
        ordered_facade_owners(EXPORT_FACADE_OWNERS)
    )
    expected_pipelines, _ = build_lazy_export_index(
        ordered_facade_owners(PIPELINE_ROOT_OWNERS)
    )
    expected_pipeline_advanced, _ = build_lazy_export_index(
        ordered_facade_owners(ADVANCED_PIPELINE_FACADE_OWNERS)
    )
    expected_pipeline_benchmarking, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARKING_PIPELINE_FACADE_OWNERS)
    )
    expected_pipeline_comparative, _ = build_lazy_export_index(
        ordered_facade_owners(COMPARATIVE_PIPELINE_FACADE_OWNERS)
    )
    expected_pipeline_engines, _ = build_lazy_export_index(
        ordered_facade_owners(ENGINE_PIPELINE_FACADE_OWNERS)
    )
    expected_pipeline_operations, _ = build_lazy_export_index(
        ordered_facade_owners(OPERATIONS_PIPELINE_FACADE_OWNERS)
    )
    expected_pipeline_synthesis, _ = build_lazy_export_index(
        ordered_facade_owners(SYNTHESIS_PIPELINE_FACADE_OWNERS)
    )
    expected_reports, _ = build_lazy_export_index(
        ordered_facade_owners(REPORT_FACADE_OWNERS)
    )
    expected_studies, _ = build_lazy_export_index(
        ordered_facade_owners(STUDY_FACADE_OWNERS)
    )

    assert tuple(benchmarks.__all__) == expected_benchmarks
    assert set(BENCHMARK_SUBMODULES).isdisjoint(benchmarks.__all__)
    assert all(hasattr(benchmarks, name) for name in BENCHMARK_SUBMODULES)
    assert tuple(benchmarks.datasets.__all__) == expected_benchmark_datasets
    assert tuple(benchmarks.fidelity.__all__) == expected_benchmark_fidelity
    assert tuple(benchmarks.synthetic.__all__) == expected_benchmark_synthetic
    assert tuple(cards.__all__) == expected_cards
    assert tuple(demo.__all__) == expected_demo
    assert tuple(exports.__all__) == expected_exports
    assert tuple(pipelines.__all__) == expected_pipelines
    assert set(PIPELINE_SUBMODULES).isdisjoint(pipelines.__all__)
    assert all(hasattr(pipelines, name) for name in PIPELINE_SUBMODULES)
    assert tuple(pipelines.advanced.__all__) == expected_pipeline_advanced
    assert tuple(pipelines.benchmarking.__all__) == expected_pipeline_benchmarking
    assert tuple(pipelines.comparative.__all__) == expected_pipeline_comparative
    assert tuple(pipelines.engines.__all__) == expected_pipeline_engines
    assert tuple(pipelines.operations.__all__) == expected_pipeline_operations
    assert tuple(pipelines.synthesis.__all__) == expected_pipeline_synthesis
    assert tuple(reports.__all__) == expected_reports
    assert tuple(studies.__all__) == expected_studies


def test_workflow_pipeline_root_prefers_benchmarking_subfacade() -> None:
    assert PIPELINE_ROOT_CANONICAL_SUBFACADE_OWNER_MODULES == {
        *(owner.owner_module for owner in ADVANCED_PIPELINE_FACADE_OWNERS),
        *BENCHMARKING_PIPELINE_OWNER_MODULES,
        *COMPARATIVE_PIPELINE_OWNER_MODULES,
        *(owner.owner_module for owner in DEMO_FACADE_OWNERS),
        *(owner.owner_module for owner in ENGINE_PIPELINE_FACADE_OWNERS),
        *OPERATIONS_PIPELINE_OWNER_MODULES,
        *SYNTHESIS_PIPELINE_OWNER_MODULES,
    }
    expected_pipeline_benchmarking, _ = build_lazy_export_index(
        ordered_facade_owners(BENCHMARKING_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_benchmarking if hasattr(pipelines, name)
    ) == ()
    assert all(
        hasattr(pipelines.benchmarking, name)
        for name in expected_pipeline_benchmarking
    )


def test_workflow_pipeline_root_prefers_synthesis_subfacade() -> None:
    expected_pipeline_synthesis, _ = build_lazy_export_index(
        ordered_facade_owners(SYNTHESIS_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_synthesis if hasattr(pipelines, name)
    ) == ()
    assert all(
        hasattr(pipelines.synthesis, name) for name in expected_pipeline_synthesis
    )


def test_workflow_pipeline_root_prefers_advanced_subfacade() -> None:
    expected_pipeline_advanced, _ = build_lazy_export_index(
        ordered_facade_owners(ADVANCED_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_advanced if hasattr(pipelines, name)
    ) == ()
    assert all(
        hasattr(pipelines.advanced, name) for name in expected_pipeline_advanced
    )


def test_workflow_pipeline_root_prefers_operations_subfacade() -> None:
    expected_pipeline_operations, _ = build_lazy_export_index(
        ordered_facade_owners(OPERATIONS_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_operations if hasattr(pipelines, name)
    ) == ()
    assert all(
        hasattr(pipelines.operations, name) for name in expected_pipeline_operations
    )


def test_workflow_pipeline_root_prefers_engine_subfacade() -> None:
    expected_pipeline_engines, _ = build_lazy_export_index(
        ordered_facade_owners(ENGINE_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_engines if hasattr(pipelines, name)
    ) == ()
    assert all(hasattr(pipelines.engines, name) for name in expected_pipeline_engines)


def test_workflow_pipeline_root_prefers_comparative_subfacade() -> None:
    expected_pipeline_comparative, _ = build_lazy_export_index(
        ordered_facade_owners(COMPARATIVE_PIPELINE_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_comparative if hasattr(pipelines, name)
    ) == ()
    assert all(
        hasattr(pipelines.comparative, name) for name in expected_pipeline_comparative
    )


def test_workflow_pipeline_root_prefers_demo_package() -> None:
    expected_pipeline_demo, _ = build_lazy_export_index(
        ordered_facade_owners(DEMO_FACADE_OWNERS)
    )

    assert tuple(
        name for name in expected_pipeline_demo if hasattr(pipelines, name)
    ) == ()
    assert all(hasattr(demo, name) for name in expected_pipeline_demo)


def test_workflow_root_prefers_canonical_owner_for_colliding_exports() -> None:
    assert (
        workflow.CrossStudyProteinStudyInput
        is cross_study_protein_harmonization.CrossStudyProteinStudyInput
    )
    assert workflow.WorkflowResult is WorkflowResult
    assert (
        workflow.load_public_benchmark_descriptor
        is public_benchmark_descriptors.load_public_benchmark_descriptor
    )
