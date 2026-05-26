from __future__ import annotations

import inspect
import json
from importlib import import_module
from pathlib import Path
from typing import Any


def _compatibility_fixture_path(name: str) -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "compatibility"
        / name
    )


def _load_symbol(symbol_path: str) -> Any:
    module_path, symbol_name = symbol_path.rsplit(".", 1)
    return getattr(import_module(module_path), symbol_name)


def _build_signature_snapshot(symbol_path: str) -> dict[str, object]:
    signature = inspect.signature(_load_symbol(symbol_path))
    required_parameters: list[str] = []
    required_keyword_only_parameters: list[str] = []
    for parameter in signature.parameters.values():
        if parameter.default is not inspect.Signature.empty:
            continue
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        required_parameters.append(parameter.name)
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            required_keyword_only_parameters.append(parameter.name)
    return {
        "signature": str(signature),
        "required_parameters": required_parameters,
        "required_keyword_only_parameters": required_keyword_only_parameters,
    }


def _assert_signature_snapshot_fixture_matches(name: str) -> None:
    expected = json.loads(
        _compatibility_fixture_path(name).read_text(encoding="utf-8")
    )
    assert {
        symbol_path: _build_signature_snapshot(symbol_path)
        for symbol_path in expected
    } == expected


def test_runtime_core_signature_snapshots_match_archive_and_smoke_surfaces() -> None:
    _assert_signature_snapshot_fixture_matches(
        "core_archive_signature_snapshots.json"
    )


def test_runtime_core_signature_snapshots_match_advanced_diann_surfaces() -> None:
    _assert_signature_snapshot_fixture_matches(
        "core_advanced_diann_signature_snapshots.json"
    )
