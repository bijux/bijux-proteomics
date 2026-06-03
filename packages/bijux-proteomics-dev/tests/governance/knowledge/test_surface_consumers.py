from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.knowledge.surface_consumers import (
    KNOWLEDGE_SURFACE_CONSUMERS_PATH,
    build_knowledge_surface_consumers,
    knowledge_surfaces,
    run,
)

pytestmark = pytest.mark.slow


def test_knowledge_surface_consumer_matrix_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_surface_consumer_matrix_records_current_owner_usage() -> None:
    entries = build_knowledge_surface_consumers()
    entry_by_module = {entry.module_name: entry for entry in entries}

    assert KNOWLEDGE_SURFACE_CONSUMERS_PATH.exists()
    assert [entry.module_name for entry in entries] == [
        surface.module_name for surface in knowledge_surfaces()
    ]
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.memory.models.evidence"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.references.workflows.benchmarks"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-lab",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.references.workflows.lookups"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.references.workflows.lookups"
        ].imported_symbols
    ) >= {
        "get_benchmark_manifest",
    }
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.references.grounding.rules"
        ].consumer_distributions
    ) == {
        "bijux-proteomics-dev",
        "bijux-proteomics-intelligence",
    }
    assert (
        "bijux_proteomics_knowledge.references.registry_queries" not in entry_by_module
    )
    assert set(
        entry_by_module[
            "bijux_proteomics_knowledge.references.workflows.briefings"
        ].consumer_distributions
    ) == {"bijux-proteomics-dev", "bijux-proteomics-intelligence"}
