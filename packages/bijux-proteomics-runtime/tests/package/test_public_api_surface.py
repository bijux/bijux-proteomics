from __future__ import annotations

import bijux_proteomics_runtime
from bijux_proteomics_runtime.public_api import list_runtime_root_api_entries


def test_runtime_public_api_module_matches_root_exports() -> None:
    assert tuple(
        entry.export_name for entry in list_runtime_root_api_entries()
    ) == tuple(bijux_proteomics_runtime.__all__)
