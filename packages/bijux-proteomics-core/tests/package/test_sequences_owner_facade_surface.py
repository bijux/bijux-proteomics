# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_PACKAGE_INIT = _PYTHON_ROOT / "__init__.py"
_SEQUENCES_INIT = _PYTHON_ROOT / "sequences" / "__init__.py"


def test_internal_modules_import_sequence_owner_modules_directly() -> None:
    violations: list[str] = []

    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path in {_PACKAGE_INIT, _SEQUENCES_INIT}:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "bijux_proteomics.sequences"
            ):
                violations.append(
                    f"{path.relative_to(_PYTHON_ROOT)} imports the sequence root facade instead of an owner module"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "bijux_proteomics.sequences":
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports the sequence root facade instead of an owner module"
                        )

    assert not violations, "\n".join(violations)
