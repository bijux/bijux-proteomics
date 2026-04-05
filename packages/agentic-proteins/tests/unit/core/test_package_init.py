# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import agentic_proteins as pkg


def test_package_exports() -> None:
    assert "Report" in pkg.__all__
    assert isinstance(pkg.__version__, str)
