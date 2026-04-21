from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.api import AppConfig, create_app


def test_runtime_api_factory_contract() -> None:
    app = create_app(AppConfig(base_dir=Path.cwd(), docs_enabled=False))
    assert app.title == "bijux-proteomics-runtime"
