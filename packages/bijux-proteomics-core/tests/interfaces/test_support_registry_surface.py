# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

import bijux_proteomics.interfaces.cli.support as cli_support
import bijux_proteomics.interfaces.support as support_registry

PYTHON_API_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics"
    / "interfaces"
    / "python_api"
)


def test_support_registry_exports_modules_not_symbol_soup() -> None:
    expected = (
        "biomarker_candidate_support",
        "contrast_resolution",
        "foundation",
        "identification",
        "imports",
        "interpretation",
        "io_and_dia",
        "multiplex_targeted",
        "output_protocol",
        "ptm_quantification",
        "review_sequences_study",
        "sequence_support",
        "targeted_panel_support",
        "targeted_selection_io",
        "timecourse_support",
        "validation_evidence_support",
        "workflow",
    )

    assert support_registry.__all__ == expected
    assert cli_support.__all__ == expected
    assert support_registry.output_protocol.__name__.endswith(".output_protocol")
    assert cli_support.output_protocol is support_registry.output_protocol


def test_python_api_modules_import_owned_support_submodules_directly() -> None:
    violations: list[str] = []
    for path in sorted(PYTHON_API_ROOT.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        for node in module.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module == "bijux_proteomics.interfaces.support":
                violations.append(
                    f"{path.relative_to(PYTHON_API_ROOT)} imports the root support registry"
                )
            if node.module == "bijux_proteomics.interfaces.support.targeted_panel_support":
                violations.append(
                    f"{path.relative_to(PYTHON_API_ROOT)} imports the targeted panel support facade instead of an owner module"
                )
            if node.module == "bijux_proteomics.interfaces.support.validation_evidence_support":
                violations.append(
                    f"{path.relative_to(PYTHON_API_ROOT)} imports the validation evidence support facade instead of an owner module"
                )
            if node.module == "bijux_proteomics.interfaces.support.workflow" and any(
                alias.name == "*" for alias in node.names
            ):
                violations.append(
                    f"{path.relative_to(PYTHON_API_ROOT)} still uses workflow star imports"
                )
    assert not violations, "\n".join(violations)
