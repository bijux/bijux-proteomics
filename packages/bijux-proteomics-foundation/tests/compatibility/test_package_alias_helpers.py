# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import sys
from types import ModuleType
from typing import cast

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_foundation._package_aliases import (
    alias_package_version,
    canonical_module_getattr,
    dispatch_alias_entrypoint,
)


def test_package_alias_helpers_forward_canonical_root_attributes() -> None:
    assert alias_package_version("definitely-missing-package") == "0.3.6"
    assert (
        canonical_module_getattr("bijux_proteomics_foundation", "DocumentSchema")
        is DocumentSchema
    )


def test_package_alias_helpers_delegate_cli_entrypoints() -> None:
    class _FakeCli:
        def __init__(self) -> None:
            self.calls: list[tuple[list[str] | None, str, bool]] = []

        def main(
            self,
            *,
            args: list[str] | None,
            prog_name: str,
            standalone_mode: bool,
        ) -> int:
            self.calls.append((args, prog_name, standalone_mode))
            return 17

    class _FakeCliModule(ModuleType):
        cli: _FakeCli

    module_name = "_bijux_package_alias_test_cli"
    fake_module = cast(_FakeCliModule, ModuleType(module_name))
    fake_module.cli = _FakeCli()
    sys.modules[module_name] = fake_module
    try:
        assert (
            dispatch_alias_entrypoint(
                canonical_module=module_name,
                attribute_name="cli",
                prog_name="proteomics",
                argv=("scan", "--demo"),
            )
            == 17
        )
        assert fake_module.cli.calls == [
            (["scan", "--demo"], "proteomics", False),
        ]
    finally:
        sys.modules.pop(module_name, None)
