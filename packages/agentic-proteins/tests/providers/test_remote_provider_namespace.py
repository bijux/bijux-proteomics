# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.providers import provider_metadata


def test_experimental_providers_are_namespaced() -> None:
    metadata = provider_metadata()
    experimental = [meta.name for meta in metadata.values() if meta.experimental]
    assert all(name.startswith("api_") for name in experimental)
