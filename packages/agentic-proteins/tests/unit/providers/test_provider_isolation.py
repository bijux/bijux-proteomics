# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import importlib.util
import pkgutil
import re
from pathlib import Path


def _provider_sources() -> list[str]:
    sources = []
    import agentic_proteins.providers as providers

    for module_info in pkgutil.walk_packages(
        providers.__path__, f"{providers.__name__}."
    ):
        spec = importlib.util.find_spec(module_info.name)
        if spec is None or spec.origin is None or not spec.origin.endswith(".py"):
            continue
        sources.append(Path(spec.origin).read_text())
    return sources


def test_providers_do_not_import_runtime_control() -> None:
    for source in _provider_sources():
        assert "agentic_proteins.runtime.control" not in source


def test_providers_do_not_write_outside_workspace() -> None:
    allowed_prefixes = ("/workspace", "/tmp", "/models")
    pattern = re.compile(r"['\"](/[^'\"]+)['\"]")
    for source in _provider_sources():
        for match in pattern.findall(source):
            if match.startswith(allowed_prefixes):
                continue
            assert False, f"Disallowed absolute path in provider: {match}"
