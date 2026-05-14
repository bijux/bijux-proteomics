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
    assert (
        "https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main"
        in rendered
    )
    assert (
        "https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white"
        in rendered
    )
    assert rendered.index("bijux-proteomics-runtime/") < rendered.index(
        "agentic-proteins/"
    )
    assert "ghcr-15%20packages" in rendered
    assert "published%20packages-15-2563EB" in rendered
    assert rendered.count("https://img.shields.io/pypi/v/") == 7
    assert rendered.count("/pkgs/container/") == 7
    assert rendered.count("https://bijux.io/bijux-proteomics/") == 7
    assert (
        "https://github.com/bijux?tab=packages&repo_name=bijux-proteomics" in rendered
    )
    assert "https://github.com/bijux?tab=packages)" not in rendered
    assert "https://pypi.org/project/proteomics/" not in rendered
    assert "https://pypi.org/project/bijux-proteomics/" not in rendered


def test_package_badge_block_prioritizes_the_current_distribution() -> None:
    rendered = render_badge_block(
        BadgeTarget(
            path=Path("packages/agentic-proteins/README.md"),
            kind="package",
            package_slug="agentic-proteins",
        )
    )
    assert (
        "https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg?branch=main"
        in rendered
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


def test_alias_package_badge_blocks_prioritize_the_current_distribution() -> None:
    cases = (
        (
            "bijux-proteomics",
            "packages/bijux-proteomics/README.md",
            "bijux--proteomics",
        ),
        ("proteomics", "packages/proteomics/README.md", "proteomics"),
        ("proteomics-core", "packages/proteomics-core/README.md", "proteomics--core"),
        (
            "proteomics-foundation",
            "packages/proteomics-foundation/README.md",
            "proteomics--foundation",
        ),
        (
            "proteomics-runtime",
            "packages/proteomics-runtime/README.md",
            "proteomics--runtime",
        ),
        (
            "proteomics-intelligence",
            "packages/proteomics-intelligence/README.md",
            "proteomics--intelligence",
        ),
        (
            "proteomics-knowledge",
            "packages/proteomics-knowledge/README.md",
            "proteomics--knowledge",
        ),
        ("proteomics-lab", "packages/proteomics-lab/README.md", "proteomics--lab"),
    )
    for package_slug, path, badge_label in cases:
        rendered = render_badge_block(
            BadgeTarget(
                path=Path(path),
                kind="package",
                package_slug=package_slug,
            )
        )
        assert (
            f"\n[![{package_slug}](https://img.shields.io/pypi/v/{package_slug}"
            in rendered
        )
        assert (
            f"\n[![{package_slug}](https://img.shields.io/badge/{badge_label}-ghcr"
            in rendered
        )
        assert (
            f"\n[![{package_slug} docs](https://img.shields.io/badge/docs-{badge_label}"
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
        Path("packages/bijux-proteomics-runtime/README.md"),
        Path("packages/bijux-proteomics-intelligence/README.md"),
        Path("packages/bijux-proteomics-knowledge/README.md"),
        Path("packages/bijux-proteomics-lab/README.md"),
        Path("packages/bijux-proteomics/README.md"),
        Path("packages/proteomics/README.md"),
        Path("packages/proteomics-core/README.md"),
        Path("packages/proteomics-foundation/README.md"),
        Path("packages/proteomics-runtime/README.md"),
        Path("packages/proteomics-intelligence/README.md"),
        Path("packages/proteomics-knowledge/README.md"),
        Path("packages/proteomics-lab/README.md"),
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        stripped = GENERATED_BLOCK_RE.sub("", text)
        assert "[![" not in stripped, (
            f"{path} contains inline badges outside the generated block"
        )
