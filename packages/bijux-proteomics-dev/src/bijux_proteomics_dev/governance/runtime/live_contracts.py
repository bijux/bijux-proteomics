"""Live runtime OpenAPI contract checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from bijux_proteomics_runtime.api import AppConfig, create_app

Schema = dict[str, Any]


def _as_schema(value: object) -> Schema:
    return value if isinstance(value, dict) else {}


def _load_yaml(path: Path) -> Schema:
    return _as_schema(yaml.safe_load(path.read_text(encoding="utf-8")))


def _load_json(path: Path) -> Schema:
    return _as_schema(json.loads(path.read_text(encoding="utf-8")))


def _canonicalize(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))
        }
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def build_runtime_openapi(repo_root: Path) -> Schema:
    """Build the live runtime OpenAPI schema from the canonical app."""
    app = create_app(AppConfig(base_dir=repo_root, docs_enabled=True))
    return _as_schema(app.openapi())


def validate_runtime_live_contract(repo_root: Path) -> list[str]:
    """Validate that the live runtime app matches the checked-in API contracts."""
    runtime_root = repo_root / "apis" / "bijux-proteomics-runtime" / "v1"
    compat_root = repo_root / "apis" / "agentic-proteins" / "v1"
    schema_yaml = runtime_root / "schema.yaml"
    pinned_json = runtime_root / "pinned_openapi.json"
    failures: list[str] = []
    live = _canonicalize(build_runtime_openapi(repo_root))

    if not schema_yaml.exists():
        failures.append("runtime api contract missing schema.yaml")
    elif _canonicalize(_load_yaml(schema_yaml)) != live:
        failures.append("runtime schema.yaml drifted from the live runtime app")

    if not pinned_json.exists():
        failures.append("runtime api contract missing pinned_openapi.json")
    elif _canonicalize(_load_json(pinned_json)) != live:
        failures.append("runtime pinned_openapi.json drifted from the live runtime app")

    for filename in ("schema.yaml", "pinned_openapi.json", "schema.hash"):
        runtime_path = runtime_root / filename
        compat_path = compat_root / filename
        if (
            runtime_path.exists()
            and compat_path.exists()
            and runtime_path.read_bytes() != compat_path.read_bytes()
        ):
            failures.append(
                f"compat api contract drifted from runtime mirror: {filename}"
            )
    return failures
