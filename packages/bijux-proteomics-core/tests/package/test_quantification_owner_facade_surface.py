# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_PACKAGE_INIT = _PYTHON_ROOT / "__init__.py"
_QUANTIFICATION_INIT = _PYTHON_ROOT / "quantification" / "__init__.py"


def test_internal_modules_import_quantification_owner_modules_directly() -> None:
    violations: list[str] = []

    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path in {_PACKAGE_INIT, _QUANTIFICATION_INIT}:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom):
                if node.module == "bijux_proteomics.quantification":
                    violations.append(
                        f"{path.relative_to(_PYTHON_ROOT)} imports the quantification root facade instead of an owner module"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "bijux_proteomics.quantification":
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports the quantification root facade instead of an owner module"
                        )

    assert not violations, "\n".join(violations)
