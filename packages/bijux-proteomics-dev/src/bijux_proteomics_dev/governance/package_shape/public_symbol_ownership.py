from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
from pathlib import Path

__all__ = [
    "CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH",
    "CanonicalPublicRoot",
    "PublicSymbolOwnershipEntry",
    "PublicSymbolOwnershipIssue",
    "build_public_symbol_ownership",
    "run",
    "validate_public_symbol_ownership",
]


@dataclass(frozen=True)
class CanonicalPublicRoot:
    """One canonical package root that owns public root exports."""

    distribution_name: str
    import_root: str


@dataclass(frozen=True)
class PublicSymbolOwnershipEntry:
    """One canonical package-root symbol ownership row."""

    symbol_name: str
    owner_distribution_name: str
    owner_import_root: str


@dataclass(frozen=True)
class PublicSymbolOwnershipIssue:
    """One issue in the canonical package-root symbol map."""

    code: str
    detail: str


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for public symbol ownership")


REPO_ROOT = _repo_root()
CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "public-root-symbol-owners.toml"
)


def canonical_public_roots() -> tuple[CanonicalPublicRoot, ...]:
    """Return the canonical publishable package roots."""

    return (
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-foundation",
            import_root="bijux_proteomics_foundation",
        ),
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-core",
            import_root="bijux_proteomics",
        ),
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-runtime",
            import_root="bijux_proteomics_runtime",
        ),
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-intelligence",
            import_root="bijux_proteomics_intelligence",
        ),
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-knowledge",
            import_root="bijux_proteomics_knowledge",
        ),
        CanonicalPublicRoot(
            distribution_name="bijux-proteomics-lab",
            import_root="bijux_proteomics_lab",
        ),
    )


def build_public_symbol_ownership() -> tuple[PublicSymbolOwnershipEntry, ...]:
    """Build the machine-readable canonical package-root symbol map."""

    entries: list[PublicSymbolOwnershipEntry] = []
    for root in canonical_public_roots():
        module = importlib.import_module(root.import_root)
        for symbol_name in getattr(module, "__all__", ()):
            entries.append(
                PublicSymbolOwnershipEntry(
                    symbol_name=symbol_name,
                    owner_distribution_name=root.distribution_name,
                    owner_import_root=root.import_root,
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.symbol_name, entry.owner_distribution_name),
        )
    )


def validate_public_symbol_ownership() -> tuple[PublicSymbolOwnershipIssue, ...]:
    """Validate that each canonical root symbol has exactly one owner package."""

    issues: list[PublicSymbolOwnershipIssue] = []
    owners_by_symbol: dict[str, list[str]] = {}
    entries = build_public_symbol_ownership()

    if not entries:
        issues.append(
            PublicSymbolOwnershipIssue(
                code="empty-public-symbol-map",
                detail="canonical package-root symbol ownership map is empty",
            )
        )
        return tuple(issues)

    for entry in entries:
        owners_by_symbol.setdefault(entry.symbol_name, []).append(
            entry.owner_distribution_name
        )

    for symbol_name, owners in sorted(owners_by_symbol.items()):
        if len(owners) <= 1:
            continue
        issues.append(
            PublicSymbolOwnershipIssue(
                code="duplicate-canonical-root-export",
                detail=(
                    f"canonical root symbol {symbol_name!r} is exported by multiple "
                    f"packages: {owners}"
                ),
            )
        )

    return tuple(issues)


def _toml_text(entries: tuple[PublicSymbolOwnershipEntry, ...]) -> str:
    lines = [
        "# Generated canonical package-root public symbol ownership map.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.public_symbol_ownership",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                "[[symbol]]",
                f'name = "{entry.symbol_name}"',
                f'owner_distribution_name = "{entry.owner_distribution_name}"',
                f'owner_import_root = "{entry.owner_import_root}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[PublicSymbolOwnershipEntry, ...]) -> bool:
    if not CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH.exists():
        return False
    return CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(entries)


def run(check: bool = False) -> int:
    entries = build_public_symbol_ownership()
    issues = validate_public_symbol_ownership()
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(entries):
            print(
                f"canonical public symbol ownership map is up to date for {len(entries)} symbols"
            )
            return 0
        print("canonical public symbol ownership map is stale; regenerate it")
        return 1
    CANONICAL_PUBLIC_SYMBOL_OWNERSHIP_PATH.write_text(
        _toml_text(entries),
        encoding="utf-8",
    )
    print(f"generated canonical public symbol ownership map for {len(entries)} symbols")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the canonical package-root public symbol ownership map."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the ownership map is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
