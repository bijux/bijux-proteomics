# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.providers.environment import (
    ProviderCapabilityEntry,
    ProviderCapabilityState,
    build_provider_capability_registry,
)


def test_build_provider_capability_registry_sorts_entries_by_type_and_id() -> None:
    registry = build_provider_capability_registry(
        (
            ProviderCapabilityEntry(
                provider_id="remote-llm",
                provider_type="model",
                capabilities=("ranking", "summarization"),
                state=ProviderCapabilityState.ADVISORY,
                note="research-only endpoint",
            ),
            ProviderCapabilityEntry(
                provider_id="local-docker",
                provider_type="tool",
                capabilities=("container_exec",),
                state=ProviderCapabilityState.PRODUCTION,
                note="validated on CI runners",
            ),
        )
    )

    assert registry.entries[0].provider_type == "model"
    assert registry.entries[1].state is ProviderCapabilityState.PRODUCTION
