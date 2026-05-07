"""Release-note impact guidance contracts."""

from __future__ import annotations

from pathlib import Path

IMPACT_LABELS = (
    "[accuracy]",
    "[robustness]",
    "[interpretability]",
    "[implementation]",
)
QUANTIFICATION_TOKENS = ("quantification", "quantify", "label-free")


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def _core_changelog() -> Path:
    return _repo_root() / "packages" / "bijux-proteomics-core" / "CHANGELOG.md"


def _unreleased_bullets(changelog_path: Path) -> list[str]:
    text = changelog_path.read_text(encoding="utf-8")
    after_unreleased = text.split("## Unreleased", maxsplit=1)[1]
    unreleased_block = after_unreleased.split("\n## ", maxsplit=1)[0]
    return [
        line.strip()
        for line in unreleased_block.splitlines()
        if line.lstrip().startswith("- ")
    ]


def test_core_quantification_release_notes_carry_impact_labels() -> None:
    changelog_path = _core_changelog()
    quantification_bullets = [
        bullet
        for bullet in _unreleased_bullets(changelog_path)
        if any(token in bullet.lower() for token in QUANTIFICATION_TOKENS)
    ]

    assert quantification_bullets, (
        f"expected unreleased quantification notes in {changelog_path}"
    )
    missing_labels = [
        bullet
        for bullet in quantification_bullets
        if not any(label in bullet for label in IMPACT_LABELS)
    ]
    assert not missing_labels, (
        "quantification release notes must declare one impact label in "
        f"{changelog_path}: {missing_labels}"
    )
