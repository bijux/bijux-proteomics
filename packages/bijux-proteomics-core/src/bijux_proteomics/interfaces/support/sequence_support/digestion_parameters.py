# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Digestion and modification parameter resolution for sequence workflows."""

from __future__ import annotations

from ..imports import *  # noqa: F401,F403


def _resolve_cli_protease_rule(
    *,
    protease: str,
    custom_protease: str | None,
    custom_protease_name: str,
) -> tuple[ProteaseRule, str | None]:
    specification = custom_protease.strip() if custom_protease is not None else ""
    if not specification:
        rule = resolve_protease_rule(protease)
        return rule, None
    if protease != "trypsin":
        raise ValueError(
            "custom protease rules cannot be combined with a second built-in protease name"
        )
    rule = resolve_protease_rule(
        custom_specification=specification,
        custom_name=custom_protease_name,
    )
    return rule, specification


def _resolve_cli_theoretical_digest_modifications(
    *,
    static_modifications: tuple[str, ...],
    variable_modifications: tuple[str, ...],
    registry_path: Path | None,
    allow_isotopic_labels: bool,
    allowed_label_families: tuple[str, ...],
) -> tuple[
    ModificationRegistryDocument | None,
    tuple[StaticModification, ...],
    tuple[VariableModification, ...],
    IsotopicLabelingPolicy | None,
]:
    registry = (
        load_modification_registry(registry_path) if registry_path is not None else None
    )
    resolved_static: list[StaticModification] = []
    for token in static_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, StaticModification):
            raise ValueError(
                f"static modification {token!r} is not a static definition"
            )
        resolved_static.append(definition)
    resolved_variable: list[VariableModification] = []
    for token in variable_modifications:
        definition = get_modification(token, registry=registry)
        if not isinstance(definition, VariableModification):
            raise ValueError(
                f"variable modification {token!r} is not a variable definition"
            )
        resolved_variable.append(definition)
    labeling_policy = (
        IsotopicLabelingPolicy(
            allow_isotopic_labels=allow_isotopic_labels,
            allowed_label_families=allowed_label_families,
        )
        if allow_isotopic_labels or allowed_label_families
        else None
    )
    return registry, tuple(resolved_static), tuple(resolved_variable), labeling_policy
