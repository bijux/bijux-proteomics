from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "CORE_SRC_ROOT",
    "SCIENTIFIC_CONCEPT_OWNERS_PATH",
    "ScientificConceptOwner",
    "ScientificConceptOwnershipIssue",
    "ScientificConceptSymbolDefinition",
    "build_scientific_concept_symbol_inventory",
    "load_scientific_concept_owners",
    "run",
    "validate_scientific_concept_ownership",
]


CORE_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-core" / "src" / "bijux_proteomics"
)
SCIENTIFIC_CONCEPT_OWNERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "scientific-concept-owners.toml"
)


@dataclass(frozen=True)
class ScientificConceptOwner:
    """One governed scientific concept owner in bijux-proteomics-core."""

    name: str
    owner_module: str
    owned_symbols: tuple[str, ...]
    allowed_facade_modules: tuple[str, ...]


@dataclass(frozen=True)
class ScientificConceptSymbolDefinition:
    """One class or function definition for a tracked scientific concept symbol."""

    concept_name: str
    symbol_name: str
    module_name: str
    symbol_kind: str


@dataclass(frozen=True)
class ScientificConceptOwnershipIssue:
    """One release-blocking scientific concept ownership issue."""

    code: str
    detail: str


def load_scientific_concept_owners(
    path: Path = SCIENTIFIC_CONCEPT_OWNERS_PATH,
) -> tuple[ScientificConceptOwner, ...]:
    """Load the governed scientific concept ownership registry."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    entries = data.get("concept", [])
    owners = [
        ScientificConceptOwner(
            name=str(entry["name"]),
            owner_module=str(entry["owner_module"]),
            owned_symbols=tuple(str(symbol) for symbol in entry["owned_symbols"]),
            allowed_facade_modules=tuple(
                str(module_name) for module_name in entry.get("allowed_facade_modules", [])
            ),
        )
        for entry in entries
    ]
    return tuple(sorted(owners, key=lambda owner: owner.name))


def _module_name_for_path(module_path: Path, *, core_src_root: Path) -> str:
    relative = module_path.relative_to(core_src_root)
    if relative.name == "__init__.py":
        parts = relative.parts[:-1]
    else:
        parts = relative.with_suffix("").parts
    return ".".join(("bijux_proteomics", *parts))


def build_scientific_concept_symbol_inventory(
    *,
    core_src_root: Path = CORE_SRC_ROOT,
    concept_owners: tuple[ScientificConceptOwner, ...] | None = None,
) -> tuple[ScientificConceptSymbolDefinition, ...]:
    """Scan the core source tree for tracked scientific concept symbol definitions."""

    owners = concept_owners or load_scientific_concept_owners()
    concept_by_symbol = {
        symbol_name: owner.name
        for owner in owners
        for symbol_name in owner.owned_symbols
    }
    tracked_symbols = set(concept_by_symbol)
    definitions: list[ScientificConceptSymbolDefinition] = []
    for path in sorted(core_src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module_name = _module_name_for_path(path, core_src_root=core_src_root)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in tracked_symbols:
                definitions.append(
                    ScientificConceptSymbolDefinition(
                        concept_name=concept_by_symbol[node.name],
                        symbol_name=node.name,
                        module_name=module_name,
                        symbol_kind="class",
                    )
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in tracked_symbols:
                definitions.append(
                    ScientificConceptSymbolDefinition(
                        concept_name=concept_by_symbol[node.name],
                        symbol_name=node.name,
                        module_name=module_name,
                        symbol_kind="function",
                    )
                )
    return tuple(
        sorted(
            definitions,
            key=lambda definition: (
                definition.concept_name,
                definition.symbol_name,
                definition.module_name,
                definition.symbol_kind,
            ),
        )
    )


def validate_scientific_concept_ownership(
    *,
    core_src_root: Path = CORE_SRC_ROOT,
    concept_owners: tuple[ScientificConceptOwner, ...] | None = None,
) -> tuple[ScientificConceptOwnershipIssue, ...]:
    """Validate that tracked scientific concept symbols have one owner definition."""

    owners = concept_owners or load_scientific_concept_owners()
    issues: list[ScientificConceptOwnershipIssue] = []
    owners_by_name = {owner.name: owner for owner in owners}
    if len(owners_by_name) != len(owners):
        issues.append(
            ScientificConceptOwnershipIssue(
                code="duplicate-scientific-concept-registry-entry",
                detail="scientific concept owner registry defines the same concept name more than once",
            )
        )
    symbol_owner_pairs = [
        (symbol_name, owner.name)
        for owner in owners
        for symbol_name in owner.owned_symbols
    ]
    owner_names_by_symbol: dict[str, list[str]] = {}
    for symbol_name, owner_name in symbol_owner_pairs:
        owner_names_by_symbol.setdefault(symbol_name, []).append(owner_name)
    for symbol_name, owner_names in sorted(owner_names_by_symbol.items()):
        if len(owner_names) == 1:
            continue
        issues.append(
            ScientificConceptOwnershipIssue(
                code="duplicate-scientific-concept-symbol-registry",
                detail=(
                    f"scientific concept symbol {symbol_name!r} is assigned to multiple "
                    f"concepts in the registry: {sorted(owner_names)}"
                ),
            )
        )

    definitions = build_scientific_concept_symbol_inventory(
        core_src_root=core_src_root,
        concept_owners=owners,
    )
    definitions_by_symbol: dict[str, list[ScientificConceptSymbolDefinition]] = {}
    for definition in definitions:
        definitions_by_symbol.setdefault(definition.symbol_name, []).append(definition)

    for owner in owners:
        allowed_modules = {owner.owner_module, *owner.allowed_facade_modules}
        for symbol_name in owner.owned_symbols:
            symbol_definitions = definitions_by_symbol.get(symbol_name, [])
            if not symbol_definitions:
                issues.append(
                    ScientificConceptOwnershipIssue(
                        code="missing-scientific-concept-symbol",
                        detail=(
                            f"scientific concept {owner.name!r} does not define tracked "
                            f"symbol {symbol_name!r}"
                        ),
                    )
                )
                continue
            if not any(
                definition.module_name == owner.owner_module
                for definition in symbol_definitions
            ):
                issues.append(
                    ScientificConceptOwnershipIssue(
                        code="missing-scientific-concept-owner",
                        detail=(
                            f"scientific concept {owner.name!r} tracks {symbol_name!r}, "
                            f"but the owner module {owner.owner_module!r} does not define it"
                        ),
                    )
                )
            unexpected_modules = sorted(
                {
                    definition.module_name
                    for definition in symbol_definitions
                    if definition.module_name not in allowed_modules
                }
            )
            if unexpected_modules:
                issues.append(
                    ScientificConceptOwnershipIssue(
                        code="duplicate-scientific-concept-owner",
                        detail=(
                            f"scientific concept {owner.name!r} tracks {symbol_name!r}, "
                            f"but it is also defined in unexpected modules: {unexpected_modules}"
                        ),
                    )
                )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def run(check: bool = False) -> int:
    owners = load_scientific_concept_owners()
    issues = validate_scientific_concept_ownership(concept_owners=owners)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    symbol_count = sum(len(owner.owned_symbols) for owner in owners)
    if check:
        print(
            "scientific concept ownership is valid for "
            f"{len(owners)} concepts and {symbol_count} tracked symbols"
        )
        return 0
    print(
        "validated scientific concept ownership for "
        f"{len(owners)} concepts and {symbol_count} tracked symbols"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate governed scientific concept ownership in bijux-proteomics-core."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and print the governed scientific concept ownership summary.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
