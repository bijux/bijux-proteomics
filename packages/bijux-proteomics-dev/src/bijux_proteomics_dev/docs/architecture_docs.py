"""Repository architecture documentation presence checks."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_DOCS = (
    "docs/bijux-proteomics/architecture-invariants.md",
    "docs/bijux-proteomics/design-debt-ledger.md",
)


def run(repo_root: Path) -> int:
    for relative_path in REQUIRED_DOCS:
        path = repo_root / relative_path
        if not path.exists():
            print(f"Missing required document: {relative_path}", file=sys.stderr)
            return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
