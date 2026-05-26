# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation.testing.public_function_docstrings import (
    build_public_function_docstring_report,
)
from bijux_proteomics_intelligence.public_api import (
    list_intelligence_root_api_entries,
)


def test_intelligence_public_functions_have_structured_docstrings() -> None:
    report = build_public_function_docstring_report(
        (list_intelligence_root_api_entries,)
    )

    assert report.function_count == 1
    assert report.violating_observations == ()
