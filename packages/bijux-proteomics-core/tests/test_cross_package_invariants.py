# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text()


def test_core_only_reaches_agentic_runtime_through_runtime_adapter() -> None:
    core_root = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
    for path in core_root.rglob("*.py"):
        content = _read(path)
        if path.name == "runtime_adapter.py":
            assert "agentic_proteins" in content
            continue
        assert "agentic_proteins" not in content


def test_knowledge_does_not_depend_on_intelligence_or_lab() -> None:
    knowledge_root = Path("packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge")
    for path in knowledge_root.rglob("*.py"):
        content = _read(path)
        assert "bijux_proteomics_intelligence" not in content
        assert "bijux_proteomics_lab" not in content


def test_lab_depends_on_core_and_knowledge_but_not_agentic_runtime() -> None:
    lab_root = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")
    for path in lab_root.rglob("*.py"):
        content = _read(path)
        assert "agentic_proteins" not in content
