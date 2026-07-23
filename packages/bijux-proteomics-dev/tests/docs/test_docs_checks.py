"""Tests for documentation checks."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.docs.consistency import (
    nav_refs,
)
from bijux_proteomics_dev.docs.consistency import (
    run as run_docs_consistency,
)
from bijux_proteomics_dev.docs.markdown_links import run as run_markdown_links


def test_docs_consistency_passes_for_repo() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
    assert run_docs_consistency(repo_root) == 0


def test_markdown_links_pass_for_repo() -> None:
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )
    assert run_markdown_links(repo_root) == 0


def test_nav_refs_excludes_redirect_sources(tmp_path: Path) -> None:
    mkdocs_path = tmp_path / "mkdocs.yml"
    mkdocs_path.write_text(
        """\
plugins:
  - redirects:
      redirect_maps:
        retired.md: canonical.md
nav:
  - Home: index.md
  - Guide: guide/index.md
extra:
  owner: bijux
""",
        encoding="utf-8",
    )

    assert nav_refs(mkdocs_path) == {Path("index.md"), Path("guide/index.md")}
