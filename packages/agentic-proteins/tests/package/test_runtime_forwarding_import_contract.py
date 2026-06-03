# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
from pathlib import Path

from pytest import MonkeyPatch


def _intelligence_src_root() -> Path:
    return Path(__file__).resolve().parents[3] / "bijux-proteomics-intelligence" / "src"


def test_agentic_runtime_forwarding_uses_local_runtime_contracts(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(_intelligence_src_root()))

    compat_module = importlib.import_module("agentic_proteins")
    runtime_module = importlib.import_module("bijux_proteomics_runtime")

    assert compat_module.AppConfig is runtime_module.AppConfig
    assert compat_module.RunManager is runtime_module.RunManager
    assert compat_module.cli is runtime_module.cli
    assert compat_module.create_app is runtime_module.create_app
