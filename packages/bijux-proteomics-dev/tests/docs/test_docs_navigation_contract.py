from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
MERMAID_RESERVED_IDS = {
    "class",
    "classdef",
    "click",
    "default",
    "end",
    "graph",
    "linkstyle",
    "style",
    "subgraph",
}


@pytest.fixture(scope="session")
def rendered_docs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    artifacts_root = REPO_ROOT / "artifacts" / "bijux-proteomics-dev" / "test"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    site_dir = Path(tempfile.mkdtemp(prefix="docs-site-", dir=artifacts_root))
    subprocess.run(
        [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
            "--quiet",
            "--config-file",
            str(REPO_ROOT / "mkdocs.yml"),
            "--site-dir",
            str(site_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    return site_dir


def _page_text(site_dir: Path, relative_path: str) -> str:
    return (site_dir / relative_path).read_text(encoding="utf-8")


def _iter_mermaid_blocks() -> list[tuple[Path, str]]:
    blocks: list[tuple[Path, str]] = []
    for path in (REPO_ROOT / "docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        blocks.extend(
            (path.relative_to(REPO_ROOT), match.group(1))
            for match in re.finditer(r"```mermaid\n([\s\S]*?)\n```", text)
        )
    return blocks


def _declared_mermaid_node_ids(block: str) -> set[str]:
    ids: set[str] = set()
    for line in block.splitlines():
        match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*\[", line)
        if match:
            ids.add(match.group(1).lower())
    return ids


def test_docs_mermaid_diagrams_avoid_reserved_node_ids() -> None:
    failures = []

    for path, block in _iter_mermaid_blocks():
        reserved_ids = sorted(
            MERMAID_RESERVED_IDS.intersection(_declared_mermaid_node_ids(block))
        )
        if reserved_ids:
            failures.append(f"{path}: reserved Mermaid ids {', '.join(reserved_ids)}")

    assert not failures, "Mermaid diagrams use reserved node ids:\n" + "\n".join(
        failures
    )


def test_primary_sidebar_does_not_use_lifted_nav_mode(rendered_docs: Path) -> None:
    text = _page_text(
        rendered_docs, "05-bijux-proteomics-intelligence/interfaces/index.html"
    )

    assert 'data-bijux-nav-variant="scoped"' in text
    assert '<nav class="md-nav md-nav--primary md-nav--lifted"' not in text


def test_header_navigation_uses_canonical_path_contract(rendered_docs: Path) -> None:
    text = _page_text(rendered_docs, "04-bijux-proteomics-core/interfaces/index.html")

    assert 'data-bijux-site-path="/"' in text
    assert 'data-bijux-site-path="/04-bijux-proteomics-core/"' in text
    assert 'data-bijux-site-path="/08-bijux-proteomics-maintain/"' in text
    assert 'data-bijux-detail-root-path="/04-bijux-proteomics-core/"' in text
    assert 'data-bijux-detail-path="/04-bijux-proteomics-core/interfaces/"' in text
    assert 'data-bijux-detail-path="/04-bijux-proteomics-core/architecture/"' in text
    assert "data-bijux-site-target" not in text
    assert "data-bijux-detail-target" not in text
    assert "data-bijux-detail-root=" not in text


def test_hub_navigation_excludes_private_sites(rendered_docs: Path) -> None:
    text = _page_text(rendered_docs, "index.html")

    assert 'href="https://bijux.io/bijux-core/"' in text
    assert "bijux-genomics" not in text


def test_rendered_header_marks_active_navigation_links(rendered_docs: Path) -> None:
    text = _page_text(rendered_docs, "07-bijux-proteomics-lab/operations/index.html")

    assert (
        'data-bijux-site-path="/07-bijux-proteomics-lab/" aria-current="page"' in text
    )
    assert (
        'data-bijux-detail-path="/07-bijux-proteomics-lab/operations/" '
        'aria-current="page"' in text
    )


def test_navigation_sync_prefers_authored_active_links() -> None:
    script = (
        REPO_ROOT / "docs" / "assets" / "javascripts" / "navigation-sync.js"
    ).read_text(encoding="utf-8")
    nav_state = (
        REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "nav-state.js"
    ).read_text(encoding="utf-8")
    detail_tabs = (
        REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "detail-tabs.js"
    ).read_text(encoding="utf-8")

    assert "window.bijuxShell?.bootstrap?.ensureBound" in script
    assert "[data-bijux-site-path][aria-current='page']" in nav_state
    assert "[data-bijux-detail-path][aria-current='page']" in detail_tabs
