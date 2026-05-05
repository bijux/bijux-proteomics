from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.foundation_root_consumers import (
    DownstreamPackage,
    REPO_ROOT,
    downstream_packages,
)

__all__ = [
    "FOUNDATION_SURFACE_CONSUMERS_PATH",
    "FoundationSurfaceConsumerEntry",
    "build_foundation_surface_consumers",
    "public_foundation_surfaces",
    "run",
]


@dataclass(frozen=True)
class PublicFoundationSurface:
    """One direct import surface that foundation intends to keep reviewable."""

    module_name: str


@dataclass(frozen=True)
class FoundationSurfaceConsumerEntry:
    """One foundation import surface and its downstream consumers."""

    module_name: str
    consumer_distributions: tuple[str, ...]
    consumer_modules: tuple[str, ...]
    imported_symbols: tuple[str, ...]


FOUNDATION_SURFACE_CONSUMERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-surface-consumers.toml"
)


def public_foundation_surfaces() -> tuple[PublicFoundationSurface, ...]:
    """Return direct import surfaces that foundation keeps stable or compatible."""

    return tuple(
        PublicFoundationSurface(module_name=module_name)
        for module_name in (
            "bijux_proteomics_foundation",
            "bijux_proteomics_foundation.documents",
            "bijux_proteomics_foundation.compatibility",
            "bijux_proteomics_foundation.serialization",
            "bijux_proteomics_foundation.identity",
            "bijux_proteomics_foundation.support",
            "bijux_proteomics_foundation.outcomes",
            "bijux_proteomics_foundation.json_models",
            "bijux_proteomics_foundation.migrations",
            "bijux_proteomics_foundation.canonicalization",
            "bijux_proteomics_foundation.hashing",
            "bijux_proteomics_foundation.ids",
            "bijux_proteomics_foundation.provenance",
            "bijux_proteomics_foundation.refusals",
            "bijux_proteomics_foundation.results",
            "bijux_proteomics_foundation.states",
        )
    )


def _src_root(package: DownstreamPackage) -> Path:
    return REPO_ROOT / "packages" / package.distribution_name / "src" / package.import_root


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
            consumer_distributions=tuple(
                sorted(distributions_by_surface[surface.module_name])
            ),
            consumer_modules=tuple(sorted(consumers_by_surface[surface.module_name])),
            imported_symbols=tuple(sorted(symbols_by_surface[surface.module_name])),
        )
        for surface in surfaces
    )


def _toml_text(entries: tuple[FoundationSurfaceConsumerEntry, ...]) -> str:
    lines = [
        "# Generated foundation surface consumer matrix.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.foundation_surface_usage",
        "",
    ]
    for entry in entries:
        distributions = ", ".join(f'"{value}"' for value in entry.consumer_distributions)
        modules = ", ".join(f'"{value}"' for value in entry.consumer_modules)
        symbols = ", ".join(f'"{value}"' for value in entry.imported_symbols)
        lines.extend(
            [
                "[[surface]]",
                f'module_name = "{entry.module_name}"',
                f"consumer_count = {len(entry.consumer_modules)}",
                f"consumer_distributions = [{distributions}]",
                f"consumer_modules = [{modules}]",
                f"imported_symbols = [{symbols}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[FoundationSurfaceConsumerEntry, ...]) -> bool:
    if not FOUNDATION_SURFACE_CONSUMERS_PATH.exists():
        return False
    return FOUNDATION_SURFACE_CONSUMERS_PATH.read_text(encoding="utf-8") == _toml_text(
        entries
    )


def run(check: bool = False) -> int:
    entries = build_foundation_surface_consumers()
    if check:
        if _is_up_to_date(entries):
            print(
                f"foundation surface consumer matrix is up to date for {len(entries)} surfaces"
            )
            return 0
        print("foundation surface consumer matrix is stale; regenerate it")
        return 1
    FOUNDATION_SURFACE_CONSUMERS_PATH.write_text(_toml_text(entries), encoding="utf-8")
    print(f"generated foundation surface consumer matrix for {len(entries)} surfaces")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation surface consumer matrix."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the consumer matrix is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
