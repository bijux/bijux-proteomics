from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read_runtime_doc(name: str) -> str:
    return (
        REPO_ROOT
        / "docs"
        / "09-bijux-proteomics-runtime"
        / name
    ).read_text(encoding="utf-8")


def test_runtime_index_links_to_runtime_proof_accounting() -> None:
    text = _read_runtime_doc("index.md")

    assert "Runtime Proof Accounting" in text
    assert "runtime-proof-accounting" in text


def test_runtime_proof_accounting_page_names_proof_classes_and_promotion_paths() -> None:
    text = _read_runtime_doc("runtime-proof-accounting.md")

    assert "# Runtime Proof Accounting" in text
    assert "`raw_execution`" in text
    assert "`import_backed_execution`" in text
    assert "`replay_backed_execution`" in text
    assert "`simulation_only`" in text
    assert "test_runtime_container_and_scheduler_end_to_end.py" in text
    assert "test_runtime_cli_surface.py" in text
    assert "test_runtime_execution_control_benchmark_surface.py" in text
    assert "run_benchmark_dda_import_path" in text
    assert "run_benchmark_dia_import_path" in text
    assert "targeted_transition_review_package/package_manifest.json" in text


def test_flagship_run_registry_page_names_runtime_proof_classes() -> None:
    text = _read_runtime_doc("flagship-run-registry.md")

    assert "Proof class" in text
    assert "`import_backed_execution`" in text
    assert "`raw_execution`" in text
    assert "runtime-proof-accounting.md" in text
