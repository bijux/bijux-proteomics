from __future__ import annotations

from typing import Any, cast

import pytest

from bijux_proteomics_runtime.providers import factory as factory_module
from bijux_proteomics_runtime.providers.errors import PredictionError
from bijux_proteomics_runtime.providers.factory import provider_requirements


def test_provider_factory_metadata_contract() -> None:
    requirements = provider_requirements("heuristic_proxy")
    assert isinstance(requirements, list)


def test_local_provider_install_hints_use_runtime_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory_helpers = cast(Any, factory_module)
    monkeypatch.setattr(factory_helpers.util, "find_spec", lambda _name: None)

    with pytest.raises(PredictionError, match="bijux-proteomics-runtime\\[local-esmfold\\]"):
        factory_module.create_provider("local_esmfold")

    with pytest.raises(
        PredictionError,
        match="bijux-proteomics-runtime\\[local-rosettafold\\]",
    ):
        factory_module.create_provider("local_rosettafold")
