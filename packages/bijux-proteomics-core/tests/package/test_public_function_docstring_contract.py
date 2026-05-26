# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import inspect

import bijux_proteomics
from bijux_proteomics.public_api import list_core_root_api_entries
from bijux_proteomics_foundation.testing.public_function_docstrings import (
    build_public_function_docstring_report,
)


def test_core_public_functions_have_structured_docstrings() -> None:
    functions = [list_core_root_api_entries]
    for entry in list_core_root_api_entries():
        exported = getattr(bijux_proteomics, entry.export_name)
        if inspect.isfunction(exported):
            functions.append(exported)

    report = build_public_function_docstring_report(tuple(functions))

    assert report.function_count == 5
    assert report.violating_observations == ()
