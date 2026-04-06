"""OpenAPI drift checks for repository API contracts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _load_schema(text: str) -> dict:
    return yaml.safe_load(text) or {}


def _git_show(path: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"HEAD~1:{path}"], text=True
        )
    except Exception:
        return None


def _extract_fields(schema: dict) -> set[str]:
    fields: set[str] = set()
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    for name, payload in schemas.items():
        props = (payload or {}).get("properties", {}) or {}
        for prop in props:
            fields.add(f"{name}.{prop}")
    return fields


def run(repo_root: Path) -> int:
    schema_path = repo_root / "apis/agentic-proteins/v1/schema.yaml"
    if not schema_path.exists():
        print("OpenAPI schema missing; skipping.")
        return 0
    current_schema = _load_schema(schema_path.read_text(encoding="utf-8"))
    previous_text = _git_show("apis/agentic-proteins/v1/schema.yaml")
    if not previous_text:
        return 0
    previous_schema = _load_schema(previous_text)
    removed_fields = _extract_fields(previous_schema) - _extract_fields(current_schema)
    if not removed_fields:
        return 0
    current_version = (current_schema.get("info") or {}).get("version")
    previous_version = (previous_schema.get("info") or {}).get("version")
    if current_version == previous_version:
        print("Breaking OpenAPI change detected without version bump:", file=sys.stderr)
        for field in sorted(removed_fields):
            print(f"- removed {field}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
