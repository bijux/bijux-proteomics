from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.compatibility_migration_guides import (
    GUIDE_PATH,
    build_compatibility_migration_guide,
    run,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_compatibility_migration_guide_generator_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_compatibility_migration_guide_covers_agentic_runtime_bridge() -> None:
    entries = build_compatibility_migration_guide(REPO_ROOT)
    by_legacy_module = {entry.legacy_module: entry for entry in entries}

    assert len(entries) == 117
    assert by_legacy_module["agentic_proteins.interfaces.http.app"].status == "wrapper"
    assert by_legacy_module[
        "agentic_proteins.interfaces.http.app"
    ].canonical_targets == ("bijux_proteomics_runtime.api.app",)
    assert by_legacy_module["agentic_proteins.execution.manager"].canonical_targets == (
        "bijux_proteomics_runtime.runs.manager",
    )
    assert by_legacy_module["agentic_proteins.state.context"].canonical_targets == (
        "bijux_proteomics_runtime.runs.context",
    )
    assert by_legacy_module["agentic_proteins.agents.catalog"].canonical_targets == (
        "bijux_proteomics_runtime.execution.agents.catalog",
    )
    assert by_legacy_module[
        "agentic_proteins.orchestration.manager"
    ].canonical_targets == ("bijux_proteomics_runtime.runs.manager",)
    assert by_legacy_module[
        "agentic_proteins.providers.remote.openprotein"
    ].canonical_targets == ("bijux_proteomics_runtime.providers.remote.openprotein",)
    guide_text = GUIDE_PATH.read_text(encoding="utf-8")
    assert "agentic-proteins Canonical Migration Guide" in guide_text
    assert "wrapper modules" in guide_text
    assert "`agentic_proteins.interfaces.http.app`" in guide_text
    assert "## Migration Proof" in guide_text
    assert "## Freshness Contract" in guide_text
    assert "this document should" not in guide_text.lower()
