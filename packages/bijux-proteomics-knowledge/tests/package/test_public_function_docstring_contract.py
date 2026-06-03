# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import inspect

from bijux_proteomics_foundation.testing.public_function_docstrings import (
    build_public_function_docstring_report,
)
import bijux_proteomics_knowledge
from bijux_proteomics_knowledge.public_api import list_knowledge_root_api_entries


def test_knowledge_public_functions_have_structured_docstrings() -> None:
    functions = [list_knowledge_root_api_entries]
    for entry in list_knowledge_root_api_entries():
        exported = getattr(bijux_proteomics_knowledge, entry.export_name)
        if inspect.isfunction(exported):
            functions.append(exported)

    report = build_public_function_docstring_report(tuple(functions))

    assert report.function_count == 20
    assert report.violating_observations == ()
