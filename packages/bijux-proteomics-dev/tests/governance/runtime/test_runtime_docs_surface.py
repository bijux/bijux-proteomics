from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
RUNTIME_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-runtime"


def _runtime_docs() -> tuple[str, ...]:
    return (
        (RUNTIME_ROOT / "README.md").read_text(encoding="utf-8"),
        (RUNTIME_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
        (RUNTIME_ROOT / "docs" / "BOUNDARIES.md").read_text(encoding="utf-8"),
        (RUNTIME_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
        (RUNTIME_ROOT / "docs" / "ADVANCED-DIANN-PYTHON-API.md").read_text(
            encoding="utf-8"
        ),
    )


def test_runtime_docs_publish_live_charter_owner_modules_and_topology() -> None:
    readme, architecture, boundaries, contracts, tutorial = _runtime_docs()
    combined = "\n".join((readme, architecture, boundaries, contracts, tutorial))

    assert "charter.py" in readme
    assert "Execution charter" in readme
    assert "api/routes/" in architecture
    assert "api/v1/endpoints/" in architecture
    assert "runs/preflight.py" in architecture
    assert "runs/import_lineage.py" in architecture
    assert "runtime docs must name the current owner modules" in contracts.lower()
    assert "runs.manager" in boundaries
    assert "providers.selection" in boundaries
    assert "run_reviewable_sequence_path" in combined
    assert "run_reviewable_import_path" in combined


def test_runtime_docs_list_supported_execution_surfaces_limits_and_non_goals() -> None:
    readme, architecture, boundaries, contracts, tutorial = _runtime_docs()
    combined = "\n".join((readme, architecture, boundaries, contracts, tutorial))

    assert 'launch_surface="local"' in combined
    assert 'launch_surface="container"' in combined
    assert 'launch_surface="scheduler"' in combined
    assert 'launch_surface="import"' in combined
    assert 'execution_mode="auto"' in combined
    assert 'execution_mode="cpu"' in combined
    assert 'execution_mode="gpu"' in combined
    assert "does not provision GPUs" in readme
    assert "does not own container image build policy" in boundaries
    assert (
        "does not convert imported evidence into runtime-owned scientific truth"
        in contracts
    )


def test_runtime_docs_reject_removed_topology_names_and_stale_route_wrappers() -> None:
    text = "\n".join(_runtime_docs())

    assert "runtime/adapters/" not in text
    assert "registry/" not in text
    assert "validation/" not in text
    assert "api/correlation.py" not in text
    assert "api/deps.py" not in text
    assert "api/middleware.py" not in text
    assert "api/product_routes.py" not in text
    assert "`runtime/context/` owns" not in text
    assert "`runtime/control/` owns orchestration" not in text


def test_runtime_docs_do_not_teach_broad_root_convenience_to_internal_consumers() -> (
    None
):
    text = "\n".join(_runtime_docs())

    assert (
        "Python integrations should start from the canonical runtime package"
        not in text
    )
    assert "canonical runtime roots" not in text
    assert (
        "from bijux_proteomics_runtime import AppConfig, RunManager, create_app"
        not in text
    )
    assert "from bijux_proteomics_runtime.api.app import AppConfig, create_app" in text
    assert "from bijux_proteomics_runtime.runs.manager import RunManager" in text


def test_runtime_docs_publish_advanced_diann_python_api_tutorial() -> None:
    readme, _, _, _, tutorial = _runtime_docs()

    assert "[Advanced DIA-NN Python API tutorial](docs/ADVANCED-DIANN-PYTHON-API.md)" in readme
    assert "run_resumable_advanced_diann_workflow" in tutorial
    assert "archive_completed_advanced_diann_run" in tutorial
    assert "load_completed_run" in tutorial
