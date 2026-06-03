# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared optional dependency guards for repository product packages."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from bijux_proteomics_foundation.outcomes.exceptions import (
    MissingOptionalDependencyError,
)

__all__ = [
    "import_optional_module",
    "is_missing_optional_dependency_error",
]


def is_missing_optional_dependency_error(
    error: BaseException,
    *,
    import_roots: tuple[str, ...],
) -> bool:
    """Return whether an import failure came from one governed optional root."""

    if not isinstance(error, (ImportError, ModuleNotFoundError)):
        return False
    expected_roots = {root.split(".", 1)[0] for root in import_roots}
    missing_name = getattr(error, "name", None)
    if (
        isinstance(missing_name, str)
        and missing_name
        and missing_name.split(".", 1)[0] in expected_roots
    ):
        return True
    error_text = str(error)
    return any(
        f"No module named '{root}'" in error_text
        or f'No module named "{root}"' in error_text
        for root in expected_roots
    )


def import_optional_module(
    module_name: str,
    *,
    dependency_name: str,
    feature_name: str,
    install_hint: str,
) -> Any:
    """Import one optional module or raise a stable optional-dependency error."""

    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        if not is_missing_optional_dependency_error(
            exc,
            import_roots=(module_name,),
        ):
            raise
        raise MissingOptionalDependencyError(
            dependency_name=dependency_name,
            feature_name=feature_name,
            install_hint=install_hint,
        ) from exc
