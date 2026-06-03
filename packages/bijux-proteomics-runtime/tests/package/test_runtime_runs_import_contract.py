# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
from pathlib import Path

from pytest import MonkeyPatch


def _intelligence_src_root() -> Path:
    return Path(__file__).resolve().parents[3] / "bijux-proteomics-intelligence" / "src"


def test_runtime_runs_import_contract_uses_local_intelligence_engine(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(_intelligence_src_root()))

    module = importlib.import_module("bijux_proteomics_runtime.runs")

    assert module.RunConfig is not None
    assert module.RunManager is not None
    assert module.build_runtime_run_config is not None


def test_runtime_root_import_contract_exposes_run_manager_with_local_intelligence(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(_intelligence_src_root()))

    module = importlib.import_module("bijux_proteomics_runtime")

    assert module.AppConfig is not None
    assert module.RunManager is not None
    assert module.cli is not None
