# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


@dataclass(frozen=True)
class PublicPackageApiLoad:
    """One ordered public package root with its loaded exports."""

    package_name: str
    module_name: str
    export_names: tuple[str, ...]


def ordered_public_package_modules() -> tuple[tuple[str, str], ...]:
    """Return the canonical product-package root order for public smoke loading."""

    return (
        ("foundation", "bijux_proteomics_foundation"),
        ("core", "bijux_proteomics"),
        ("knowledge", "bijux_proteomics_knowledge"),
        ("intelligence", "bijux_proteomics_intelligence"),
        ("runtime", "bijux_proteomics_runtime"),
    )


def load_public_package_apis() -> tuple[PublicPackageApiLoad, ...]:
    """Import every product-package root and force all curated root exports to load."""

    loaded: list[PublicPackageApiLoad] = []
    for package_name, module_name in ordered_public_package_modules():
        module = import_module(module_name)
        export_names = tuple(getattr(module, "__all__", ()))
        for export_name in export_names:
            _ = getattr(module, export_name)
        loaded.append(
            PublicPackageApiLoad(
                package_name=package_name,
                module_name=module_name,
                export_names=export_names,
            )
        )
    return tuple(loaded)
