# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from types import SimpleNamespace

from agentic_proteins.providers import factory


def test_provider_requirements_missing_weights(monkeypatch) -> None:
    def fake_find_spec(name: str):
        return SimpleNamespace() if name in {"torch"} else None

    monkeypatch.setattr(factory.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(factory.os.path, "exists", lambda _path: False)
    monkeypatch.setattr(factory.shutil, "which", lambda _name: "/usr/bin/docker")

    errors = factory.provider_requirements("local_rosettafold")
    assert any(e.startswith("missing_weights:") for e in errors)
