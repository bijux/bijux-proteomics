# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Upstream regulator inference ownership and governed export surface."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.interpretation.public_api import (
    InterpretationFacadeOwner,
    build_lazy_export_index,
    facade_owner_modules,
    resolve_public_export,
    module_directory,
)

_REGULATOR_INFERENCE_FACADE_OWNERS: tuple[InterpretationFacadeOwner, ...] = (
    InterpretationFacadeOwner(
        owner_module=(
            "bijux_proteomics.interpretation.regulator_inference.evidence_import"
        ),
        rationale="regulator evidence import ownership",
    ),
    InterpretationFacadeOwner(
        owner_module="bijux_proteomics.interpretation.regulator_inference.models",
        rationale="regulator inference model ownership",
    ),
    InterpretationFacadeOwner(
        owner_module="bijux_proteomics.interpretation.regulator_inference.rendering",
        rationale="regulator inference rendering ownership",
    ),
    InterpretationFacadeOwner(
        owner_module=(
            "bijux_proteomics.interpretation.regulator_inference.site_signal_input"
        ),
        rationale="regulator site signal ownership",
    ),
    InterpretationFacadeOwner(
        owner_module="bijux_proteomics.interpretation.regulator_inference.inference",
        rationale="regulator inference analysis ownership",
    ),
)

__all__, _REGULATOR_INFERENCE_EXPORT_INDEX = build_lazy_export_index(
    facade_owner_modules(_REGULATOR_INFERENCE_FACADE_OWNERS),
    collision_policy="prefer_first_owner",
)


def __getattr__(name: str) -> Any:
    return resolve_public_export(
        __name__,
        globals(),
        _REGULATOR_INFERENCE_EXPORT_INDEX,
        name,
    )


def __dir__() -> list[str]:
    return module_directory(globals(), __all__)
