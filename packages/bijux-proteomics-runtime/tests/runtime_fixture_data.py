from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def fixture_path(*parts: str) -> Path:
    """Return one runtime test fixture path."""

    return Path(__file__).resolve().parent / "fixtures" / Path(*parts)


def load_fixture(*parts: str) -> dict[str, Any]:
    """Load one JSON fixture as a dictionary."""

    payload = json.loads(fixture_path(*parts).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Fixture {'/'.join(parts)} must be a JSON object.")
    return payload
