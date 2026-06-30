# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Benchmark tests govern runtime themselves and should not use blanket test timeouts."""

    timeout_disabled = pytest.mark.timeout(0)
    for item in items:
        item.add_marker(timeout_disabled)
