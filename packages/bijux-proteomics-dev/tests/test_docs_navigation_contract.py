from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
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


class _RenderedNavigationParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._stack: list[tuple[str, dict[str, str], set[str]]] = []
        self._capture: str | None = None
        self._capture_tag: str | None = None
        self._buffer: list[str] = []
        self._detail_depth: int | None = None
        self._scoped_nav_depth: int | None = None
        self.detail_tabs: list[str] = []
        self.active_detail_tabs: list[str] = []
        self.sidebar_links: list[str] = []
        self.sidebar_title: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attr_map = {name: value or "" for name, value in attrs}
        classes = set(attr_map.get("class", "").split())
        self._stack.append((tag, attr_map, classes))
        depth = len(self._stack)

        if "bijux-detail-tabs" in classes and "hidden" not in attr_map:
            self._detail_depth = depth
        if attr_map.get("data-bijux-nav-variant") == "scoped":
            self._scoped_nav_depth = depth

        if tag == "a":
            if self._detail_depth is not None:
                self._capture = (
                    "active_detail_tabs"
                    if self._inside("bijux-tabs__item--active")
                    else "detail_tabs"
                )
                self._capture_tag = tag
                self._buffer = []
            elif (
                self._scoped_nav_depth is not None
                and self._inside("md-nav__list")
                and not self._inside("md-nav__source")
                and not self._inside("md-sidebar--secondary")
            ):
                self._capture = "sidebar_links"
                self._capture_tag = tag
                self._buffer = []
        elif (
            tag == "label"
            and "md-nav__title" in classes
            and self._scoped_nav_depth is not None
        ):
            self._capture = "sidebar_title"
            self._capture_tag = tag
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if (
            self._capture
            and self._capture_tag == tag
            and self._stack
            and self._stack[-1][0] == tag
        ):
            text = " ".join(" ".join(self._buffer).split())
            if text:
                if self._capture == "detail_tabs":
                    self.detail_tabs.append(text)
                elif self._capture == "active_detail_tabs":
                    self.detail_tabs.append(text)
                    self.active_detail_tabs.append(text)
                elif self._capture == "sidebar_links":
                    self.sidebar_links.append(text)
                elif self._capture == "sidebar_title":
                    self.sidebar_title = text
            self._capture = None
            self._capture_tag = None
            self._buffer = []

        if self._detail_depth == len(self._stack):
            self._detail_depth = None
        if self._scoped_nav_depth == len(self._stack):
            self._scoped_nav_depth = None

        if self._stack:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)

    def _inside(self, class_name: str) -> bool:
        return any(class_name in classes for _, _, classes in self._stack)


@pytest.fixture(scope="session")
def rendered_docs(tmp_path_factory: pytest.TempPathFactory) -> Path:
    site_dir = tmp_path_factory.mktemp("docs-site")
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


def _parse_navigation(site_dir: Path, relative_path: str) -> _RenderedNavigationParser:
    text = (site_dir / relative_path).read_text(encoding="utf-8")
    parser = _RenderedNavigationParser()
    parser.feed(text)
    if parser.sidebar_title is None:
        match = re.search(
            r'data-bijux-nav-variant="scoped".*?<label class="md-nav__title"[^>]*>'
            r".*?</a>\s*([^<]+?)\s*</label>",
            text,
            re.DOTALL,
        )
        if match:
            parser.sidebar_title = " ".join(match.group(1).split())
    parser.sidebar_links = [
        link for link in parser.sidebar_links if "bijux/bijux-proteomics" not in link
    ]
    return parser


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


def test_product_package_detail_tabs_follow_authored_order(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(rendered_docs, "04-bijux-proteomics-core/index.html")

    assert page.detail_tabs == [
        "Home",
        "Foundation",
        "Architecture",
        "Interfaces",
        "Operations",
        "Quality",
    ]
    assert page.active_detail_tabs == ["Home"]


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


@pytest.mark.parametrize(
    "relative_path",
    [
        "index.html",
        "01-bijux-proteomics/index.html",
        "02-agentic-proteins/index.html",
        "04-bijux-proteomics-core/index.html",
        "08-bijux-proteomics-maintain/index.html",
    ],
)
def test_overview_pages_hide_primary_sidebar(
    rendered_docs: Path,
    relative_path: str,
) -> None:
    text = _page_text(rendered_docs, relative_path)
    page = _parse_navigation(rendered_docs, relative_path)

    assert 'data-bijux-nav-empty="true"' in text
    assert page.sidebar_links == []


def test_repository_detail_tabs_keep_home_first(rendered_docs: Path) -> None:
    page = _parse_navigation(rendered_docs, "01-bijux-proteomics/index.html")

    assert page.detail_tabs == [
        "Home",
        "Foundation",
        "Operations",
    ]
    assert page.active_detail_tabs == ["Home"]


def test_repository_foundation_leaf_pages_keep_section_sidebar(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(
        rendered_docs,
        "01-bijux-proteomics/foundation/package-map/index.html",
    )

    assert page.active_detail_tabs == ["Foundation"]
    assert page.sidebar_title == "Foundation"
    assert page.sidebar_links == [
        "Foundation",
        "Platform Overview",
        "Repository Scope",
        "Workspace Layout",
        "Package Map",
        "Ownership Model",
        "Domain Language",
        "Documentation System",
        "Change Principles",
        "Decision Rules",
    ]


def test_repository_operations_leaf_pages_keep_section_sidebar(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(
        rendered_docs,
        "01-bijux-proteomics/operations/review-expectations/index.html",
    )

    assert page.active_detail_tabs == ["Operations"]
    assert page.sidebar_title == "Operations"
    assert page.sidebar_links == [
        "Operations",
        "Local Development",
        "Testing and Validation",
        "Release and Versioning",
        "API and Schema Governance",
        "Contributor Workflows",
        "Automation Surfaces",
        "Artifact Governance",
        "Review Expectations",
        "Change Management",
    ]


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


def test_repository_site_tab_uses_repository_label(rendered_docs: Path) -> None:
    text = _page_text(rendered_docs, "01-bijux-proteomics/index.html")

    assert re.search(r">\s*Repository\s*<", text)
    assert re.search(r">\s*Maintainer\s*<", text)


def test_rendered_header_marks_active_navigation_links(rendered_docs: Path) -> None:
    text = _page_text(rendered_docs, "07-bijux-proteomics-lab/operations/index.html")

    assert (
        'data-bijux-site-path="/07-bijux-proteomics-lab/" aria-current="page"' in text
    )
    assert (
        'data-bijux-detail-path="/07-bijux-proteomics-lab/operations/" '
        'aria-current="page"' in text
    )


def test_maintainer_detail_tabs_keep_expected_sections(rendered_docs: Path) -> None:
    page = _parse_navigation(rendered_docs, "08-bijux-proteomics-maintain/index.html")

    assert page.detail_tabs == [
        "Home",
        "bijux-proteomics-dev",
        "makes",
        "gh-workflows",
    ]


def test_maintenance_dev_leaf_pages_keep_section_sidebar(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(
        rendered_docs,
        "08-bijux-proteomics-maintain/bijux-proteomics-dev/security-gates/index.html",
    )

    assert page.active_detail_tabs == ["bijux-proteomics-dev"]
    assert page.sidebar_title == "bijux-proteomics-dev"
    assert page.sidebar_links == [
        "bijux-proteomics-dev",
        "Package Overview",
        "Scope and Non-Goals",
        "Module Map",
        "Quality Gates",
        "Security Gates",
        "Schema Governance",
        "Release Support",
        "Documentation Integrity",
        "Badge Catalog",
        "Operating Guidelines",
    ]


def test_maintenance_make_leaf_pages_keep_section_sidebar(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(
        rendered_docs,
        "08-bijux-proteomics-maintain/makes/package-dispatch/index.html",
    )

    assert page.active_detail_tabs == ["makes"]
    assert page.sidebar_title == "makes"
    assert page.sidebar_links == [
        "makes",
        "Make System Overview",
        "Root Entrypoints",
        "Environment Model",
        "Repository Layout",
        "Package Dispatch",
        "CI Targets",
        "Package Contracts",
        "Release Surfaces",
        "Authoring Rules",
    ]


def test_maintenance_workflow_leaf_pages_keep_section_sidebar(
    rendered_docs: Path,
) -> None:
    page = _parse_navigation(
        rendered_docs,
        "08-bijux-proteomics-maintain/gh-workflows/release-workflows/index.html",
    )

    assert page.active_detail_tabs == ["gh-workflows"]
    assert page.sidebar_title == "gh-workflows"
    assert page.sidebar_links == [
        "gh-workflows",
        "verify",
        "reusable-workflows",
        "deploy-docs",
        "release-workflows",
    ]


def test_leaf_pages_keep_sidebar_scoped_to_current_section(rendered_docs: Path) -> None:
    page = _parse_navigation(
        rendered_docs,
        "04-bijux-proteomics-core/architecture/code-navigation/index.html",
    )

    assert page.active_detail_tabs == ["Architecture"]
    assert page.sidebar_title == "Architecture"
    assert page.sidebar_links == [
        "Architecture",
        "Module Map",
        "Dependency Direction",
        "Execution Model",
        "State and Persistence",
        "Integration Seams",
        "Error Model",
        "Extensibility Model",
        "Code Navigation",
        "Architecture Risks",
    ]


@pytest.mark.parametrize(
    (
        "relative_path",
        "expected_active_detail",
        "expected_sidebar_title",
        "expected_sidebar_links",
    ),
    [
        (
            "04-bijux-proteomics-core/interfaces/index.html",
            ["Interfaces"],
            "Interfaces",
            [
                "Interfaces",
                "CLI Surface",
                "API Surface",
                "Configuration Surface",
                "Data Contracts",
                "Artifact Contracts",
                "Entrypoints and Examples",
                "Operator Workflows",
                "Public Imports",
                "Compatibility Commitments",
            ],
        ),
        (
            "04-bijux-proteomics-core/interfaces/api-surface/index.html",
            ["Interfaces"],
            "Interfaces",
            [
                "Interfaces",
                "CLI Surface",
                "API Surface",
                "Configuration Surface",
                "Data Contracts",
                "Artifact Contracts",
                "Entrypoints and Examples",
                "Operator Workflows",
                "Public Imports",
                "Compatibility Commitments",
            ],
        ),
        (
            "02-agentic-proteins/operations/index.html",
            ["Operations"],
            "Operations",
            [
                "Operations",
                "Installation and Setup",
                "Local Development",
                "Common Workflows",
                "Observability and Diagnostics",
                "Performance and Scaling",
                "Failure Recovery",
                "Release and Versioning",
                "Security and Safety",
                "Deployment Boundaries",
            ],
        ),
    ],
)
def test_section_pages_keep_sidebar_scoped_to_current_third_row(
    rendered_docs: Path,
    relative_path: str,
    expected_active_detail: list[str],
    expected_sidebar_title: str,
    expected_sidebar_links: list[str],
) -> None:
    page = _parse_navigation(rendered_docs, relative_path)

    assert page.active_detail_tabs == expected_active_detail
    assert page.sidebar_title == expected_sidebar_title
    assert page.sidebar_links == expected_sidebar_links


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
