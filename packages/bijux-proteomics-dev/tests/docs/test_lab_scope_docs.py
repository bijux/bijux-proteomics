from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_lab_docs_name_assay_consequence_burden_controls_and_outcomes() -> None:
    combined = "\n".join(
        [
            _read("docs/07-bijux-proteomics-lab/foundation/index.md"),
            _read("docs/07-bijux-proteomics-lab/foundation/package-overview.md"),
            _read("docs/07-bijux-proteomics-lab/foundation/ownership-boundary.md"),
        ]
    )

    assert "assay consequence" in combined
    assert "control demands" in combined
    assert "queue or material burden" in combined
    assert "observed outcomes" in combined
    assert "This Package Does Not Own" in combined
