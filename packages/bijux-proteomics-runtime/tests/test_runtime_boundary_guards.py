from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime import __all__ as runtime_public_entrypoints
from bijux_proteomics_runtime.charter import DEFAULT_RUNTIME_CHARTER_ENTRIES
from bijux_proteomics_runtime.runtime.control import __all__ as runtime_control_exports


def _runtime_source_root() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "src"
        / "bijux_proteomics_runtime"
    )


def test_runtime_source_tree_excludes_removed_legacy_buckets() -> None:
    runtime_root = _runtime_source_root()

    assert not (runtime_root / "registry").exists()
    assert not (runtime_root / "validation").exists()
    assert not (runtime_root / "runtime" / "adapters").exists()
    assert not (runtime_root / "runtime" / "infra").exists()


def test_runtime_source_tree_excludes_removed_generic_http_helper_names() -> None:
    runtime_root = _runtime_source_root()

    assert not (runtime_root / "api" / "correlation.py").exists()
    assert not (runtime_root / "api" / "deps.py").exists()
    assert not (runtime_root / "api" / "middleware.py").exists()
    assert (runtime_root / "runtime" / "context" / "correlation.py").exists()
    assert (runtime_root / "api" / "request_context.py").exists()
    assert (runtime_root / "api" / "request_logging.py").exists()


def test_runtime_source_tree_avoids_wrong_owner_symbols() -> None:
    runtime_root = _runtime_source_root()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(runtime_root.rglob("*.py"))
    )

    assert "bijux_proteomics.biology" not in source_text
    assert "PathwayContract" not in source_text
    assert "from bijux_proteomics_knowledge" not in source_text
    assert "import bijux_proteomics_knowledge" not in source_text
    assert "from bijux_proteomics_lab" not in source_text
    assert "import bijux_proteomics_lab" not in source_text
    assert "agentic_proteins" not in source_text


def test_runtime_charter_required_modules_exist_in_source_tree() -> None:
    runtime_root = _runtime_source_root()

    for entry in DEFAULT_RUNTIME_CHARTER_ENTRIES:
        for module_path in entry.required_modules:
            assert (runtime_root / module_path).exists(), (
                f"missing required runtime charter module: {module_path}"
            )


def test_runtime_root_exports_only_runtime_owned_entrypoints() -> None:
    assert tuple(runtime_public_entrypoints) == (
        "AppConfig",
        "RunManager",
        "cli",
        "create_app",
    )


def test_runtime_control_exports_release_blocking_execution_surfaces() -> None:
    required_exports = {
        "build_runtime_preflight_report",
        "build_runtime_partial_rerun_plan",
        "verify_runtime_artifact_integrity",
        "write_runtime_failure_report",
        "run_reviewable_import_path",
        "run_reviewable_sequence_path",
    }

    assert required_exports.issubset(set(runtime_control_exports))
