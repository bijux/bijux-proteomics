# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import inspect

import bijux_proteomics_foundation
from bijux_proteomics_foundation.public_api import list_foundation_root_api_entries
from bijux_proteomics_foundation.testing.public_function_docstrings import (
    build_public_function_docstring_report,
)


def test_foundation_public_functions_have_structured_docstrings() -> None:
    functions = [list_foundation_root_api_entries]
    for entry in list_foundation_root_api_entries():
        exported = getattr(bijux_proteomics_foundation, entry.export_name)
        if inspect.isfunction(exported):
            functions.append(exported)

    report = build_public_function_docstring_report(tuple(functions))

    assert report.function_count == 6
    assert report.violating_observations == ()
