# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins_testsupport.paths import repo_root


def test_root_md_whitelist() -> None:
    root = repo_root()
    allowed = {
        "README.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
    }
    for path in root.glob("*.md"):
        assert path.name in allowed
