from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-runtime"


def test_runtime_docs_publish_live_charter_and_topology() -> None:
    readme = (RUNTIME_ROOT / "README.md").read_text(encoding="utf-8")
    architecture = (RUNTIME_ROOT / "docs" / "ARCHITECTURE.md").read_text(
        encoding="utf-8"
    )
    contracts = (RUNTIME_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8")

    assert "charter.py" in readme
    assert "Execution charter" in readme
    assert "charter.py" in architecture
    assert "runs/" in architecture
    assert "workflows/" in architecture
    assert "providers/" in architecture
    assert "Runtime charter entries stay backed by live modules" in contracts


def test_runtime_docs_reject_removed_topology_names() -> None:
    text = "\n".join(
        (
            (RUNTIME_ROOT / "README.md").read_text(encoding="utf-8"),
            (RUNTIME_ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            (RUNTIME_ROOT / "docs" / "CONTRACTS.md").read_text(encoding="utf-8"),
        )
    )

    assert "runtime/adapters/" not in text
    assert "registry/" not in text
    assert "validation/" not in text
    assert "api/correlation.py" not in text
    assert "api/deps.py" not in text
    assert "api/middleware.py" not in text
    assert "`runtime/context/` owns" not in text
    assert "`runtime/control/` owns orchestration" not in text
