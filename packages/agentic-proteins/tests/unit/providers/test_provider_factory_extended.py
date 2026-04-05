# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import sys
import types

import pytest

from agentic_proteins.providers import factory as factory_module
from agentic_proteins.providers.errors import PredictionError
from agentic_proteins.providers.heuristic import HeuristicStructureProvider


def _install_module(name: str, **attrs: object) -> None:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


def test_create_provider_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module, "_require_module", lambda *_: None)
    class DummyProvider:
        def __init__(self, model: str | None = None) -> None:
            self.model = model
    modules = [
        "agentic_proteins.providers.experimental.openprotein",
        "agentic_proteins.providers.experimental.colabfold",
        "agentic_proteins.providers.local.esmfold",
        "agentic_proteins.providers.local.rosettafold",
    ]
    try:
        _install_module(
            modules[0],
            APIOpenProteinProvider=DummyProvider,
        )
        _install_module(
            modules[1],
            APIColabFoldProvider=DummyProvider,
        )
        _install_module(
            modules[2],
            LocalESMFoldProvider=DummyProvider,
        )
        _install_module(
            modules[3],
            LocalRoseTTAFoldProvider=DummyProvider,
        )
        assert isinstance(
            factory_module.create_provider("heuristic_proxy"),
            HeuristicStructureProvider,
        )
        assert factory_module.create_provider("api_openprotein_esmfold").model == "esmfold"
        assert isinstance(factory_module.create_provider("api_colabfold"), DummyProvider)
        assert isinstance(factory_module.create_provider("local_esmfold"), DummyProvider)
        assert isinstance(factory_module.create_provider("local_rosettafold"), DummyProvider)
        with pytest.raises(PredictionError, match="Unknown provider"):
            factory_module.create_provider("missing")
    finally:
        for name in modules:
            sys.modules.pop(name, None)


def test_provider_requirements(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module.util, "find_spec", lambda _: None)
    monkeypatch.setattr(factory_module.os, "getenv", lambda *_: "")
    monkeypatch.setattr(factory_module.os.path, "exists", lambda *_: False)
    monkeypatch.setattr(factory_module.shutil, "which", lambda *_: None)
    errors = factory_module.provider_requirements("local_rosettafold")
    assert "missing_dependency:torch" in errors
    assert any(item.startswith("missing_weights:") for item in errors)
    assert "missing_dependency:docker" in errors
    errors = factory_module.provider_requirements("api_openprotein_esmfold")
    assert "missing_env:OPENPROTEIN_USER" in errors
    assert "missing_env:OPENPROTEIN_PASSWORD" in errors
    assert "missing_dependency:openprotein-python" in errors
