# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


def test_root_md_whitelist() -> None:
    root = Path(__file__).resolve().parents[2]
    allowed = {
        "README.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
    }
    for path in root.glob("*.md"):
        assert path.name in allowed
