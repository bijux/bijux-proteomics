# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrapper for golden-path demonstration utility."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_SRC = ROOT / "packages" / "bijux-proteomics-dev" / "src"
if str(DEV_SRC) not in sys.path:
    sys.path.insert(0, str(DEV_SRC))


def main() -> None:
    from bijux_proteomics_dev.tools.golden_path_example import main as tool_main

    tool_main()


if __name__ == "__main__":
    main()
