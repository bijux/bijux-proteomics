from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
RUNTIME_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-runtime"
RUNTIME_DOCS_ROOT = RUNTIME_ROOT / "docs"


def _assert_doc_references_live_paths(
    doc_name: str,
    *,
    required_references: tuple[str, ...],
) -> None:
    doc_path = RUNTIME_DOCS_ROOT / doc_name
    text = doc_path.read_text(encoding="utf-8")

    missing = [reference for reference in required_references if reference not in text]
    assert not missing, f"{doc_name} is missing references: {missing}"

    missing_paths = [
        reference
        for reference in required_references
        if not (RUNTIME_ROOT / reference).exists()
    ]
    assert not missing_paths, f"{doc_name} points at missing paths: {missing_paths}"


def test_runtime_public_surfaces_dossier_covers_live_owner_code_tests_and_fixtures() -> (
    None
):
    _assert_doc_references_live_paths(
        "PUBLIC-SURFACES.md",
        required_references=(
            "src/bijux_proteomics_runtime/api/cli.py",
            "src/bijux_proteomics_runtime/api/app.py",
            "src/bijux_proteomics_runtime/runs/manager.py",
            "src/bijux_proteomics_runtime/workflows/paths.py",
            "src/bijux_proteomics_runtime/workflows/advanced_diann_archive.py",
            "src/bijux_proteomics_runtime/runs/import_lineage.py",
            "tests/api/test_runtime_cli_surface.py",
            "tests/api/test_runtime_api_surface.py",
            "tests/runs/test_runtime_execution_conformance.py",
            "tests/workflows/test_runtime_workflow_paths.py",
            "tests/workflows/test_advanced_diann_archive_surface.py",
            "tests/workflows/test_advanced_diann_python_api_tutorial_surface.py",
            "tests/runs/test_runtime_import_surface.py",
            "tests/fixtures/execution/sequence_review_path.json",
            "tests/fixtures/execution/import_review_path.json",
            "tests/fixtures/api/runtime_health_response.json",
            "docs/ADVANCED-DIANN-PYTHON-API.md",
        ),
    )


def test_runtime_route_ownership_dossier_covers_live_route_owners_tests_and_fixtures() -> (
    None
):
    _assert_doc_references_live_paths(
        "ROUTE-OWNERSHIP.md",
        required_references=(
            "src/bijux_proteomics_runtime/api/routes/runtime_execution.py",
            "src/bijux_proteomics_runtime/api/routes/decision_briefs.py",
            "src/bijux_proteomics_runtime/api/routes/quant_reports.py",
            "src/bijux_proteomics_runtime/api/routes/ptm_reports.py",
            "src/bijux_proteomics_runtime/api/routes/evidence_graph.py",
            "src/bijux_proteomics_runtime/api/routes/lab_handoffs.py",
            "src/bijux_proteomics_runtime/api/routes/adapter_conformance.py",
            "src/bijux_proteomics_runtime/api/v1/endpoints/run.py",
            "src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py",
            "tests/api/test_runtime_execution_route_surface.py",
            "tests/api/test_decision_brief_route_surface.py",
            "tests/api/test_quant_report_route_surface.py",
            "tests/api/test_ptm_report_route_surface.py",
            "tests/api/test_evidence_graph_query_route_surface.py",
            "tests/api/test_lab_handoff_route_surface.py",
            "tests/api/test_adapter_conformance_route_surface.py",
            "tests/support/fixture_data.py",
            "tests/fixtures/api/evidence_lookup_response.json",
            "tests/fixtures/api/run_history_response.json",
        ),
    )


def test_runtime_provider_ownership_dossier_covers_live_provider_owners_tests_and_fixtures() -> (
    None
):
    _assert_doc_references_live_paths(
        "PROVIDER-OWNERSHIP.md",
        required_references=(
            "src/bijux_proteomics_runtime/providers/catalog.py",
            "src/bijux_proteomics_runtime/providers/contracts.py",
            "src/bijux_proteomics_runtime/providers/errors.py",
            "src/bijux_proteomics_runtime/providers/capabilities.py",
            "src/bijux_proteomics_runtime/providers/selection.py",
            "src/bijux_proteomics_runtime/providers/environment.py",
            "src/bijux_proteomics_runtime/providers/builtin/heuristic.py",
            "src/bijux_proteomics_runtime/providers/local/esmfold.py",
            "src/bijux_proteomics_runtime/providers/local/rosettafold.py",
            "src/bijux_proteomics_runtime/providers/remote/colabfold.py",
            "src/bijux_proteomics_runtime/providers/remote/openprotein.py",
            "src/bijux_proteomics_runtime/providers/remote/_async_utils.py",
            "tests/providers/test_runtime_provider_surface.py",
            "tests/providers/test_provider_capability_validation.py",
            "tests/providers/test_provider_capability_registry_surface.py",
            "tests/runs/test_runtime_execution_conformance.py",
            "tests/conftest.py",
            "tests/fixtures/execution/sequence_review_path.json",
            "tests/fixtures/execution/container_review_path.json",
        ),
    )


def test_runtime_artifact_lineage_dossier_covers_live_owner_code_tests_and_fixtures() -> (
    None
):
    _assert_doc_references_live_paths(
        "ARTIFACT-LINEAGE.md",
        required_references=(
            "src/bijux_proteomics_runtime/runs/contracts.py",
            "src/bijux_proteomics_runtime/support/artifact_formats.py",
            "src/bijux_proteomics_runtime/support/workspace.py",
            "src/bijux_proteomics_runtime/runs/ledger.py",
            "src/bijux_proteomics_runtime/runs/artifacts.py",
            "src/bijux_proteomics_runtime/runs/import_lineage.py",
            "src/bijux_proteomics_runtime/runs/replay.py",
            "src/bijux_proteomics_runtime/runs/integrity.py",
            "src/bijux_proteomics_runtime/runs/reruns.py",
            "src/bijux_proteomics_runtime/runs/launch_bundles.py",
            "src/bijux_proteomics_runtime/workflows/paths.py",
            "src/bijux_proteomics_runtime/runs/replay_decisions.py",
            "src/bijux_proteomics_runtime/runs/execution_decisions.py",
            "src/bijux_proteomics_runtime/runs/failure_reports.py",
            "src/bijux_proteomics_runtime/runs/recovery.py",
            "tests/runs/test_run_context_contracts.py",
            "tests/api/test_runtime_transport_contracts.py",
            "tests/runs/test_runtime_artifact_ledger.py",
            "tests/runs/test_runtime_integrity_surface.py",
            "tests/runs/test_runtime_import_surface.py",
            "tests/runs/test_runtime_replay_bundle.py",
            "tests/runs/test_runtime_replay_integrity_and_cache_end_to_end.py",
            "tests/runs/test_runtime_rerun_planning.py",
            "tests/runs/test_runtime_execution_bundles.py",
            "tests/execution/test_runtime_container_and_scheduler_end_to_end.py",
            "tests/workflows/test_runtime_workflow_paths.py",
            "tests/runs/test_runtime_replay_decision_reports.py",
            "tests/runs/test_runtime_execution_decision_reports.py",
            "tests/runs/test_runtime_cleanup_and_recovery.py",
            "tests/runs/test_runtime_failure_and_preflight.py",
            "tests/fixtures/execution/sequence_review_path.json",
            "tests/fixtures/execution/cache_claim_safety.json",
            "tests/fixtures/execution/import_review_path.json",
            "tests/fixtures/execution/replay_rerun_path.json",
            "tests/fixtures/execution/container_review_path.json",
            "tests/fixtures/execution/scheduler_review_path.json",
            "tests/fixtures/execution/failure_recovery_paths.json",
            "tests/fixtures/execution/preflight_failure_cases.json",
        ),
    )


def test_runtime_readme_links_runtime_ownership_dossiers() -> None:
    readme = (RUNTIME_ROOT / "README.md").read_text(encoding="utf-8")

    assert "[Public surfaces dossier](docs/PUBLIC-SURFACES.md)" in readme
    assert "[Route ownership dossier](docs/ROUTE-OWNERSHIP.md)" in readme
    assert "[Provider ownership dossier](docs/PROVIDER-OWNERSHIP.md)" in readme
    assert "[Artifact lineage dossier](docs/ARTIFACT-LINEAGE.md)" in readme
