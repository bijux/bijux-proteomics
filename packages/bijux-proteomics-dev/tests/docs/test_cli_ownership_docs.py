from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_runtime_and_compat_docs_name_the_workflow_cli_owner() -> None:
    runtime_readme = (
        REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "README.md"
    ).read_text(encoding="utf-8")
    core_readme = (
        REPO_ROOT / "packages" / "bijux-proteomics-core" / "README.md"
    ).read_text(encoding="utf-8")
    compat_readme = (
        REPO_ROOT / "packages" / "agentic-proteins" / "README.md"
    ).read_text(encoding="utf-8")
    compat_cli_docs = (
        REPO_ROOT / "docs" / "02-agentic-proteins" / "interfaces" / "cli-surface.md"
    ).read_text(encoding="utf-8")
    normalized_compat_cli_docs = " ".join(compat_cli_docs.split())

    assert "Flagship workflow CLI command: `bijux-proteomics-runtime`" in runtime_readme
    assert "not the flagship workflow runner" in core_readme
    assert "Legacy compatibility CLI command: `agentic-proteins`" in compat_readme
    assert "bijux-proteomics-runtime --help" in compat_readme
    assert "agentic-proteins --help" in compat_readme
    assert (
        "new workflow use should start from `bijux-proteomics-runtime --help`"
        in normalized_compat_cli_docs
    )


def test_non_compat_docs_and_examples_default_to_canonical_entrypoints() -> None:
    disallowed_patterns = (
        "from agentic_proteins",
        "import agentic_proteins",
        "agentic-proteins --help",
        "pip install agentic-proteins",
    )
    excluded_prefixes = (
        "artifacts/",
        "packages/agentic-proteins/",
        "docs/02-agentic-proteins/",
        "docs/09-bijux-proteomics-runtime/migration-ledger/",
    )
    failures: list[str] = []
    for path in sorted(REPO_ROOT.rglob("*.md")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(excluded_prefixes):
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in disallowed_patterns:
            if pattern in text:
                failures.append(f"{rel}: {pattern}")
    assert not failures, (
        "non-compat docs must default to canonical entrypoints:\n" + "\n".join(failures)
    )
