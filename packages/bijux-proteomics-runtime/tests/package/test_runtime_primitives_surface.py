from __future__ import annotations

from bijux_proteomics_foundation import (
    hash_payload as foundation_hash_payload,
)
from bijux_proteomics_foundation import (
    hash_text as foundation_hash_text,
)
from bijux_proteomics_foundation import (
    to_canonical_json,
)
from bijux_proteomics_runtime.support.primitives import (
    CostSummary,
    ExecutionStatus,
    FailureType,
    Outcome,
    ToolStatus,
    WorkflowState,
    deterministic_id,
    hash_payload,
    stable_json,
    suggest_next_action,
)
from bijux_proteomics_runtime.support.primitives.contracts import (
    EXECUTION_REVIEW_CONTRACT,
)
from bijux_proteomics_runtime.support.primitives.execution import ExecutionContext
from bijux_proteomics_runtime.support.primitives.surface_area import (
    CONFIG_KNOBS,
    PUBLIC_ENTRYPOINTS,
)
from bijux_proteomics_runtime.support.primitives.tooling import ToolInvocationSpec


def test_runtime_core_surface_smoke() -> None:
    _ = ExecutionContext
    _ = ToolInvocationSpec
    _ = CostSummary
    _ = FailureType


def test_runtime_core_exports_failure_helpers() -> None:
    assert suggest_next_action(FailureType.INPUT_INVALID) == "fix_input_sequence"


def test_runtime_core_exports_deterministic_id() -> None:
    assert deterministic_id("runtime", {"id": 1}).startswith("runtime_")


def test_runtime_core_reuses_foundation_hashing_and_serialization() -> None:
    payload = {"nested": {"b": 2, "a": 1}, "id": 1}

    assert stable_json(payload) == to_canonical_json(payload)
    assert hash_payload(payload) == foundation_hash_payload(payload)
    assert (
        deterministic_id("runtime", payload)
        == f"runtime_{foundation_hash_payload(payload)}"
    )
    assert foundation_hash_text("runtime")


def test_runtime_core_exports_status_enums() -> None:
    assert ExecutionStatus.COMPLETED.value == "completed"
    assert WorkflowState.DONE.value == "done"
    assert Outcome.ACCEPTED.value == "accepted"
    assert ToolStatus.SUCCESS.value == "success"


def test_runtime_surface_area_uses_canonical_cli_entrypoint() -> None:
    assert "bijux_proteomics_runtime.api.cli.cli" in PUBLIC_ENTRYPOINTS


def test_runtime_surface_area_uses_canonical_run_manager_entrypoint() -> None:
    assert "bijux_proteomics_runtime.runs.RunManager" in PUBLIC_ENTRYPOINTS


def test_runtime_surface_area_uses_reviewable_runtime_paths() -> None:
    assert (
        "bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path"
        in PUBLIC_ENTRYPOINTS
    )
    assert (
        "bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path"
        in PUBLIC_ENTRYPOINTS
    )


def test_runtime_surface_area_uses_workflow_assurance_ledgers() -> None:
    from bijux_proteomics_runtime.workflows import (
        build_flagship_operator_path,
        build_workflow_assurance_matrix,
    )

    assert (
        build_flagship_operator_path().path_id
        == "runtime-sequence-review-operator-path"
    )
    assert build_workflow_assurance_matrix()


def test_runtime_surface_area_exposes_workflow_cache_reuse_planning() -> None:
    from bijux_proteomics_runtime.workflows import (
        WorkflowCacheReusePlan,
        build_workflow_cache_reuse_plan,
    )

    assert WorkflowCacheReusePlan is not None
    assert callable(build_workflow_cache_reuse_plan)


def test_runtime_surface_area_exposes_workflow_dag_planning() -> None:
    from bijux_proteomics_runtime.workflows import (
        ProteomicsDagPlan,
        WorkflowDataType,
        WorkflowDagValidationReport,
        WorkflowStepTypeValidationReport,
        build_parallel_execution_plan,
        build_proteomics_dag_plan,
        validate_proteomics_workflow_step_types,
        validate_proteomics_dag_plan,
    )

    assert ProteomicsDagPlan is not None
    assert WorkflowDataType.PEPTIDE_QUANT_MATRIX.value == "peptide_quant_matrix"
    assert WorkflowDagValidationReport is not None
    assert WorkflowStepTypeValidationReport is not None
    assert callable(build_proteomics_dag_plan)
    assert callable(validate_proteomics_workflow_step_types)
    assert callable(validate_proteomics_dag_plan)
    assert callable(build_parallel_execution_plan)


def test_runtime_surface_area_exposes_resumable_advanced_diann_execution() -> None:
    from bijux_proteomics_runtime.workflows import (
        AdvancedDiannDryRunReport,
        AdvancedDiannDryRunStatus,
        AdvancedDiannRuntimeRunReport,
        AdvancedDiannRuntimeStage,
        AdvancedDiannRuntimeStatus,
        dry_run_resumable_advanced_diann_workflow,
        run_resumable_advanced_diann_workflow,
    )

    assert AdvancedDiannDryRunReport is not None
    assert AdvancedDiannDryRunStatus.READY.value == "ready"
    assert AdvancedDiannRuntimeRunReport is not None
    assert AdvancedDiannRuntimeStage.MATRICES.value == "advanced-diann-matrices"
    assert AdvancedDiannRuntimeStatus.COMPLETED.value == "completed"
    assert callable(dry_run_resumable_advanced_diann_workflow)
    assert callable(run_resumable_advanced_diann_workflow)


def test_runtime_surface_area_exposes_advanced_diann_comparison() -> None:
    from bijux_proteomics_runtime.workflows import (
        AdvancedDiannClaimComparisonState,
        AdvancedDiannProteinComparisonState,
        AdvancedDiannRejectedRowComparisonState,
        AdvancedDiannRuntimeComparisonReport,
        compare_advanced_diann_runtime_outputs,
    )

    assert AdvancedDiannRuntimeComparisonReport is not None
    assert AdvancedDiannClaimComparisonState.SUPPORTED.value == "supported"
    assert AdvancedDiannProteinComparisonState.ACCEPTED.value == "accepted"
    assert AdvancedDiannRejectedRowComparisonState.REJECTED.value == "rejected"
    assert callable(compare_advanced_diann_runtime_outputs)


def test_runtime_surface_area_exposes_workflow_failure_reports() -> None:
    from bijux_proteomics_runtime.workflows import (
        WorkflowFailureReport,
        build_workflow_failure_report,
        write_workflow_failure_report,
    )

    assert WorkflowFailureReport is not None
    assert callable(build_workflow_failure_report)
    assert callable(write_workflow_failure_report)


def test_runtime_surface_area_uses_runtime_extension_points() -> None:
    from bijux_proteomics_runtime.support.primitives.surface_area import (
        EXTENSION_POINTS,
    )

    assert "bijux_proteomics_runtime.providers" in EXTENSION_POINTS
    assert "bijux_proteomics_runtime.providers.remote" in EXTENSION_POINTS


def test_runtime_surface_area_tracks_live_run_config_knobs() -> None:
    assert "RunConfig.execution_mode" in CONFIG_KNOBS
    assert "RunConfig.launch_surface" in CONFIG_KNOBS
    assert "RunConfig.max_bundle_artifact_bytes" in CONFIG_KNOBS


def test_runtime_contracts_track_review_and_failure_surfaces() -> None:
    assert (
        EXECUTION_REVIEW_CONTRACT["sequence_review_path"]
        == "bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path"
    )
    assert (
        EXECUTION_REVIEW_CONTRACT["failure_report_writer"]
        == "bijux_proteomics_runtime.runs.failure_reports.write_runtime_failure_report"
    )


def test_runtime_core_contract_metadata_avoids_stale_biology_symbols() -> None:
    combined = (
        *PUBLIC_ENTRYPOINTS,
        *CONFIG_KNOBS,
        *EXECUTION_REVIEW_CONTRACT.values(),
    )
    assert not any("bijux_proteomics.biology" in entry for entry in combined)
    assert not any("PathwayContract" in entry for entry in combined)
