from __future__ import annotations

from pathlib import Path

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)
CORE_README = REPO_ROOT / "packages" / "bijux-proteomics-core" / "README.md"


def test_core_readme_describes_core_as_the_scientific_heart() -> None:
    text = CORE_README.read_text(encoding="utf-8")

    assert "scientific heart of the suite" in text
    assert "runtime-agnostic scientific contracts" in text


def test_core_readme_publishes_reader_facing_example_entrypoints() -> None:
    text = CORE_README.read_text(encoding="utf-8")

    assert "build_sequence_digest_example" in text
    assert "build_glycopeptide_refusal_example" in text
    assert "build_loss_aware_search_normalization_example" in text


def test_core_readme_source_guide_points_to_live_core_modules() -> None:
    text = CORE_README.read_text(encoding="utf-8")
    expected_paths = (
        "packages/bijux-proteomics-core/src/bijux_proteomics/domain/program_spec.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/sequences/core.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/chemistry/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/identification/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/io/formats/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/io/ingestion.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/io/spectra/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/quantification/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/ptm/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/dia/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/review/__init__.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/workflow/blueprint.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/execution/runtime_adapter.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/examples.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/governance/charter.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/study/qc.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/review/protein_family_graphs.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/ptm/proteoforms.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/cli/app.py",
        "packages/bijux-proteomics-core/src/bijux_proteomics/interfaces/cli/__main__.py",
    )

    for relative_path in expected_paths:
        assert relative_path in text
        assert (REPO_ROOT / relative_path).exists()
