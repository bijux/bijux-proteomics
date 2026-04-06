# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Gate for pip-audit results.

Reads a pip-audit JSON report, filters out ignored vulnerability IDs (and aliases),
prints a concise, deterministic summary, and exits non-zero when problems remain.

Environment variables:
  PIPA_JSON             Path to pip-audit JSON (default: artifacts_pages/security/pip-audit.json)
  SECURITY_IGNORE_IDS   Space-separated list of IDs to ignore (e.g., "CVE-2023-1234 GHSA-xxxx")
  SECURITY_STRICT       "1" to fail when report is missing/unreadable or vulns remain; else soft-pass
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_SRC = ROOT / "packages" / "bijux-proteomics-dev" / "src"
if str(DEV_SRC) not in sys.path:
    sys.path.insert(0, str(DEV_SRC))


def main() -> None:
    from bijux_proteomics_dev.security.pip_audit_gate import main as gate_main

    gate_main()


if __name__ == "__main__":
    main()
