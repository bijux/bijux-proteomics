from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_release_guidance_requires_runtime_compatibility_validation() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "make quality-runtime-migration-validation" in readme
    assert "as canonical and `agentic-proteins` as compatibility" in readme


def test_operations_nav_includes_runtime_compatibility_validation_runbook() -> None:
    operations_index = (
        REPO_ROOT / "docs" / "01-bijux-proteomics" / "operations" / "index.md"
    ).read_text(encoding="utf-8")
    mkdocs_nav = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "Runtime Migration Validation" in operations_index
    assert "runtime-migration-validation.md" in mkdocs_nav
