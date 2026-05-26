# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Private test-support helpers for public function type boundary audits."""

from __future__ import annotations

import inspect
from dataclasses import dataclass


@dataclass(frozen=True)
class PublicFunctionTypeBoundaryObservation:
    """Observed free-dict boundary state for one public function."""

    qualified_name: str
    offending_parameter_names: tuple[str, ...]
    has_offending_return_type: bool
    signature_text: str


@dataclass(frozen=True)
class PublicFunctionTypeBoundaryReport:
    """Structured report over one curated public function set."""

    function_count: int
    compliant_qualified_names: tuple[str, ...]
    violating_observations: tuple[PublicFunctionTypeBoundaryObservation, ...]


def build_public_function_type_boundary_report(
    functions: tuple[object, ...],
) -> PublicFunctionTypeBoundaryReport:
    """Detect free-dict public function boundaries unless explicitly raw JSON."""

    compliant_qualified_names: list[str] = []
    violating_observations: list[PublicFunctionTypeBoundaryObservation] = []
    for function in functions:
        signature = inspect.signature(function)
        qualified_name = _qualified_name(function)
        function_name = getattr(function, "__name__", "")
        offending_parameter_names = tuple(
            parameter.name
            for parameter in signature.parameters.values()
            if _annotation_uses_free_dict(parameter.annotation)
            and "raw_json" not in parameter.name
            and "raw_json" not in function_name
        )
        has_offending_return_type = _annotation_uses_free_dict(
            signature.return_annotation
        ) and "raw_json" not in function_name
        observation = PublicFunctionTypeBoundaryObservation(
            qualified_name=qualified_name,
            offending_parameter_names=offending_parameter_names,
            has_offending_return_type=has_offending_return_type,
            signature_text=str(signature),
        )
        if (
            not observation.offending_parameter_names
            and not observation.has_offending_return_type
        ):
            compliant_qualified_names.append(qualified_name)
            continue
        violating_observations.append(observation)
    return PublicFunctionTypeBoundaryReport(
        function_count=len(functions),
        compliant_qualified_names=tuple(compliant_qualified_names),
        violating_observations=tuple(violating_observations),
    )


def _annotation_uses_free_dict(annotation: object) -> bool:
    if annotation is inspect.Signature.empty:
        return False
    return "dict[" in str(annotation)


def _qualified_name(function: object) -> str:
    module_name = getattr(function, "__module__", "")
    qualname = getattr(function, "__qualname__", repr(function))
    return f"{module_name}.{qualname}" if module_name else str(qualname)


__all__ = [
    "PublicFunctionTypeBoundaryObservation",
    "PublicFunctionTypeBoundaryReport",
    "build_public_function_type_boundary_report",
]
