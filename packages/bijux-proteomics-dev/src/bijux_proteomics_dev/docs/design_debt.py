"""Repository design debt ledger policy checks."""

from __future__ import annotations

from pathlib import Path
import sys


def run(repo_root: Path) -> int:
    path = repo_root / "docs/bijux-proteomics/operations/change-management.md"
    if not path.exists():
        print(
            "Missing design debt ledger: "
            "docs/bijux-proteomics/operations/change-management.md",
            file=sys.stderr,
        )
        return 1
    items: list[str] = []
    in_ledger = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "## Design Debt Ledger":
            in_ledger = True
            continue
        if in_ledger and stripped.startswith("## "):
            break
        if in_ledger and stripped.startswith("- "):
            items.append(stripped)
    if len(items) > 10:
        print("Design debt ledger exceeds 10 items.", file=sys.stderr)
        return 1
    for item in items:
        if "why:" not in item or "exit:" not in item:
            print(
                "Design debt items must include why: and exit: fields.", file=sys.stderr
            )
            return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
