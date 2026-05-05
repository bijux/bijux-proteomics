from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
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


def test_runtime_public_surfaces_dossier_covers_live_owner_code_tests_and_fixtures() -> None:
    _assert_doc_references_live_paths(
        "PUBLIC-SURFACES.md",
        required_references=(
            "src/bijux_proteomics_runtime/interfaces/cli.py",
            "src/bijux_proteomics_runtime/api/app.py",
            "src/bijux_proteomics_runtime/runs/manager.py",
            "src/bijux_proteomics_runtime/workflows/paths.py",
            "src/bijux_proteomics_runtime/runs/import_lineage.py",
            "tests/test_runtime_cli_surface.py",
            "tests/test_runtime_api_surface.py",
            "tests/test_runtime_execution_conformance.py",
            "tests/test_runtime_workflow_paths.py",
            "tests/test_runtime_import_surface.py",
            "tests/fixtures/execution/sequence_review_path.json",
            "tests/fixtures/execution/import_review_path.json",
            "tests/fixtures/api/runtime_health_response.json",
        ),
    )


def test_runtime_route_ownership_dossier_covers_live_route_owners_tests_and_fixtures() -> None:
    _assert_doc_references_live_paths(
        "ROUTE-OWNERSHIP.md",
        required_references=(
            "src/bijux_proteomics_runtime/api/routes/runtime_execution.py",
            "src/bijux_proteomics_runtime/api/routes/review_packets.py",
            "src/bijux_proteomics_runtime/api/routes/quant_reports.py",
            "src/bijux_proteomics_runtime/api/routes/ptm_reports.py",
            "src/bijux_proteomics_runtime/api/routes/evidence_graph.py",
            "src/bijux_proteomics_runtime/api/routes/lab_handoffs.py",
            "src/bijux_proteomics_runtime/api/routes/adapter_conformance.py",
            "src/bijux_proteomics_runtime/api/v1/endpoints/run.py",
            "src/bijux_proteomics_runtime/api/v1/endpoints/runtime_contracts.py",
            "tests/test_runtime_execution_route_surface.py",
            "tests/test_review_packet_route_surface.py",
            "tests/test_quant_report_route_surface.py",
            "tests/test_ptm_report_route_surface.py",
            "tests/test_evidence_graph_query_route_surface.py",
            "tests/test_lab_handoff_route_surface.py",
            "tests/test_adapter_conformance_route_surface.py",
            "tests/runtime_fixture_data.py",
            "tests/fixtures/api/evidence_lookup_response.json",
            "tests/fixtures/api/run_history_response.json",
        ),
    )


def test_runtime_readme_links_runtime_ownership_dossiers() -> None:
    readme = (RUNTIME_ROOT / "README.md").read_text(encoding="utf-8")

    assert "[Public surfaces dossier](docs/PUBLIC-SURFACES.md)" in readme
    assert "[Route ownership dossier](docs/ROUTE-OWNERSHIP.md)" in readme
