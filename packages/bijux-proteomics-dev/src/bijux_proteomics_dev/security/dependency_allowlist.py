"""Dependency allowlist check against root pyproject dependencies."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib


def _normalize(dependency: str) -> str:
    match = re.match(r"([A-Za-z0-9_.-]+)", dependency.strip())
    return match.group(1).lower() if match else dependency.strip().lower()


def run(repo_root: Path) -> int:
    pyproject = repo_root / "pyproject.toml"
    allowlist_path = (
        repo_root / "docs/01-bijux-proteomics/operations/artifact-governance.md"
    )
    if not pyproject.exists():
        print("pyproject.toml missing.", file=sys.stderr)
        return 1
    if not allowlist_path.exists():
        print(
            "Allowlist missing: "
            "docs/01-bijux-proteomics/operations/artifact-governance.md",
            file=sys.stderr,
        )
        return 1
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    required = {_normalize(dependency) for dependency in dependencies}
    allowlist = set()
    in_allowlist = False
    for line in allowlist_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "## Dependency Allowlist":
            in_allowlist = True
            continue
        if in_allowlist and stripped.startswith("## "):
            break
        if in_allowlist and stripped.startswith("- "):
            allowlist.add(stripped[2:].strip().lower())
    missing = sorted(required - allowlist)
    if missing:
        print("Dependencies missing from allowlist:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
