from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import importlib
from pathlib import Path

from bijux_proteomics_dev.api.foundation_root_consumers import (
    DownstreamPackage,
    REPO_ROOT,
    downstream_packages,
)

__all__ = [
    "FOUNDATION_COMPATIBILITY_ALIASES_PATH",
    "FOUNDATION_DEAD_EXPORTS_PATH",
    "FOUNDATION_SURFACE_CONSUMERS_PATH",
    "FoundationCompatibilityAliasEntry",
    "FoundationDeadExportEntry",
    "FoundationSurfaceConsumerEntry",
    "build_foundation_compatibility_aliases",
    "build_foundation_dead_exports",
    "build_foundation_surface_consumers",
    "public_foundation_surfaces",
    "run",
]


@dataclass(frozen=True)
class PublicFoundationSurface:
    """One foundation import surface with durable ownership metadata."""

    module_name: str
    canonical_module_name: str | None = None
    compatibility_wrapper: bool = False


@dataclass(frozen=True)
class FoundationSurfaceConsumerEntry:
    """One foundation import surface and its downstream consumers."""

    module_name: str
    exported_symbols: tuple[str, ...]
    consumer_distributions: tuple[str, ...]
    consumer_modules: tuple[str, ...]
    imported_symbols: tuple[str, ...]


@dataclass(frozen=True)
class FoundationDeadExportEntry:
    """One foundation surface and the public exports that no downstream package imports."""

    module_name: str
    exported_symbols: tuple[str, ...]
    live_symbols: tuple[str, ...]
    dead_symbols: tuple[str, ...]
    consumer_count: int


@dataclass(frozen=True)
class FoundationCompatibilityAliasEntry:
    """One compatibility wrapper and whether real downstream consumers still need it."""

    module_name: str
    canonical_module_name: str
    exported_symbols: tuple[str, ...]
    live_symbols: tuple[str, ...]
    dead_symbols: tuple[str, ...]
    consumer_distributions: tuple[str, ...]
    consumer_modules: tuple[str, ...]
    requires_alias_test: bool


FOUNDATION_SURFACE_CONSUMERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-surface-consumers.toml"
)
FOUNDATION_DEAD_EXPORTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-dead-exports.toml"
)
FOUNDATION_COMPATIBILITY_ALIASES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-compatibility-aliases.toml"
)


def public_foundation_surfaces() -> tuple[PublicFoundationSurface, ...]:
    """Return direct import surfaces that foundation keeps stable or compatible."""

    return (
        PublicFoundationSurface(module_name="bijux_proteomics_foundation"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.documents"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.compatibility"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.serialization"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.identity"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.support"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.outcomes"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.json_models"),
        PublicFoundationSurface(module_name="bijux_proteomics_foundation.migrations"),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.canonicalization",
            canonical_module_name=(
                "bijux_proteomics_foundation.serialization.canonicalization"
            ),
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.hashing",
            canonical_module_name="bijux_proteomics_foundation.serialization.hashing",
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.ids",
            canonical_module_name="bijux_proteomics_foundation.identity.identifiers",
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.provenance",
            canonical_module_name="bijux_proteomics_foundation.support.provenance",
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.refusals",
            canonical_module_name="bijux_proteomics_foundation.outcomes.refusals",
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.results",
            canonical_module_name="bijux_proteomics_foundation.outcomes.results",
            compatibility_wrapper=True,
        ),
        PublicFoundationSurface(
            module_name="bijux_proteomics_foundation.states",
            canonical_module_name="bijux_proteomics_foundation.support.states",
            compatibility_wrapper=True,
        ),
    )


def _src_root(package: DownstreamPackage) -> Path:
    return REPO_ROOT / "packages" / package.distribution_name / "src" / package.import_root


def _exported_symbols(module_name: str) -> tuple[str, ...]:
    module = importlib.import_module(module_name)
    return tuple(getattr(module, "__all__", ()))


def build_foundation_surface_consumers() -> tuple[FoundationSurfaceConsumerEntry, ...]:
    """Build a machine-readable matrix of downstream foundation surface use."""

    surfaces = public_foundation_surfaces()
    modules = {surface.module_name for surface in surfaces}
    consumers_by_surface: dict[str, set[str]] = {module_name: set() for module_name in modules}
    distributions_by_surface: dict[str, set[str]] = {
        module_name: set() for module_name in modules
    }
    symbols_by_surface: dict[str, set[str]] = {module_name: set() for module_name in modules}

    for package in downstream_packages():
        src_root = _src_root(package)
        if not src_root.exists():
            continue
        for path in src_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in modules:
                            continue
                        distributions_by_surface[alias.name].add(package.distribution_name)
                        consumers_by_surface[alias.name].add(relative_path)
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                if node.module not in modules:
                    continue
                distributions_by_surface[node.module].add(package.distribution_name)
                consumers_by_surface[node.module].add(relative_path)
                for alias in node.names:
                    symbols_by_surface[node.module].add(alias.name)

    return tuple(
        FoundationSurfaceConsumerEntry(
            module_name=surface.module_name,
            exported_symbols=_exported_symbols(surface.module_name),
            consumer_distributions=tuple(
                sorted(distributions_by_surface[surface.module_name])
            ),
            consumer_modules=tuple(sorted(consumers_by_surface[surface.module_name])),
            imported_symbols=tuple(sorted(symbols_by_surface[surface.module_name])),
        )
        for surface in surfaces
    )


def build_foundation_dead_exports() -> tuple[FoundationDeadExportEntry, ...]:
    """Report public exports that no downstream package imports directly."""

    entries = build_foundation_surface_consumers()
    return tuple(
        FoundationDeadExportEntry(
            module_name=entry.module_name,
            exported_symbols=entry.exported_symbols,
            live_symbols=tuple(
                symbol for symbol in entry.exported_symbols if symbol in entry.imported_symbols
            ),
            dead_symbols=tuple(
                symbol
                for symbol in entry.exported_symbols
                if symbol not in entry.imported_symbols
            ),
            consumer_count=len(entry.consumer_modules),
        )
        for entry in entries
    )


def build_foundation_compatibility_aliases() -> tuple[FoundationCompatibilityAliasEntry, ...]:
    """Report which compatibility wrappers still need alias coverage."""

    dead_export_by_module = {
        entry.module_name: entry for entry in build_foundation_dead_exports()
    }
    consumer_by_module = {
        entry.module_name: entry for entry in build_foundation_surface_consumers()
    }
    return tuple(
        FoundationCompatibilityAliasEntry(
            module_name=surface.module_name,
            canonical_module_name=surface.canonical_module_name or "",
            exported_symbols=dead_export_by_module[surface.module_name].exported_symbols,
            live_symbols=dead_export_by_module[surface.module_name].live_symbols,
            dead_symbols=dead_export_by_module[surface.module_name].dead_symbols,
            consumer_distributions=consumer_by_module[
                surface.module_name
            ].consumer_distributions,
            consumer_modules=consumer_by_module[surface.module_name].consumer_modules,
            requires_alias_test=bool(dead_export_by_module[surface.module_name].consumer_count),
        )
        for surface in public_foundation_surfaces()
        if surface.compatibility_wrapper
    )


def _surface_consumer_toml_text(
    entries: tuple[FoundationSurfaceConsumerEntry, ...],
) -> str:
    lines = [
        "# Generated foundation surface consumer matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_surface_usage",
        "",
    ]
    for entry in entries:
        exported = ", ".join(f'"{value}"' for value in entry.exported_symbols)
        distributions = ", ".join(f'"{value}"' for value in entry.consumer_distributions)
        modules = ", ".join(f'"{value}"' for value in entry.consumer_modules)
        symbols = ", ".join(f'"{value}"' for value in entry.imported_symbols)
        lines.extend(
            [
                "[[surface]]",
                f'module_name = "{entry.module_name}"',
                f"consumer_count = {len(entry.consumer_modules)}",
                f"exported_symbols = [{exported}]",
                f"consumer_distributions = [{distributions}]",
                f"consumer_modules = [{modules}]",
                f"imported_symbols = [{symbols}]",
                "",
            ]
        )
    return "\n".join(lines)


def _dead_export_toml_text(entries: tuple[FoundationDeadExportEntry, ...]) -> str:
    lines = [
        "# Generated foundation dead-export report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_surface_usage",
        "",
    ]
    for entry in entries:
        exported = ", ".join(f'"{value}"' for value in entry.exported_symbols)
        live = ", ".join(f'"{value}"' for value in entry.live_symbols)
        dead = ", ".join(f'"{value}"' for value in entry.dead_symbols)
        lines.extend(
            [
                "[[surface]]",
                f'module_name = "{entry.module_name}"',
                f"consumer_count = {entry.consumer_count}",
                f"exported_symbols = [{exported}]",
                f"live_symbols = [{live}]",
                f"dead_symbols = [{dead}]",
                "",
            ]
        )
    return "\n".join(lines)


def _compatibility_alias_toml_text(
    entries: tuple[FoundationCompatibilityAliasEntry, ...],
) -> str:
    lines = [
        "# Generated foundation compatibility alias report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_surface_usage",
        "",
    ]
    for entry in entries:
        exported = ", ".join(f'"{value}"' for value in entry.exported_symbols)
        live = ", ".join(f'"{value}"' for value in entry.live_symbols)
        dead = ", ".join(f'"{value}"' for value in entry.dead_symbols)
        distributions = ", ".join(f'"{value}"' for value in entry.consumer_distributions)
        modules = ", ".join(f'"{value}"' for value in entry.consumer_modules)
        lines.extend(
            [
                "[[alias]]",
                f'module_name = "{entry.module_name}"',
                f'canonical_module_name = "{entry.canonical_module_name}"',
                f"requires_alias_test = {str(entry.requires_alias_test).lower()}",
                f"exported_symbols = [{exported}]",
                f"live_symbols = [{live}]",
                f"dead_symbols = [{dead}]",
                f"consumer_distributions = [{distributions}]",
                f"consumer_modules = [{modules}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(path: Path, text: str) -> bool:
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == text


def run(check: bool = False) -> int:
    consumer_entries = build_foundation_surface_consumers()
    dead_export_entries = build_foundation_dead_exports()
    compatibility_alias_entries = build_foundation_compatibility_aliases()
    outputs = (
        (
            FOUNDATION_SURFACE_CONSUMERS_PATH,
            _surface_consumer_toml_text(consumer_entries),
            "surface consumer matrix",
        ),
        (
            FOUNDATION_DEAD_EXPORTS_PATH,
            _dead_export_toml_text(dead_export_entries),
            "dead-export report",
        ),
        (
            FOUNDATION_COMPATIBILITY_ALIASES_PATH,
            _compatibility_alias_toml_text(compatibility_alias_entries),
            "compatibility alias report",
        ),
    )
    if check:
        stale = [
            description
            for path, text, description in outputs
            if not _is_up_to_date(path, text)
        ]
        if stale:
            print(
                "foundation surface governance reports are stale: "
                + ", ".join(stale)
            )
            return 1
        print(
            "foundation surface governance reports are up to date for "
            f"{len(consumer_entries)} surfaces"
        )
        return 0
    for path, text, _ in outputs:
        path.write_text(text, encoding="utf-8")
    print(
        "generated foundation surface governance reports for "
        f"{len(consumer_entries)} surfaces and "
        f"{len(compatibility_alias_entries)} compatibility wrappers"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation surface governance reports."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if any foundation surface governance report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
