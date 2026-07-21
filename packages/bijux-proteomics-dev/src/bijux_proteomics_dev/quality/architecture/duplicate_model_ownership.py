from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import load_workspace_packages

__all__ = [
    "DUPLICATE_MODEL_OWNERSHIP_CSV_PATH",
    "DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH",
    "DuplicateModelDefinition",
    "DuplicateModelOwnershipIssue",
    "build_duplicate_model_inventory",
    "is_duplicate_model_ownership_report_up_to_date",
    "run",
    "validate_duplicate_model_ownership",
]


@dataclass(frozen=True)
class DuplicateModelDefinition:
    """One structured model definition owned by one canonical package."""

    model_name: str
    package_name: str
    module_path: str
    model_kind: str


@dataclass(frozen=True)
class DuplicateModelOwnershipIssue:
    """One release-blocking duplicate-model ownership issue."""

    code: str
    detail: str


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError(
        "Unable to resolve repository root for duplicate model ownership"
    )


REPO_ROOT = _repo_root()
DUPLICATE_MODEL_OWNERSHIP_CSV_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "foundation"
    / "duplicate-model-ownership.csv"
)
DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "01-bijux-proteomics"
    / "foundation"
    / "duplicate-model-ownership.md"
)
_IGNORED_PACKAGE_NAMES = {"agentic-proteins", "bijux-proteomics-dev"}
_TRACKED_MODEL_BASE_NAMES = frozenset({"JsonModel", "Protocol", "StrEnum", "BaseModel"})
_ALLOWED_SHARED_MODEL_OWNERS = {
    "BeliefAuditEntry": frozenset(
        {
            (
                "bijux-proteomics-core",
                "bijux_proteomics/review/belief/belief_audit.py",
            ),
            (
                "bijux-proteomics-intelligence",
                "bijux_proteomics_intelligence/belief_audit.py",
            ),
        }
    ),
    "BeliefAuditReport": frozenset(
        {
            (
                "bijux-proteomics-core",
                "bijux_proteomics/review/belief/belief_audit.py",
            ),
            (
                "bijux-proteomics-intelligence",
                "bijux_proteomics_intelligence/belief_audit.py",
            ),
        }
    ),
    "BeliefAuditSummary": frozenset(
        {
            (
                "bijux-proteomics-core",
                "bijux_proteomics/review/belief/belief_audit.py",
            ),
            (
                "bijux-proteomics-intelligence",
                "bijux_proteomics_intelligence/belief_audit.py",
            ),
        }
    ),
    "ProteinSetEnrichmentEntry": frozenset(
        {
            (
                "bijux-proteomics-core",
                "bijux_proteomics/interpretation/protein_set_enrichment.py",
            ),
            (
                "bijux-proteomics-intelligence",
                "bijux_proteomics_intelligence/interpretation/pathways.py",
            ),
        }
    ),
    "ProteinSetEnrichmentReport": frozenset(
        {
            (
                "bijux-proteomics-core",
                "bijux_proteomics/interpretation/protein_set_enrichment.py",
            ),
            (
                "bijux-proteomics-intelligence",
                "bijux_proteomics_intelligence/interpretation/pathways.py",
            ),
        }
    ),
}


def _class_base_names(node: ast.ClassDef) -> tuple[str, ...]:
    names: list[str] = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
            continue
        if isinstance(base, ast.Attribute):
            parts: list[str] = []
            current: ast.AST = base
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            names.append(".".join(reversed(parts)))
    return tuple(names)


def _tracked_model_kind(node: ast.ClassDef) -> str | None:
    base_names = _class_base_names(node)
    for name in base_names:
        stem = name.rsplit(".", 1)[-1]
        if stem in _TRACKED_MODEL_BASE_NAMES:
            return stem.lower()
    return None


def build_duplicate_model_inventory(
    repo_root: Path,
) -> tuple[DuplicateModelDefinition, ...]:
    """Build the structured-model inventory across canonical packages."""

    definitions: list[DuplicateModelDefinition] = []
    for package in load_workspace_packages(repo_root):
        if package.package_name in _IGNORED_PACKAGE_NAMES:
            continue
        for path in sorted(package.src_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            module_path = path.relative_to(package.src_dir).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                    continue
                model_kind = _tracked_model_kind(node)
                if model_kind is None:
                    continue
                definitions.append(
                    DuplicateModelDefinition(
                        model_name=node.name,
                        package_name=package.package_name,
                        module_path=module_path,
                        model_kind=model_kind,
                    )
                )
    return tuple(
        sorted(
            definitions,
            key=lambda item: (
                item.model_name,
                item.package_name,
                item.module_path,
            ),
        )
    )


def validate_duplicate_model_ownership(
    repo_root: Path,
) -> tuple[DuplicateModelOwnershipIssue, ...]:
    """Validate that tracked model names are owned by exactly one canonical package."""

    definitions = build_duplicate_model_inventory(repo_root)
    issues: list[DuplicateModelOwnershipIssue] = []
    owners_by_name: dict[str, list[DuplicateModelDefinition]] = {}
    for definition in definitions:
        owners_by_name.setdefault(definition.model_name, []).append(definition)
    for model_name, owners in sorted(owners_by_name.items()):
        package_names = sorted({owner.package_name for owner in owners})
        if len(package_names) <= 1:
            continue
        owner_keys = frozenset(
            (owner.package_name, owner.module_path) for owner in owners
        )
        if _ALLOWED_SHARED_MODEL_OWNERS.get(model_name) == owner_keys:
            continue
        rendered = ", ".join(
            f"{owner.package_name}:{owner.module_path}" for owner in owners
        )
        issues.append(
            DuplicateModelOwnershipIssue(
                code="duplicate-model-name",
                detail=(
                    f"structured model {model_name!r} is owned by multiple canonical "
                    f"packages: {rendered}"
                ),
            )
        )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _csv_text(definitions: tuple[DuplicateModelDefinition, ...]) -> str:
    lines = ["model_name,package_name,module_path,model_kind"]
    for definition in definitions:
        lines.append(
            ",".join(
                (
                    definition.model_name,
                    definition.package_name,
                    definition.module_path,
                    definition.model_kind,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _summary_text(
    definitions: tuple[DuplicateModelDefinition, ...],
    issues: tuple[DuplicateModelOwnershipIssue, ...],
) -> str:
    package_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for definition in definitions:
        package_counts[definition.package_name] = (
            package_counts.get(definition.package_name, 0) + 1
        )
        kind_counts[definition.model_kind] = (
            kind_counts.get(definition.model_kind, 0) + 1
        )

    lines = [
        "---",
        "title: Duplicate Model Ownership",
        "audience: maintainer",
        "type: reference",
        "status: canonical",
        "owner: bijux-proteomics-dev",
        "last_reviewed: 2026-07-21",
        "---",
        "",
        "# Duplicate Model Ownership",
        "",
        "This generated report inventories public structured-model definitions across "
        "the six canonical product packages. A repeated model name is a release blocker "
        "unless the exact package and module pair is an explicitly governed exception.",
        "",
        "```mermaid",
        "flowchart LR",
        '    S["canonical package sources"] --> I["AST model inventory"]',
        '    I --> N["group by model name"]',
        '    N --> E["exact governed exceptions"]',
        '    E --> V{"single canonical owner?"}',
        '    V -->|yes| C["ownership clean"]',
        '    V -->|no| B["release blocker"]',
        "```",
        "",
        "## Current Assessment",
        "",
        f"- tracked definitions: **{len(definitions)}**",
        f"- canonical packages: **{len(package_counts)}**",
        f"- unresolved ownership conflicts: **{len(issues)}**",
        f"- release posture: **{'blocked' if issues else 'clean'}**",
        "",
        "## Model Kinds",
        "",
        "| model kind | definitions |",
        "| --- | ---: |",
    ]
    for model_kind, count in sorted(kind_counts.items()):
        lines.append(f"| `{model_kind}` | {count} |")
    lines.extend(
        [
            "",
            "## Package Distribution",
            "",
            "| canonical package | definitions |",
            "| --- | ---: |",
        ]
    )
    for package_name, count in sorted(
        package_counts.items(), key=lambda item: (-item[1], item[0])
    ):
        lines.append(f"| `{package_name}` | {count} |")
    lines.extend(["", "## Blocking Conflicts", ""])
    if issues:
        lines.extend(f"- {issue.detail}" for issue in issues)
    else:
        lines.append("No unresolved duplicate ownership conflicts were detected.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A matching class name is not harmless duplication. Separate owners can diverge "
            "in validation, serialization, defaults, or meaning while callers continue to "
            "treat them as one concept. Resolve a blocker by choosing one canonical owner and "
            "migrating consumers, or by governing the exact shared owner set when duplication "
            "is intentional and semantically identical.",
            "",
            "The exception registry is exact by design: a module move invalidates an exception "
            "until maintainers re-establish that the new owner pair still represents the same "
            "contract.",
            "",
            "## Evidence And Validation",
            "",
            f"- inventory: `{DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.relative_to(REPO_ROOT).as_posix()}`",
            "- generator: `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/quality/architecture/duplicate_model_ownership.py`",
            "- validation: `packages/bijux-proteomics-dev/tests/quality/architecture/test_duplicate_model_ownership.py`",
            "",
        ]
    )
    return "\n".join(lines)


def _is_up_to_date(
    definitions: tuple[DuplicateModelDefinition, ...],
    issues: tuple[DuplicateModelOwnershipIssue, ...],
) -> bool:
    if not DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.exists():
        return False
    if not DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH.exists():
        return False
    return DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    ) == _csv_text(definitions).replace(
        "\r\n", "\n"
    ) and DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH.read_text(
        encoding="utf-8"
    ) == _summary_text(definitions, issues)


def is_duplicate_model_ownership_report_up_to_date() -> bool:
    """Return whether generated ownership artifacts match the current inventory."""
    definitions = build_duplicate_model_inventory(REPO_ROOT)
    issues = validate_duplicate_model_ownership(REPO_ROOT)
    return _is_up_to_date(definitions, issues)


def run(check: bool = False) -> int:
    definitions = build_duplicate_model_inventory(REPO_ROOT)
    issues = validate_duplicate_model_ownership(REPO_ROOT)
    if check:
        if _is_up_to_date(definitions, issues):
            print(
                f"duplicate model ownership report is up to date for {len(definitions)} definitions"
            )
        else:
            print("duplicate model ownership report is stale; regenerate it")
            return 1
    else:
        DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        DUPLICATE_MODEL_OWNERSHIP_CSV_PATH.write_text(
            _csv_text(definitions),
            encoding="utf-8",
            newline="",
        )
        DUPLICATE_MODEL_OWNERSHIP_SUMMARY_PATH.write_text(
            _summary_text(definitions, issues),
            encoding="utf-8",
        )
        print(
            f"generated duplicate model ownership report for {len(definitions)} definitions"
        )
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the duplicate model ownership report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the duplicate model ownership report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
