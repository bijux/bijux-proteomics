# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Thin compatibility helpers for install and import alias packages."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from importlib import import_module, metadata
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
import sys
from types import ModuleType
from typing import Any, cast

__all__ = [
    "alias_package_version",
    "canonical_module_dir",
    "canonical_module_getattr",
    "dispatch_alias_entrypoint",
    "install_import_aliases",
]


def alias_package_version(
    distribution_name: str,
    *,
    fallback: str = "0.3.6",
) -> str:
    """Return installed version metadata for a thin alias distribution."""

    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return fallback


def canonical_module_getattr(canonical_package: str, name: str) -> Any:
    """Resolve one attribute from the canonical owner package."""

    return getattr(import_module(canonical_package), name)


def canonical_module_dir(
    module_globals: Mapping[str, object],
    canonical_package: str,
) -> list[str]:
    """Expose canonical package names in interactive discovery for an alias root."""

    return sorted(set(module_globals) | set(dir(import_module(canonical_package))))


class _ImportAliasLoader(Loader):
    """Load the canonical module under a thin alias-package submodule name."""

    def __init__(self, alias_name: str, canonical_name: str) -> None:
        self._alias_name = alias_name
        self._canonical_name = canonical_name

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        """Instantiate the canonical module for the alias import."""

        module = import_module(self._canonical_name)
        sys.modules[self._alias_name] = module
        return module

    def exec_module(self, module: ModuleType) -> None:
        """Register the canonical module under the alias import name."""

        sys.modules.setdefault(self._alias_name, module)


class _ImportAliasFinder(MetaPathFinder):
    """Resolve alias-package submodules through one canonical owner package."""

    def __init__(
        self,
        *,
        alias_package: str,
        canonical_package: str,
        local_submodules: Collection[str],
    ) -> None:
        self.alias_package = alias_package
        self.canonical_package = canonical_package
        self.local_submodules = frozenset(local_submodules)
        self._alias_prefix = f"{alias_package}."

    def find_spec(
        self,
        fullname: str,
        path: object | None = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Return a loader spec that redirects alias submodules to canonical ones."""

        del path, target
        if not fullname.startswith(self._alias_prefix):
            return None
        module_suffix = fullname.removeprefix(self._alias_prefix)
        if module_suffix.partition(".")[0] in self.local_submodules:
            return None
        canonical_name = f"{self.canonical_package}.{module_suffix}"
        canonical_spec = find_spec(canonical_name)
        if canonical_spec is None:
            return None
        alias_spec = ModuleSpec(
            name=fullname,
            loader=_ImportAliasLoader(fullname, canonical_name),
            origin=canonical_spec.origin,
            is_package=canonical_spec.submodule_search_locations is not None,
        )
        if canonical_spec.submodule_search_locations is not None:
            alias_spec.submodule_search_locations = list(
                canonical_spec.submodule_search_locations
            )
        return alias_spec


def install_import_aliases(
    *,
    alias_package: str,
    canonical_package: str,
    local_submodules: Collection[str],
) -> None:
    """Install one import finder that maps alias-package submodules to canonical ones."""

    for finder in sys.meta_path:
        if not isinstance(finder, _ImportAliasFinder):
            continue
        if (
            finder.alias_package == alias_package
            and finder.canonical_package == canonical_package
        ):
            return
    sys.meta_path.insert(
        0,
        _ImportAliasFinder(
            alias_package=alias_package,
            canonical_package=canonical_package,
            local_submodules=local_submodules,
        ),
    )


def dispatch_alias_entrypoint(
    *,
    canonical_module: str,
    attribute_name: str,
    prog_name: str,
    argv: Sequence[str] | None = None,
) -> int:
    """Run a canonical command entrypoint under an alias package command name."""

    cli_object = getattr(import_module(canonical_module), attribute_name)
    return cast(
        int,
        cli_object.main(
            args=list(argv) if argv is not None else None,
            prog_name=prog_name,
            standalone_mode=False,
        ),
    )
