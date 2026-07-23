from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
from enum import StrEnum
import io
from pathlib import Path
from typing import TypeAlias

from bijux_proteomics_dev.quality.architecture.scanner import (
    import_references,
    iter_python_files,
    parse_python_module,
)
from bijux_proteomics_dev.release.governance.compatibility_ledger import (
    build_ledger,
)

__all__ = [
    "AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH",
    "AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH",
    "AgenticCompatibilityInventoryEntry",
    "AgenticCompatibilityInventoryIssue",
    "AgenticModuleClassification",
    "build_agentic_compatibility_inventory",
    "run",
    "validate_agentic_compatibility_inventory",
]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for compat inventory")


REPO_ROOT = _repo_root()
_WrapperFunctionNode: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef
MODULE_ROOT = REPO_ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"
AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-compatibility-inventory.csv"
)
AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "09-bijux-proteomics-runtime"
    / "migration-ledger"
    / "agentic-proteins-compatibility-inventory.md"
)

_CANONICAL_IMPORT_PREFIXES = (
    "bijux_proteomics",
    "bijux_proteomics_foundation",
    "bijux_proteomics_intelligence",
    "bijux_proteomics_knowledge",
    "bijux_proteomics_lab",
    "bijux_proteomics_runtime",
)
_COMPAT_IMPORT_PREFIX = "agentic_proteins"
_OWNER_BY_IMPORT_ROOT = {
    "bijux_proteomics": "bijux-proteomics-core",
    "bijux_proteomics_foundation": "bijux-proteomics-foundation",
    "bijux_proteomics_intelligence": "bijux-proteomics-intelligence",
    "bijux_proteomics_knowledge": "bijux-proteomics-knowledge",
    "bijux_proteomics_lab": "bijux-proteomics-lab",
    "bijux_proteomics_runtime": "bijux-proteomics-runtime",
}
_FORBIDDEN_COMPAT_OWNER_PACKAGES = frozenset(
    {
        "bijux-proteomics-foundation",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    }
)


class AgenticModuleClassification(StrEnum):
    """Compatibility-layer posture for one source module."""

    CANONICAL = "canonical"
    DEAD = "dead"
    DUPLICATE = "duplicate"
    WRAPPER = "wrapper"


@dataclass(frozen=True)
class AgenticCompatibilityInventoryEntry:
    """One inventory row for a compatibility-layer source module."""

    module_path: str
    import_path: str
    classification: AgenticModuleClassification
    owner_package: str
    canonical_targets: tuple[str, ...]
    migration_action: str


@dataclass(frozen=True)
class AgenticCompatibilityInventoryIssue:
    """One release-blocking issue in the compatibility inventory."""

    code: str
    detail: str


def _module_import_path(module_path: str) -> str:
    return "agentic_proteins." + module_path.removesuffix(".py").replace(
        "/", "."
    ).replace(".__init__", "")


def _canonical_targets(tree: ast.Module) -> tuple[str, ...]:
    targets = {
        name
        for name in import_references(tree)
        if any(
            name == prefix or name.startswith(f"{prefix}.")
            for prefix in _CANONICAL_IMPORT_PREFIXES
        )
    }
    return tuple(sorted(targets))


def _compat_targets(tree: ast.Module) -> tuple[str, ...]:
    targets = {
        name
        for name in import_references(tree)
        if name == _COMPAT_IMPORT_PREFIX or name.startswith(f"{_COMPAT_IMPORT_PREFIX}.")
    }
    return tuple(sorted(targets))


def _local_definition_names(tree: ast.Module) -> tuple[str, ...]:
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "__getattr__" and _is_wrapper_function(node):
                continue
            names.append(node.name)
            continue
        if isinstance(node, ast.ClassDef):
            names.append(node.name)
    return tuple(names)


def _inferred_owner_package(
    canonical_targets: tuple[str, ...],
    fallback_owner_package: str,
) -> str:
    if not canonical_targets:
        return fallback_owner_package
    owner_packages = {
        _OWNER_BY_IMPORT_ROOT[target.split(".", 1)[0]]
        for target in canonical_targets
        if target.split(".", 1)[0] in _OWNER_BY_IMPORT_ROOT
    }
    if len(owner_packages) == 1:
        return next(iter(owner_packages))
    return fallback_owner_package


def _is_docstring_expr(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_alias_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Attribute):
        return _is_alias_expr(node.value)
    return bool(isinstance(node, ast.Constant))


def _is_all_assignment(node: ast.Assign) -> bool:
    if not any(
        isinstance(target, ast.Name) and target.id == "__all__"
        for target in node.targets
    ):
        return False
    return isinstance(node.value, (ast.List, ast.Tuple))


def _is_top_level_alias_assignment(node: ast.Assign) -> bool:
    if _is_all_assignment(node):
        return True
    if not all(isinstance(target, ast.Name) for target in node.targets):
        return False
    return _is_alias_expr(node.value)


def _is_wrapper_call_expr(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(
        node.func, (ast.Name, ast.Attribute)
    )


def _is_wrapper_assign(node: ast.Assign) -> bool:
    if not all(
        isinstance(target, (ast.Name, ast.Attribute)) for target in node.targets
    ):
        return False
    return _is_alias_expr(node.value) or _is_wrapper_call_expr(node.value)


def _is_wrapper_try(node: ast.Try) -> bool:
    if node.orelse or node.finalbody:
        return False

    def _statements_are_wrapper_safe(statements: list[ast.stmt]) -> bool:
        for statement in statements:
            if isinstance(statement, ast.Assign):
                if _is_wrapper_assign(statement):
                    continue
                return False
            return False
        return True

    if not _statements_are_wrapper_safe(node.body):
        return False
    return all(_statements_are_wrapper_safe(handler.body) for handler in node.handlers)


def _is_type_checking_guard(node: ast.If) -> bool:
    if not isinstance(node.test, ast.Name) or node.test.id != "TYPE_CHECKING":
        return False
    if node.orelse:
        return False
    return all(
        isinstance(statement, (ast.Import, ast.ImportFrom)) for statement in node.body
    )


def _is_wrapper_function(node: _WrapperFunctionNode) -> bool:
    statements = list(node.body)
    if statements and _is_docstring_expr(statements[0]):
        statements = statements[1:]
    if not statements:
        return True
    for statement in statements:
        if isinstance(statement, ast.Assign):
            if not _is_wrapper_assign(statement):
                return False
            continue
        if isinstance(statement, ast.Expr):
            if not _is_wrapper_call_expr(statement.value):
                return False
            continue
        if isinstance(statement, ast.Return):
            if statement.value is None:
                continue
            if _is_alias_expr(statement.value) or _is_wrapper_call_expr(
                statement.value
            ):
                continue
            return False
        return False
    return True


def _is_dead_module(tree: ast.Module) -> bool:
    statements = []
    for node in tree.body:
        if _is_docstring_expr(node):
            continue
        if (
            isinstance(node, ast.Assign)
            and _is_all_assignment(node)
            and isinstance(node.value, (ast.List, ast.Tuple))
            and not node.value.elts
        ):
            continue
        statements.append(node)
    return not statements


def _is_wrapper_module(tree: ast.Module) -> bool:
    for node in tree.body:
        if _is_docstring_expr(node):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.If):
            if _is_type_checking_guard(node):
                continue
            return False
        if isinstance(node, ast.Assign):
            if _is_top_level_alias_assignment(node):
                continue
            return False
        if isinstance(node, ast.Try):
            if _is_wrapper_try(node):
                continue
            return False
        if isinstance(node, ast.FunctionDef):
            if _is_wrapper_function(node):
                continue
            return False
        return False
    return True


def _classification_for(tree: ast.Module) -> AgenticModuleClassification:
    if _is_dead_module(tree):
        return AgenticModuleClassification.DEAD
    if _is_wrapper_module(tree):
        return AgenticModuleClassification.WRAPPER
    if _canonical_targets(tree):
        return AgenticModuleClassification.DUPLICATE
    return AgenticModuleClassification.CANONICAL


def _migration_action(
    entry: AgenticCompatibilityInventoryEntry,
) -> str:
    if entry.classification is AgenticModuleClassification.DEAD:
        return f"delete `{entry.import_path}` after confirming no callers remain"
    if entry.canonical_targets:
        if len(entry.canonical_targets) == 1:
            return (
                f"replace `{entry.import_path}` with "
                f"`{entry.canonical_targets[0]}` and retire the compat import"
            )
        targets = ", ".join(f"`{target}`" for target in entry.canonical_targets)
        return f"replace `{entry.import_path}` with one of {targets} based on the live owner"
    return (
        f"review `{entry.import_path}` before removal because the live canonical target "
        "is not explicit in direct imports"
    )


def build_agentic_compatibility_inventory(
    repo_root: Path,
) -> tuple[AgenticCompatibilityInventoryEntry, ...]:
    """Build the checked compatibility inventory for every agentic module."""

    owner_by_module = {row.module_path: row.owner_package for row in build_ledger()}
    entries: list[AgenticCompatibilityInventoryEntry] = []
    for path in iter_python_files(MODULE_ROOT):
        module_path = path.relative_to(MODULE_ROOT).as_posix()
        tree = parse_python_module(path).tree
        classification = _classification_for(tree)
        canonical_targets = _canonical_targets(tree)
        fallback_owner_package = owner_by_module.get(
            module_path, "agentic-proteins-compat"
        )
        entry = AgenticCompatibilityInventoryEntry(
            module_path=module_path,
            import_path=_module_import_path(module_path),
            classification=classification,
            owner_package=_inferred_owner_package(
                canonical_targets,
                fallback_owner_package=fallback_owner_package,
            ),
            canonical_targets=canonical_targets,
            migration_action="",
        )
        entries.append(
            AgenticCompatibilityInventoryEntry(
                module_path=entry.module_path,
                import_path=entry.import_path,
                classification=entry.classification,
                owner_package=entry.owner_package,
                canonical_targets=entry.canonical_targets,
                migration_action=_migration_action(entry),
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.module_path))


def validate_agentic_compatibility_inventory(
    repo_root: Path,
) -> tuple[AgenticCompatibilityInventoryIssue, ...]:
    """Validate that the compatibility layer is wrapper-only or dead."""

    issues: list[AgenticCompatibilityInventoryIssue] = []
    for entry in build_agentic_compatibility_inventory(repo_root):
        tree = parse_python_module(MODULE_ROOT / entry.module_path).tree
        if entry.classification in {
            AgenticModuleClassification.CANONICAL,
            AgenticModuleClassification.DUPLICATE,
        }:
            issues.append(
                AgenticCompatibilityInventoryIssue(
                    code="non-wrapper-compat-module",
                    detail=(
                        f"{entry.module_path} is classified as {entry.classification.value} "
                        "instead of wrapper or dead"
                    ),
                )
            )
        if (
            entry.classification is AgenticModuleClassification.WRAPPER
            and not entry.canonical_targets
            and not entry.module_path.endswith("/__init__.py")
            and entry.module_path != "__init__.py"
        ):
            issues.append(
                AgenticCompatibilityInventoryIssue(
                    code="wrapper-without-canonical-target",
                    detail=(
                        f"{entry.module_path} is wrapper-only but does not name a canonical "
                        "target import"
                    ),
                )
            )
        if entry.owner_package in _FORBIDDEN_COMPAT_OWNER_PACKAGES:
            issues.append(
                AgenticCompatibilityInventoryIssue(
                    code="compat-owner-family-not-allowed",
                    detail=(
                        f"{entry.module_path} still resolves to forbidden bridge owner "
                        f"{entry.owner_package}"
                    ),
                )
            )
        compat_targets = _compat_targets(tree)
        if compat_targets:
            issues.append(
                AgenticCompatibilityInventoryIssue(
                    code="compat-import-hop",
                    detail=(
                        f"{entry.module_path} still imports compatibility modules "
                        f"instead of canonical owners: {', '.join(compat_targets)}"
                    ),
                )
            )
        local_definitions = _local_definition_names(tree)
        if local_definitions:
            issues.append(
                AgenticCompatibilityInventoryIssue(
                    code="compat-local-definition",
                    detail=(
                        f"{entry.module_path} still defines local compatibility logic: "
                        f"{', '.join(local_definitions)}"
                    ),
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _csv_text(entries: tuple[AgenticCompatibilityInventoryEntry, ...]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "module_path",
            "import_path",
            "classification",
            "owner_package",
            "canonical_targets",
            "migration_action",
        ]
    )
    for entry in entries:
        writer.writerow(
            [
                entry.module_path,
                entry.import_path,
                entry.classification.value,
                entry.owner_package,
                ";".join(entry.canonical_targets),
                entry.migration_action,
            ]
        )
    return buffer.getvalue()


def _summary_text(entries: tuple[AgenticCompatibilityInventoryEntry, ...]) -> str:
    counts: dict[AgenticModuleClassification, int] = dict.fromkeys(
        AgenticModuleClassification, 0
    )
    owner_counts: dict[str, int] = {}
    compat_import_hops = 0
    local_definition_count = 0
    for entry in entries:
        counts[entry.classification] += 1
        owner_counts[entry.owner_package] = owner_counts.get(entry.owner_package, 0) + 1
        tree = parse_python_module(MODULE_ROOT / entry.module_path).tree
        if _compat_targets(tree):
            compat_import_hops += 1
        if _local_definition_names(tree):
            local_definition_count += 1

    lines = [
        "---",
        "title: Agentic Compatibility Inventory",
        "audience: maintainer",
        "type: reference",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        "last_reviewed: 2026-05-05",
        "---",
        "",
        "# agentic-proteins Compatibility Inventory",
        "",
        (
            "`agentic-proteins` remains in this repository as an explicit compatibility family. "
            "Its modules are allowed to be wrappers or dead ends only. Any remaining "
            "canonical or duplicate logic is release-blocking."
        ),
        "",
        "## Current Counts",
        "",
        f"- total modules: {len(entries)}",
    ]
    for classification in AgenticModuleClassification:
        lines.append(f"- `{classification.value}`: {counts[classification]}")
    lines.extend(
        [
            "",
            "## Owner Distribution",
            "",
        ]
    )
    for owner_package, count in sorted(
        owner_counts.items(), key=lambda item: (-item[1], item[0])
    ):
        lines.append(f"- `{owner_package}`: {count}")
    lines.extend(
        [
            "",
            "## Forbidden Owner Families",
            "",
        ]
    )
    for owner_package in sorted(_FORBIDDEN_COMPAT_OWNER_PACKAGES):
        lines.append(f"- `{owner_package}`: {owner_counts.get(owner_package, 0)}")
    lines.extend(
        [
            "",
            "## Release Rule",
            "",
            "- `wrapper` means the module is only preserving an old import or patch seam while delegating live behavior to a canonical package.",
            "- `dead` means the module no longer carries meaningful behavior and can be removed once callers disappear.",
            "- `canonical` or `duplicate` are not allowed to survive in the compatibility family at release time.",
            "- foundation, knowledge, and lab ownership are not allowed to survive in the compatibility family at release time.",
            f"- direct compat-to-compat import hops remaining: {compat_import_hops}",
            f"- wrapper modules with local definitions remaining: {local_definition_count}",
            "",
            "## First Proof Check",
            "",
            f"- `{AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.relative_to(REPO_ROOT).as_posix()}`",
            f"- `{AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.relative_to(REPO_ROOT).as_posix()}`",
            "- `packages/bijux-proteomics-dev/tests/quality/architecture/test_agentic_compatibility_inventory.py`",
            "",
        ]
    )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[AgenticCompatibilityInventoryEntry, ...]) -> bool:
    if not AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.exists():
        return False
    if not AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.exists():
        return False
    return AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    ) == _csv_text(entries).replace(
        "\r\n", "\n"
    ) and AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.read_text(
        encoding="utf-8"
    ) == _summary_text(entries)


def run(check: bool = False) -> int:
    entries = build_agentic_compatibility_inventory(REPO_ROOT)
    issues = validate_agentic_compatibility_inventory(REPO_ROOT)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(entries):
            print(
                f"agentic compatibility inventory is up to date for {len(entries)} modules"
            )
            return 0
        print("agentic compatibility inventory is stale; regenerate it")
        return 1
    AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.write_text(
        _csv_text(entries),
        encoding="utf-8",
        newline="",
    )
    AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.write_text(
        _summary_text(entries),
        encoding="utf-8",
    )
    print(f"generated agentic compatibility inventory for {len(entries)} modules")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the agentic compatibility inventory."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the compatibility inventory is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
