# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agentic_proteins.providers import factory
from agentic_proteins.providers.errors import PredictionError


def test_provider_requirements_openprotein_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENPROTEIN_USER", raising=False)
    monkeypatch.delenv("OPENPROTEIN_PASSWORD", raising=False)

    def _find_spec(name: str):
        return None if name == "openprotein" else SimpleNamespace()

    monkeypatch.setattr(factory.util, "find_spec", _find_spec)
    errors = factory.provider_requirements("api_openprotein_esmfold")
    assert "missing_env:OPENPROTEIN_USER" in errors
    assert "missing_env:OPENPROTEIN_PASSWORD" in errors
    assert "missing_dependency:openprotein-python" in errors


def test_provider_requirements_rosettafold_missing_weights_and_docker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory.util, "find_spec", lambda _name: SimpleNamespace())
    monkeypatch.setattr(factory.os.path, "exists", lambda _path: False)
    monkeypatch.setattr(factory.shutil, "which", lambda _name: None)

    errors = factory.provider_requirements("local_rosettafold")
    assert any(item.startswith("missing_weights:") for item in errors)
    assert "missing_dependency:docker" in errors


def test_require_module_raises_prediction_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory.util, "find_spec", lambda _name: None)
    with pytest.raises(PredictionError, match="Missing dependency"):
        factory._require_module("missing", "pip install missing")
