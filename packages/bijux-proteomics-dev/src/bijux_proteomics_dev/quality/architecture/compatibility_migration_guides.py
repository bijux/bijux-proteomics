from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.architecture.agentic_compatibility_inventory import (
    AgenticModuleClassification,
    build_agentic_compatibility_inventory,
)


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError(
        "Unable to resolve repository root for compatibility migration guides"
    )


REPO_ROOT = _repo_root()
GUIDE_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-canonical-migration-guide.md"
)


@dataclass(frozen=True)
class CompatibilityMigrationGuideEntry:
    legacy_module: str
    canonical_targets: tuple[str, ...]
    status: str
    migration_action: str


def build_compatibility_migration_guide(
    repo_root: Path,
) -> tuple[CompatibilityMigrationGuideEntry, ...]:
    """Build migration guide entries from the live compatibility inventory."""
    entries: list[CompatibilityMigrationGuideEntry] = []
    for inventory_entry in build_agentic_compatibility_inventory(repo_root):
        entries.append(
            CompatibilityMigrationGuideEntry(
                legacy_module=inventory_entry.import_path,
                canonical_targets=inventory_entry.canonical_targets,
                status=inventory_entry.classification.value,
                migration_action=inventory_entry.migration_action,
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.legacy_module))


def _render_markdown(entries: tuple[CompatibilityMigrationGuideEntry, ...]) -> str:
    wrapper_count = sum(
        1
        for entry in entries
        if entry.status == AgenticModuleClassification.WRAPPER.value
    )
    dead_count = sum(
        1 for entry in entries if entry.status == AgenticModuleClassification.DEAD.value
    )
    lines = [
        "---",
        "title: agentic-proteins Canonical Migration Guide",
        "audience: maintainer",
        "type: reference",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        "last_reviewed: 2026-04-29",
        "---",
        "",
        "# agentic-proteins Canonical Migration Guide",
        "",
        "This guide shows how compatibility imports map back to canonical package ownership. The point is not to preserve the bridge forever; it is to make every remaining legacy path reviewable and replaceable.",
        "",
        "## Current Posture",
        "",
        f"- total compatibility modules: {len(entries)}",
        f"- wrapper modules: {wrapper_count}",
        f"- dead modules: {dead_count}",
        "",
        "## Migration Map",
        "",
        "| legacy module | status | canonical target(s) | migration action |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        targets = (
            "<br>".join(f"`{target}`" for target in entry.canonical_targets)
            if entry.canonical_targets
            else "_none declared_"
        )
        lines.append(
            f"| `{entry.legacy_module}` | `{entry.status}` | {targets} | {entry.migration_action} |"
        )
    lines.extend(
        [
            "",
            "## Reading The Guide",
            "",
            "- `wrapper` means the compatibility module is a narrow bridge and callers should move directly to the named canonical target.",
            "- `dead` means the module no longer carries meaningful behavior and should be deleted once callers disappear.",
            "- `canonical` or `duplicate` would be release-blocking because the compatibility family is not allowed to regain original product logic.",
            "- this document should be regenerated whenever compatibility forwarding changes so release and retirement discussions are based on current code rather than memory.",
            "",
        ]
    )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[CompatibilityMigrationGuideEntry, ...]) -> bool:
    if not GUIDE_PATH.exists():
        return False
    return GUIDE_PATH.read_text(encoding="utf-8") == _render_markdown(entries)


def run(check: bool = False) -> int:
    entries = build_compatibility_migration_guide(REPO_ROOT)
    if check:
        if _is_up_to_date(entries):
            print(
                f"compatibility migration guide is up to date for {len(entries)} modules"
            )
            return 0
        print("compatibility migration guide is stale; regenerate it")
        return 1
    GUIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GUIDE_PATH.write_text(_render_markdown(entries), encoding="utf-8")
    print(f"generated compatibility migration guide for {len(entries)} modules")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the compatibility-to-canonical migration guide."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated migration guide is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
