"""Repository architecture documentation presence checks."""

from __future__ import annotations

from pathlib import Path
import sys

REQUIRED_DOCS = (
    "docs/01-bijux-proteomics/foundation/change-principles.md",
    "docs/01-bijux-proteomics/operations/change-management.md",
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
