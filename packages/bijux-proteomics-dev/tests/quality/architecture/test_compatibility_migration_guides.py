from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.compatibility_migration_guides import (
    GUIDE_PATH,
    build_compatibility_migration_guide,
    run,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_compatibility_migration_guide_generator_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_compatibility_migration_guide_covers_agentic_runtime_bridge() -> None:
    entries = build_compatibility_migration_guide(REPO_ROOT)
    by_legacy_module = {entry.legacy_module: entry for entry in entries}

    assert len(entries) >= 100
    assert by_legacy_module["agentic_proteins.report.render"].status == "wrapper"
    assert by_legacy_module["agentic_proteins.api.app"].canonical_targets == (
        "bijux_proteomics_runtime.api.app",
    )
    assert by_legacy_module["agentic_proteins.biology.pathway"].canonical_targets == (
        "bijux_proteomics.biology.pathway",
    )
    guide_text = GUIDE_PATH.read_text(encoding="utf-8")
    assert "agentic-proteins Canonical Migration Guide" in guide_text
    assert "wrapper modules" in guide_text
    assert "`agentic_proteins.api.app`" in guide_text
