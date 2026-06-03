from __future__ import annotations

from bijux_proteomics_dev.governance.runtime.import_graph import (
    RUNTIME_IMPORT_GRAPH_PATH,
    build_runtime_import_cycles,
    build_runtime_import_surfaces,
    run,
)


def test_runtime_import_graph_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_runtime_import_graph_locks_current_surface_edges_and_cycles() -> None:
    surfaces = build_runtime_import_surfaces()
    cycles = build_runtime_import_cycles()
    outgoing = {surface.name: surface.outgoing_surfaces for surface in surfaces}

    assert RUNTIME_IMPORT_GRAPH_PATH.exists()
    assert [cycle.surfaces for cycle in cycles] == [("state", "support")]
    assert outgoing["runs"] == (
        "execution",
        "providers",
        "state",
        "support",
    )
    assert outgoing["workflows"] == (
        "artifacts",
        "rehydrate",
        "resume",
        "runs",
        "support",
    )
