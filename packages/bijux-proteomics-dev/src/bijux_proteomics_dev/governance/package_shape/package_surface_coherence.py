from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.dependencies.package_dependency_dossiers import (
    build_package_dependency_dossier_report,
)
from bijux_proteomics_dev.governance.package_shape.package_tree_dossiers import (
    build_package_tree_dossier_report,
)
from bijux_proteomics_dev.governance.package_shape.public_surfaces import (
    default_public_surface_contracts,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_SURFACE_COHERENCE_PATH",
    "PackageSurfaceCoherenceEntry",
    "PackageSurfaceCoherenceReport",
    "build_package_surface_coherence_report",
    "run",
    "validate_package_surface_coherence",
]


PACKAGE_SURFACE_COHERENCE_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-surface-coherence.toml"
)

_PRODUCT_PACKAGE_DOCS_PATHS = {
    "bijux-proteomics-foundation": Path(
        "docs/03-bijux-proteomics-foundation/this-package-does-not-own.md"
    ),
    "bijux-proteomics-core": Path(
        "docs/04-bijux-proteomics-core/this-package-does-not-own.md"
    ),
    "bijux-proteomics-intelligence": Path(
        "docs/05-bijux-proteomics-intelligence/this-package-does-not-own.md"
    ),
    "bijux-proteomics-knowledge": Path(
        "docs/06-bijux-proteomics-knowledge/this-package-does-not-own.md"
    ),
    "bijux-proteomics-lab": Path(
        "docs/07-bijux-proteomics-lab/this-package-does-not-own.md"
    ),
    "bijux-proteomics-runtime": Path(
        "docs/09-bijux-proteomics-runtime/this-package-does-not-own.md"
    ),
}


@dataclass(frozen=True)
class PackageSurfaceCoherenceEntry:
    """One product package with its checked docs, import, and boundary surface."""

    distribution_name: str
    import_root: str
    docs_path: str
    public_surface_names: tuple[str, ...]
    allowed_outbound_edges: tuple[str, ...]
    excluded_responsibilities: tuple[str, ...]


@dataclass(frozen=True)
class PackageSurfaceCoherenceReport:
    """Checked contract tying package docs to public imports and boundaries."""

    entries: tuple[PackageSurfaceCoherenceEntry, ...]


def _public_surface_names() -> dict[str, tuple[str, ...]]:
    by_package: dict[str, tuple[str, ...]] = {}
    for contract in default_public_surface_contracts():
        if contract.distribution_name not in _PRODUCT_PACKAGE_DOCS_PATHS:
            continue
        public_names = contract.supported_attributes + tuple(
            module_name.rsplit(".", 1)[-1] for module_name in contract.supported_modules
        )
        by_package[contract.distribution_name] = public_names
    return by_package


def build_package_surface_coherence_report() -> PackageSurfaceCoherenceReport:
    """Build the product-package scope coherence report."""

    by_dependency = {
        entry.distribution_name: entry
        for entry in build_package_dependency_dossier_report().entries
    }
    by_tree = {
        entry.distribution_name: entry
        for entry in build_package_tree_dossier_report().entries
    }
    by_public = _public_surface_names()
    entries = tuple(
        PackageSurfaceCoherenceEntry(
            distribution_name=distribution_name,
            import_root=by_tree[distribution_name].import_root,
            docs_path=docs_path.as_posix(),
            public_surface_names=by_public[distribution_name],
            allowed_outbound_edges=by_dependency[
                distribution_name
            ].allowed_outbound_edges,
            excluded_responsibilities=by_tree[
                distribution_name
            ].excluded_responsibilities,
        )
        for distribution_name, docs_path in _PRODUCT_PACKAGE_DOCS_PATHS.items()
    )
    return PackageSurfaceCoherenceReport(entries=entries)


def validate_package_surface_coherence(
    report: PackageSurfaceCoherenceReport | None = None,
) -> tuple[str, ...]:
    """Fail when package scope docs drift away from imports or boundaries."""

    report = report or build_package_surface_coherence_report()
    failures: list[str] = []
    for entry in report.entries:
        path = REPO_ROOT / entry.docs_path
        if not path.exists():
            failures.append(f"missing package scope page: {entry.docs_path}")
            continue
        text = path.read_text(encoding="utf-8")
        expected_bits = [
            "# This Package Does Not Own",
            f"Package: `{entry.distribution_name}`",
            f"Import root: `{entry.import_root}`",
            "## Allowed Package Dependencies",
            "## Supported Package-Root Imports",
            "## Excluded Responsibilities",
        ]
        expected_bits.extend(f"`{name}`" for name in entry.public_surface_names)
        expected_bits.extend(f"`{name}`" for name in entry.allowed_outbound_edges)
        expected_bits.extend(entry.excluded_responsibilities)
        missing = [bit for bit in expected_bits if bit not in text]
        if missing:
            failures.append(
                f"{entry.docs_path} drifted from package scope contract: {', '.join(missing)}"
            )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageSurfaceCoherenceReport) -> str:
    lines = [
        "# Generated package surface coherence report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_surface_coherence",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'import_root = "{entry.import_root}"',
                f'docs_path = "{entry.docs_path}"',
                f"public_surface_names = [{_render_tuple(entry.public_surface_names)}]",
                f"allowed_outbound_edges = [{_render_tuple(entry.allowed_outbound_edges)}]",
                (
                    "excluded_responsibilities = "
                    f"[{_render_tuple(entry.excluded_responsibilities)}]"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageSurfaceCoherenceReport) -> bool:
    if not PACKAGE_SURFACE_COHERENCE_PATH.exists():
        return False
    return PACKAGE_SURFACE_COHERENCE_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_surface_coherence_report()
    failures = validate_package_surface_coherence(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package surface coherence report is up to date")
            return 0
        print("package surface coherence report is stale; regenerate it")
        return 1
    PACKAGE_SURFACE_COHERENCE_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package surface coherence report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package surface coherence report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package surface coherence report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
