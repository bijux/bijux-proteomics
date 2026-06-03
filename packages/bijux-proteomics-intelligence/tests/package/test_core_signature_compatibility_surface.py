# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from importlib import import_module
import inspect
import json
from pathlib import Path
from typing import Any


def _fixture_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "compatibility"
        / "core_public_signature_snapshots.json"
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


def test_intelligence_core_signature_snapshots_match_consumed_core_surfaces() -> None:
    expected = json.loads(_fixture_path().read_text(encoding="utf-8"))

    assert {
        symbol_path: _build_signature_snapshot(symbol_path) for symbol_path in expected
    } == expected
