from __future__ import annotations

from typing import Any, cast

import pytest

from bijux_proteomics_runtime.providers import selection as factory_module
from bijux_proteomics_runtime.providers.catalog import provider_requirements
from bijux_proteomics_runtime.providers.contracts import _time_left
from bijux_proteomics_runtime.providers.errors import PredictionError
from bijux_proteomics_runtime.providers.remote.colabfold import (
    APIColabFoldProvider,
)
from bijux_proteomics_runtime.providers.selection import _require_module


def test_provider_factory_metadata_contract() -> None:
    requirements = provider_requirements("heuristic_proxy")
    assert isinstance(requirements, list)


def test_provider_base_exports_deadline_helper() -> None:
    assert _time_left is not None


def test_provider_factory_exports_dependency_helper() -> None:
    assert _require_module is not None


def test_local_provider_install_hints_use_runtime_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory_helpers = cast(Any, factory_module)
    monkeypatch.setattr(factory_helpers.util, "find_spec", lambda _name: None)

    with pytest.raises(
        PredictionError,
        match=("bijux-proteomics-runtime\\[local-esmfold\\].*pip install torch"),
    ):
        factory_module.create_provider("local_esmfold")

    with pytest.raises(
        PredictionError,
        match=("bijux-proteomics-runtime\\[local-rosettafold\\].*pip install torch"),
    ):
        factory_module.create_provider("local_rosettafold")


def test_api_provider_install_hints_use_runtime_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory_helpers = cast(Any, factory_module)
    monkeypatch.setattr(factory_helpers.util, "find_spec", lambda _name: None)

    with pytest.raises(
        PredictionError,
        match="provider 'api_openprotein_esmfold'.*bijux-proteomics-runtime\\[api\\]",
    ):
        factory_module.create_provider("api_openprotein_esmfold")

    with pytest.raises(
        PredictionError,
        match="provider 'api_colabfold'.*bijux-proteomics-runtime\\[api\\]",
    ):
        factory_module.create_provider("api_colabfold")


def test_provider_metadata_stays_importable_when_local_optional_dependencies_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    from bijux_proteomics_runtime.providers.catalog import provider_metadata

    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "torch" or name.startswith("torch."):
            raise ModuleNotFoundError("No module named 'torch'")
        if name == "transformers" or name.startswith("transformers."):
            raise ModuleNotFoundError("No module named 'transformers'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    metadata = provider_metadata()

    assert "heuristic_proxy" in metadata
    assert "local_esmfold" not in metadata


def test_colabfold_provider_uses_runtime_user_agent() -> None:
    provider = APIColabFoldProvider()
    try:
        assert (
            provider.session.headers["User-Agent"]
            == "bijux-proteomics-runtime (+https://github.com/bijux/bijux-proteomics)"
        )
    finally:
        provider.close()
