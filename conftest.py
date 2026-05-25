# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent

for source_root in reversed(sorted((REPO_ROOT / "packages").glob("*/src"))):
    source_path = str(source_root)
    if source_path not in sys.path:
        sys.path.insert(0, source_path)
