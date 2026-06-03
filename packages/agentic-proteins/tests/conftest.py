# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import sys

import pytest

from bijux_proteomics_foundation.testing.pytest_markers import (
    apply_default_test_markers,
)

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = ROOT / "packages" / "agentic-proteins"
for path in (ROOT, PACKAGE_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    apply_default_test_markers(
        items,
        integration_dirs=(
            "agents",
            "execution",
            "integration",
            "interfaces",
            "orchestration",
            "providers",
        ),
        e2e_dirs=("e2e",),
        real_local_dirs=("local_models",),
    )
