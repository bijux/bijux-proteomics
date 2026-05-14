"""Check that version bumps include changelog updates."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

from bijux_proteomics_dev.security.trusted_process import run_text


def _git_executable() -> str:
    resolved = shutil.which("git")
    if resolved is None:
        raise SystemExit("git executable not found")
    return resolved


def _parse_version(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip()
        if line.strip().startswith("version ="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def _git_show(path: str) -> str | None:
    try:
        return run_text(
            [_git_executable(), "show", f"HEAD~1:{path}"],
            check=True,
            capture_output=True,
        ).stdout.strip()
    except Exception:
        return None


def run(repo_root: Path) -> int:
    pyproject = repo_root / "pyproject.toml"
    changelog = repo_root / "CHANGELOG.md"
    if not pyproject.exists():
        print("pyproject.toml missing; skipping changelog version check.")
        return 0
    current_version = _parse_version(pyproject.read_text(encoding="utf-8"))
    previous_text = _git_show("pyproject.toml")
    if not previous_text:
        return 0
    previous_version = _parse_version(previous_text)
    if not current_version or not previous_version:
        return 0
    if current_version == previous_version:
        return 0
    try:
        changed_files = run_text(
            [_git_executable(), "diff", "--name-only", "HEAD~1..HEAD"],
            check=True,
            capture_output=True,
        ).stdout.splitlines()
    except Exception:
        return 0
    if str(changelog.relative_to(repo_root)) not in changed_files:
        print(
            "Version bumped in pyproject.toml without CHANGELOG.md update.",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
