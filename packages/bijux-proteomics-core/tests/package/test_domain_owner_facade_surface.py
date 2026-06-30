# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
_DOMAIN_INIT = _PYTHON_ROOT / "domain" / "__init__.py"


def test_internal_modules_import_domain_owner_modules_directly() -> None:
    violations: list[str] = []

    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        if path == _DOMAIN_INIT:
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if isinstance(node, ast.ImportFrom):
                if node.module == "bijux_proteomics.domain":
                    violations.append(
                        f"{path.relative_to(_PYTHON_ROOT)} imports the domain root facade instead of an owner module"
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "bijux_proteomics.domain":
                        violations.append(
                            f"{path.relative_to(_PYTHON_ROOT)} imports the domain root facade instead of an owner module"
                        )

    assert not violations, "\n".join(violations)
