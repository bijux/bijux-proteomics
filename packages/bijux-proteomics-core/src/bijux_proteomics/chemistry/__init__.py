# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Peptide chemistry, isotope-labeling, and fragment-reference surfaces."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

from bijux_proteomics.chemistry.public_api import (
    CHEMISTRY_ROOT_FACADE_OWNERS,
    bind_submodule_shadow_exports,
    build_lazy_export_index,
    facade_owner_modules,
    module_directory,
    resolve_public_export,
)

__all__, _CHEMISTRY_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(CHEMISTRY_ROOT_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


class _ChemistryFacadeModule(ModuleType):
    """Facade module that preserves owned exports over submodule shadowing."""

    def __setattr__(self, name: str, value: Any) -> None:
        owner = _CHEMISTRY_EXPORT_INDEX.get(name)
        if owner is not None and isinstance(value, ModuleType):
            owner_module, owner_export = owner
            if (
                value.__name__ == owner_module
                and name == owner_module.rsplit(".", maxsplit=1)[-1]
                and hasattr(value, owner_export)
            ):
                value = getattr(value, owner_export)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _ChemistryFacadeModule
bind_submodule_shadow_exports(__name__, globals(), _CHEMISTRY_EXPORT_INDEX)


def __getattr__(name: str) -> Any:
    return resolve_public_export(__name__, globals(), _CHEMISTRY_EXPORT_INDEX, name)


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
