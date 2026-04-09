"""Release documentation honesty checks."""

from __future__ import annotations

from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _release_docs() -> list[Path]:
    docs_dir = _repo_root() / "docs"
    return sorted(docs_dir.glob("*/operations/release-and-versioning.md"))


def test_release_docs_do_not_reference_missing_version_files() -> None:
    for doc_path in _release_docs():
        text = doc_path.read_text(encoding="utf-8")
        assert "_version.py" not in text, f"stale version file reference in {doc_path}"


def test_release_docs_do_not_claim_nonexistent_smoke_suite() -> None:
    for doc_path in _release_docs():
        text = doc_path.read_text(encoding="utf-8")
        assert "tests/smoke" not in text, f"stale smoke suite reference in {doc_path}"


def test_release_docs_use_real_versioning_language() -> None:
    for doc_path in _release_docs():
        text = doc_path.read_text(encoding="utf-8")
        has_explicit_version = "release version is explicit in" in text
        has_vcs_version = (
            "version is resolved from Git tags through `hatch-vcs`" in text
        )
        assert has_explicit_version or has_vcs_version, (
            f"missing concrete versioning anchor in {doc_path}"
        )
