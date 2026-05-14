# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.independent_reruns import (
    build_workflow_independent_rerun_dossier,
    build_workflow_independent_rerun_dossier_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_independent_rerun_dossier_family_covers_all_five_flagship_workflows() -> None:
    family = build_workflow_independent_rerun_dossier_family()

    assert family.family_id == "flagship-independent-rerun-dossiers"
    assert tuple(dossier.workflow_family for dossier in family.dossiers) == (
        KnowledgeWorkflowFamily.DDA,
        KnowledgeWorkflowFamily.DIA,
        KnowledgeWorkflowFamily.LFQ,
        KnowledgeWorkflowFamily.PTM,
        KnowledgeWorkflowFamily.TARGETED,
    )


def test_dda_independent_rerun_dossier_names_cross_engine_import_surface() -> None:
    dossier = build_workflow_independent_rerun_dossier(KnowledgeWorkflowFamily.DDA)

    assert dossier.scrutiny_ready is True
    assert dossier.flagship_lane.package_id == "dda-maxquant-pipeline-corpus"
    assert dossier.companion_lane.package_id == "dda-comet-cross-engine-corpus"
    assert dossier.flagship_lane.run_mode.value == "import_only"
    assert dossier.cross_environment_drift_visible is True
    assert any(
        "dda_cross_engine_review_package/README.md" in path
        for path in dossier.companion_lane.public_package_paths
    )
    assert "cross-package challenge path" in dossier.note


def test_other_independent_rerun_dossiers_name_companion_drift_surfaces() -> None:
    dia = build_workflow_independent_rerun_dossier(KnowledgeWorkflowFamily.DIA)
    lfq = build_workflow_independent_rerun_dossier(KnowledgeWorkflowFamily.LFQ)
    ptm = build_workflow_independent_rerun_dossier(KnowledgeWorkflowFamily.PTM)
    targeted = build_workflow_independent_rerun_dossier(
        KnowledgeWorkflowFamily.TARGETED
    )

    assert dia.flagship_lane.package_id == "dia-diann-pipeline-corpus"
    assert dia.companion_lane.package_id == "dia-matrix-shift-review-corpus"
    assert dia.flagship_lane.run_mode.value == "raw_executable"
    assert "matrix" in " ".join(dia.drift_questions).lower()
    assert lfq.companion_lane.package_id == "lfq-sparse-contrast-review-corpus"
    assert "multi-cohort transfer authority" in " ".join(lfq.remaining_limits)
    assert ptm.companion_lane.package_id == "ptm-ambiguity-stress-review-corpus"
    assert "ambiguity" in " ".join(ptm.drift_questions).lower()
    assert targeted.companion_lane.package_id == "targeted-carryover-review-corpus"
    assert "vendor-parity proof" in " ".join(targeted.remaining_limits)
