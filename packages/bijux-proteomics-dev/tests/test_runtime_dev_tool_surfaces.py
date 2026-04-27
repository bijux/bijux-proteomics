from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-dev" / "src" / "bijux_proteomics_dev" / "tools"
)


def _tool_text(name: str) -> str:
    return (TOOLS_ROOT / name).read_text(encoding="utf-8")


def test_golden_path_example_uses_canonical_biology_imports() -> None:
    text = _tool_text("golden_path_example.py")
    assert "from agentic_proteins" not in text
    assert "from bijux_proteomics.biology import (" in text
    assert "from bijux_proteomics.biology.protein_agent import " in text


def test_visualize_invariants_uses_canonical_biology_imports() -> None:
    text = _tool_text("visualize_invariants.py")
    assert "from agentic_proteins" not in text
    assert "from bijux_proteomics.biology import (" in text
    assert "from bijux_proteomics.biology.protein_agent import " in text


def test_minimal_repro_example_uses_canonical_biology_imports() -> None:
    text = _tool_text("mre_agentic_protein.py")
    assert "from agentic_proteins" not in text
    assert "from bijux_proteomics.biology.pathway import (" in text
    assert "from bijux_proteomics.biology.protein_agent import (" in text
    assert "from bijux_proteomics.biology.signals import " in text
