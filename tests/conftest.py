# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        path = Path(str(item.fspath))
        parts = path.parts
        if "tests" not in parts:
            continue
        if "integration" in parts:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in parts:
            item.add_marker(pytest.mark.e2e)
        elif "regression" in parts:
            item.add_marker(pytest.mark.regression)
        elif "real_local" in parts:
            item.add_marker(pytest.mark.real_local)
        else:
            item.add_marker(pytest.mark.unit)
