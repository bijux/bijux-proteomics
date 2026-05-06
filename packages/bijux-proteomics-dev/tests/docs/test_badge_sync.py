from __future__ import annotations

from pathlib import Path
import re

from bijux_proteomics_dev.docs.badge_sync import (
    BadgeTarget,
    load_badge_catalog,
    render_badge_block,
    synchronize_badges,
)

GENERATED_BLOCK_RE = re.compile(
    r"<!-- bijux-proteomics-badges:generated:start -->.*?<!-- bijux-proteomics-badges:generated:end -->",
    re.DOTALL,
)


def test_badge_catalog_exposes_expected_templates() -> None:
    catalog = load_badge_catalog()
    assert set(catalog) == {
        "family-docs-badge",
        "family-ghcr-badge",
        "family-pypi-badge",
        "package-summary",
        "repository-summary",
    }


def test_repository_badge_block_renders_all_public_badge_groups() -> None:
    rendered = render_badge_block(
        BadgeTarget(path=Path("README.md"), kind="repository")
    )
    assert "https://pypi.org/project/bijux-proteomics-runtime/" in rendered
    assert "https://pypi.org/project/agentic-proteins/" in rendered
    assert rendered.index("bijux-proteomics-runtime/") < rendered.index(
        "agentic-proteins/"
    )
    assert rendered.count("https://img.shields.io/pypi/v/") == 7
    assert rendered.count("/pkgs/container/") == 7
    assert rendered.count("https://bijux.io/bijux-proteomics/") == 7
    assert (
        "https://github.com/bijux?tab=packages&repo_name=bijux-proteomics" in rendered
    )
    assert "https://github.com/bijux?tab=packages)" not in rendered


def test_package_badge_block_prioritizes_the_current_distribution() -> None:
    rendered = render_badge_block(
        BadgeTarget(
            path=Path("packages/agentic-proteins/README.md"),
            kind="package",
            package_slug="agentic-proteins",
        )
    )
    assert (
        "\n[![agentic-proteins](https://img.shields.io/pypi/v/agentic-proteins"
        in rendered
    )
    assert (
        "\n[![agentic-proteins](https://img.shields.io/badge/agentic--proteins-ghcr"
        in rendered
    )
    assert (
        "\n[![agentic-proteins docs](https://img.shields.io/badge/docs-agentic--proteins"
        in rendered
    )


def test_badge_surfaces_are_synchronized() -> None:
    assert synchronize_badges(check=True) == []


def test_managed_surfaces_only_use_generated_badges() -> None:
    targets = [
        Path("README.md"),
        Path("docs/index.md"),
        Path("packages/agentic-proteins/README.md"),
        Path("packages/bijux-proteomics-foundation/README.md"),
        Path("packages/bijux-proteomics-core/README.md"),
        Path("packages/bijux-proteomics-intelligence/README.md"),
        Path("packages/bijux-proteomics-knowledge/README.md"),
        Path("packages/bijux-proteomics-lab/README.md"),
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        stripped = GENERATED_BLOCK_RE.sub("", text)
        assert "[![" not in stripped, (
            f"{path} contains inline badges outside the generated block"
        )
