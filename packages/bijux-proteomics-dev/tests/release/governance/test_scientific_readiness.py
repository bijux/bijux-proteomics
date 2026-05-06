from __future__ import annotations

from pathlib import Path

from bijux_proteomics_knowledge.references.workflows.benchmarks import KnowledgeWorkflowFamily
from bijux_proteomics_dev.release.governance.scientific_readiness import (
    build_scientific_release_dossier,
    validate_scientific_release_dossier,
)

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())


def test_scientific_release_dossier_covers_every_benchmark_workflow_family() -> None:
    dossier = build_scientific_release_dossier(REPO_ROOT)

    assert {entry.workflow_family for entry in dossier} == set(KnowledgeWorkflowFamily)
    assert all(entry.ready for entry in dossier)
    assert all(entry.dataset_locator for entry in dossier)


def test_scientific_release_dossier_is_valid_for_current_repo() -> None:
    assert validate_scientific_release_dossier(REPO_ROOT) == ()
