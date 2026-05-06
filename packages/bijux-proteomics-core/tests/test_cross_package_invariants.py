# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import re

_AGENTIC_IMPORT_RE = re.compile(
    r"^\s*(?:from|import)\s+agentic_proteins(?:\b|\.)",
    flags=re.MULTILINE,
)


def _read(path: Path) -> str:
    return path.read_text()


def _imports_agentic_runtime(content: str) -> bool:
    return _AGENTIC_IMPORT_RE.search(content) is not None


def test_core_does_not_import_agentic_runtime_paths() -> None:
    core_root = Path("packages/bijux-proteomics-core/src/bijux_proteomics")
    for path in core_root.rglob("*.py"):
        content = _read(path)
        assert not _imports_agentic_runtime(content)


def test_core_runtime_adapter_uses_canonical_runtime_imports() -> None:
    runtime_adapter = Path(
        "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/execution/runtime_adapter.py"
    )
    content = _read(runtime_adapter)

    assert "from bijux_proteomics_runtime.runs.manager import RunManager" in content
    assert "from bijux_proteomics_runtime.runs.run_config import RunConfig" in content


def test_knowledge_does_not_depend_on_intelligence_or_lab() -> None:
    knowledge_root = Path(
        "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
    )
    for path in knowledge_root.rglob("*.py"):
        content = _read(path)
        assert "bijux_proteomics_intelligence" not in content
        assert "bijux_proteomics_lab" not in content


def test_lab_depends_on_core_and_knowledge_but_not_agentic_runtime() -> None:
    lab_root = Path("packages/bijux-proteomics-lab/src/bijux_proteomics_lab")
    for path in lab_root.rglob("*.py"):
        content = _read(path)
        assert "agentic_proteins" not in content
