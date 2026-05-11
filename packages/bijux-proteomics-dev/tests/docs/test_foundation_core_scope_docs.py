from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_foundation_docs_stay_on_primitives_serialization_and_invariants() -> None:
    combined = "\n".join(
        [
            _read("docs/03-bijux-proteomics-foundation/foundation/index.md"),
            _read("docs/03-bijux-proteomics-foundation/foundation/package-overview.md"),
            _read(
                "docs/03-bijux-proteomics-foundation/foundation/ownership-boundary.md"
            ),
        ]
    )

    assert "identifiers" in combined
    assert "canonical serialization" in combined
    assert "deterministic hashing" in combined
    assert "cross-package invariants" in combined
    assert "This Package Does Not Own" in combined
    assert "recommendation posture" in combined


def test_core_docs_name_scientific_contracts_and_runtime_agnostic_law() -> None:
    combined = "\n".join(
        [
            _read("docs/04-bijux-proteomics-core/foundation/index.md"),
            _read("docs/04-bijux-proteomics-core/foundation/package-overview.md"),
            _read("docs/04-bijux-proteomics-core/foundation/ownership-boundary.md"),
        ]
    )

    assert "scientific law" in combined
    assert "runtime-agnostic workflow contracts" in combined
    assert "benchmark-acceptance" in combined
    assert "lifecycle transitions" in combined
    assert "This Package Does Not Own" in combined
