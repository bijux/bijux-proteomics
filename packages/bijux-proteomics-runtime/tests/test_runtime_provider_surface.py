from __future__ import annotations

from bijux_proteomics_runtime.providers.factory import provider_requirements


def test_provider_factory_metadata_contract() -> None:
    requirements = provider_requirements("heuristic_proxy")
    assert isinstance(requirements, list)
