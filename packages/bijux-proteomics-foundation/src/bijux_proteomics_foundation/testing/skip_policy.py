# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared skip-policy helpers for package test suites."""

from __future__ import annotations

from enum import StrEnum
import importlib
from types import ModuleType
from typing import NoReturn

__all__ = [
    "SkipCategory",
    "format_skip_reason",
    "import_or_skip",
    "skip_test",
    "validate_skip_reason",
]

_FORBIDDEN_REASON_PHRASES = frozenset({"not ready"})


class SkipCategory(StrEnum):
    """Allowed high-level reasons for skipping package tests."""

    OPTIONAL_DEPENDENCY = "optional_dependency"
    PROVIDER_REQUIREMENT = "provider_requirement"
    HARDWARE_REQUIREMENT = "hardware_requirement"
    CHECKOUT_FIXTURE = "checkout_fixture"


def validate_skip_reason(reason: str) -> str:
    """Return one normalized skip reason or raise on hidden placeholders."""

    normalized = " ".join(reason.split())
    if not normalized:
        raise ValueError("skip reason must not be empty")
    folded = normalized.lower().replace("-", " ").replace("_", " ")
    if folded in _FORBIDDEN_REASON_PHRASES:
        raise ValueError(
            "skip reason must explain the real blocker instead of saying only "
            "'not ready'"
        )
    return normalized


def format_skip_reason(*, category: SkipCategory, reason: str) -> str:
    """Compose one durable skip message with explicit category and detail."""

    return f"{category.value}: {validate_skip_reason(reason)}"


def skip_test(
    *,
    category: SkipCategory,
    reason: str,
    allow_module_level: bool = False,
) -> NoReturn:
    """Skip one test with explicit category and validated reason text."""

    import pytest

    pytest.skip(
        format_skip_reason(category=category, reason=reason),
        allow_module_level=allow_module_level,
    )


def import_or_skip(
    module_name: str,
    *,
    category: SkipCategory,
    reason: str,
) -> ModuleType:
    """Import one optional module or skip with explicit policy metadata."""

    validated_reason = format_skip_reason(category=category, reason=reason)
    try:
        return importlib.import_module(module_name)
    except ImportError:
        skip_test(
            category=category,
            reason=validated_reason.split(": ", 1)[1],
            allow_module_level=True,
        )
