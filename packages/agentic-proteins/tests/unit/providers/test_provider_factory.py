# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from agentic_proteins.providers import factory


def test_provider_requirements_missing_weights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_find_spec(name: str) -> object | None:
        return SimpleNamespace() if name in {"torch"} else None

    factory_module = cast(Any, factory)
    monkeypatch.setattr(factory_module.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(factory_module.os.path, "exists", lambda _path: False)
    monkeypatch.setattr(factory_module.shutil, "which", lambda _name: "/usr/bin/docker")

    errors = factory.provider_requirements("local_rosettafold")
    assert any(e.startswith("missing_weights:") for e in errors)
