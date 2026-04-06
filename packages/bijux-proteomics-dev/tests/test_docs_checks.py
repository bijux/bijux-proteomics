"""Tests for documentation checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.docs.consistency import run as run_docs_consistency
from bijux_proteomics_dev.docs.markdown_links import run as run_markdown_links


def test_docs_consistency_passes_for_repo() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert run_docs_consistency(repo_root) == 0


def test_markdown_links_pass_for_repo() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    assert run_markdown_links(repo_root) == 0
