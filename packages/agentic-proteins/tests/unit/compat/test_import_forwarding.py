from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, cast

from click.testing import CliRunner

from agentic_proteins.api import AppConfig as CompatAppConfig
from agentic_proteins.api import create_app as compat_create_app
from agentic_proteins.interfaces.cli import cli as compat_cli
from bijux_proteomics_runtime.api import AppConfig as RuntimeAppConfig
from bijux_proteomics_runtime.api import create_app as runtime_create_app
from bijux_proteomics_runtime.interfaces.cli import cli as runtime_cli


def _config_payload(config: object) -> dict[str, object]:
    if is_dataclass(config):
        return cast(dict[str, object], asdict(cast(Any, config)))
    if hasattr(config, "model_dump"):
        return cast(dict[str, object], cast(Any, config).model_dump())
    if hasattr(config, "dict"):
        return cast(dict[str, object], cast(Any, config).dict())
    raise TypeError(f"Unsupported config model type: {type(config)!r}")


def test_compat_cli_import_forwards_to_runtime_symbol() -> None:
    assert compat_cli is runtime_cli


def test_compat_and_runtime_cli_help_are_equivalent() -> None:
    compat_result = CliRunner().invoke(compat_cli, ["--help"])
    runtime_result = CliRunner().invoke(runtime_cli, ["--help"])
    assert compat_result.exit_code == 0
    assert runtime_result.exit_code == 0
    assert compat_result.output == runtime_result.output


def test_compat_and_runtime_api_factory_are_equivalent() -> None:
    base_dir = Path.cwd()
    compat_config = CompatAppConfig(base_dir=base_dir, docs_enabled=False)
    runtime_config = RuntimeAppConfig(base_dir=base_dir, docs_enabled=False)
    assert _config_payload(compat_config) == _config_payload(runtime_config)

    compat_app = compat_create_app(compat_config)
    runtime_app = runtime_create_app(runtime_config)
    assert compat_app.title == runtime_app.title
    assert [getattr(route, "path", "") for route in compat_app.routes] == [
        getattr(route, "path", "") for route in runtime_app.routes
    ]
