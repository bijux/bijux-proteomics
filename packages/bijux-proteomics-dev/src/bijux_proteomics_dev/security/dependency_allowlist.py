"""Enforce the root project's declared runtime dependency policy."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib
from typing import Any


POLICY_PATH = Path(
    "configs/package-governance/root-runtime-dependency-policy.toml"
)


def _normalize(dependency: str) -> str:
    match = re.match(r"([A-Za-z0-9_.-]+)", dependency.strip())
    return match.group(1).lower() if match else dependency.strip().lower()


def _load_toml(path: Path, label: str) -> dict[str, Any] | None:
    if not path.is_file():
        print(f"{label} missing: {path}", file=sys.stderr)
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        print(f"{label} unreadable: {path}: {error}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"{label} must contain a TOML table: {path}", file=sys.stderr)
        return None
    return data


def _allowed_distributions(policy: dict[str, Any], path: Path) -> set[str] | None:
    values = policy.get("allowed_distributions")
    if not isinstance(values, list) or not all(
        isinstance(value, str) and value.strip() for value in values
    ):
        print(
            f"Dependency policy must define allowed_distributions as strings: {path}",
            file=sys.stderr,
        )
        return None
    normalized = {_normalize(value) for value in values}
    if len(normalized) != len(values):
        print(
            f"Dependency policy contains duplicate normalized distributions: {path}",
            file=sys.stderr,
        )
        return None
    return normalized


def run(repo_root: Path) -> int:
    pyproject = repo_root / "pyproject.toml"
    policy_path = repo_root / POLICY_PATH
    project_data = _load_toml(pyproject, "Root project configuration")
    if project_data is None:
        return 1
    policy_data = _load_toml(policy_path, "Root runtime dependency policy")
    if policy_data is None:
        return 1
    dependencies = project_data.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(dependency, str) for dependency in dependencies
    ):
        print(
            "Root project dependencies must be a list of strings: pyproject.toml",
            file=sys.stderr,
        )
        return 1
    required = {_normalize(dependency) for dependency in dependencies}
    allowed = _allowed_distributions(policy_data, policy_path)
    if allowed is None:
        return 1
    missing = sorted(required - allowed)
    unused = sorted(allowed - required)
    if missing:
        print("Root runtime dependencies missing from policy:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
    if unused:
        print("Policy entries absent from root runtime dependencies:", file=sys.stderr)
        for item in unused:
            print(f"- {item}", file=sys.stderr)
    return int(bool(missing or unused))


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
