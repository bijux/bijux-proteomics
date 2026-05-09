# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import importlib
from pathlib import Path
import re

from bijux_proteomics.governance.charter import (
    DEFAULT_CORE_MODULE_AUDIT,
    CoreModuleClassification,
)

CORE_SRC_ROOT = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
COMPATIBILITY_IMPORT_RE = re.compile(
    r"^from\s+(bijux_proteomics(?:\.[a-z0-9_]+)+)\s+import\s+\*(?:\s+#.*)?$",
    flags=re.MULTILINE,
)


def _public_names(module: object) -> set[str]:
    export_names = getattr(module, "__all__", None)
    if export_names is not None:
        return set(export_names)
    return {
        name
        for name in vars(module)
        if not name.startswith("_") and name != "annotations"
    }


def _wrapper_targets() -> dict[str, str]:
    targets: dict[str, str] = {}
    for entry in DEFAULT_CORE_MODULE_AUDIT:
        if entry.classification is not CoreModuleClassification.COMPATIBILITY_EXPORT:
            continue
        content = (CORE_SRC_ROOT / entry.module_path).read_text(encoding="utf-8")
        match = COMPATIBILITY_IMPORT_RE.search(content)
        assert match is not None, entry.module_path
        targets[entry.module_path] = match.group(1)
    return targets


def _module_import_name(module_path: str) -> str:
    suffix = module_path.removesuffix(".py").replace("/", ".")
    return f"bijux_proteomics.{suffix}"


def test_remaining_core_compatibility_exports_stay_root_level() -> None:
    wrapper_paths = _wrapper_targets()

    assert wrapper_paths == {}
    assert all("/" not in path for path in wrapper_paths)


def test_remaining_core_compatibility_exports_match_canonical_symbols() -> None:
    for wrapper_path, target_import_name in _wrapper_targets().items():
        wrapper_module = importlib.import_module(_module_import_name(wrapper_path))
        target_module = importlib.import_module(target_import_name)

        wrapper_names = _public_names(wrapper_module)
        target_names = _public_names(target_module)

        assert wrapper_names == target_names
        for name in target_names:
            assert getattr(wrapper_module, name) is getattr(target_module, name)
