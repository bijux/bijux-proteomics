from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.architecture.runtime_boundaries import load_policy
from bijux_proteomics_dev.quality.architecture.scanner import (
    import_references,
    iter_python_files,
    parse_python_module,
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


def _allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    values: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        values.add(value)
    return values


def _is_forwarding_module(tree: ast.Module, target_prefixes: tuple[str, ...]) -> bool:
    def _matches_target(module_name: str) -> bool:
        return any(
            module_name == target_prefix or module_name.startswith(f"{target_prefix}.")
            for target_prefix in target_prefixes
        )

    module_aliases: set[str] = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                continue
            if (
                all(isinstance(target, ast.Name) for target in node.targets)
                and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id in module_aliases
            ):
                continue
            return False
        if isinstance(node, ast.Import):
            if all(_matches_target(alias.name) for alias in node.names):
                for alias in node.names:
                    if alias.asname:
                        module_aliases.add(alias.asname)
                continue
            return False
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _matches_target(module):
                for alias in node.names:
                    if alias.asname:
                        module_aliases.add(alias.asname)
                continue
            return False
        return False
    return True


def build_compatibility_migration_guide(
    repo_root: Path,
) -> tuple[CompatibilityMigrationGuideEntry, ...]:
    """Build migration guide entries from compatibility forwarding modules."""
    policy = load_policy(repo_root)
    allowlist = _allowlist(policy.compat_forwarding.non_forwarding_allowlist_path)
    entries: list[CompatibilityMigrationGuideEntry] = []
    package_root = policy.compat_forwarding.package_root
    for path in iter_python_files(package_root):
        relative_path = path.relative_to(package_root).as_posix()
        if relative_path == "__init__.py":
            continue
        tree = parse_python_module(path).tree
        targets = tuple(sorted(import_references(tree)))
        legacy_module = (
            "agentic_proteins."
            + relative_path.removesuffix(".py").replace("/", ".").replace(".__init__", "")
        )
        if _is_forwarding_module(tree, policy.compat_forwarding.forwarding_target_prefixes):
            action = (
                f"replace `{legacy_module}` with `{targets[0]}`"
                if len(targets) == 1
                else f"replace `{legacy_module}` with one of {', '.join(f'`{item}`' for item in targets)}"
            )
            status = "forwarding-only"
        elif relative_path in allowlist:
            action = (
                f"review `{legacy_module}` manually before moving callers because it is allowlisted as non-forwarding"
            )
            status = "review-required"
        else:
            action = (
                f"review `{legacy_module}` manually because it is not a pure forwarding module"
            )
            status = "non-forwarding"
        entries.append(
            CompatibilityMigrationGuideEntry(
                legacy_module=legacy_module,
                canonical_targets=targets,
                status=status,
                migration_action=action,
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.legacy_module))


def _render_markdown(entries: tuple[CompatibilityMigrationGuideEntry, ...]) -> str:
    forwarding_count = sum(1 for entry in entries if entry.status == "forwarding-only")
    review_count = sum(1 for entry in entries if entry.status == "review-required")
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
        f"- forwarding-only modules: {forwarding_count}",
        f"- review-required modules: {review_count}",
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
            "- `forwarding-only` means the compatibility module is a narrow bridge and callers should move directly to the named canonical target.",
            "- `review-required` means the module is still intentionally broader and needs explicit migration review before callers are switched.",
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
            print(f"compatibility migration guide is up to date for {len(entries)} modules")
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
