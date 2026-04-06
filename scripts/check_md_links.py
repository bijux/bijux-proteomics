# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_SRC = ROOT / "packages" / "bijux-proteomics-dev" / "src"
if str(DEV_SRC) not in sys.path:
    sys.path.insert(0, str(DEV_SRC))


def main() -> int:
    from bijux_proteomics_dev.docs.markdown_links import run

    return run(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
