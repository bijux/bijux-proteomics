# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "bijux_proteomics"

CANONICAL_REJECTED_EVIDENCE_OWNERS = {
    "workflow/pipelines/engines/diann_biological_workflow.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/engines/dda_biological_workflow.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/engines/maxquant_biological_workflow.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/engines/ptm_site_workflow.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/engines/tmt_experiment_workflow.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/advanced/advanced_diann.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        "rejected_evidence_tsv=diann_manifest.artifacts.rejected_evidence_tsv",
        "build_rejected_evidence_entries_from_table_rows(",
    ),
    "workflow/pipelines/advanced/advanced_maxquant.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/advanced/advanced_fragpipe.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/advanced/advanced_ptm.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        "rejected_evidence_tsv=workflow_manifest.artifacts.rejected_evidence_tsv",
        "manifest.artifacts.rejected_evidence_tsv",
    ),
    "workflow/pipelines/advanced/advanced_tmt.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
    "workflow/pipelines/advanced/advanced_targeted.py": (
        "rejected_evidence_tsv: str = Field(..., min_length=1)",
        'rejected_evidence_name = "rejected_evidence.tsv"',
        "render_result_rejected_evidence_tsv(",
    ),
}


def test_managed_workflow_owners_expose_canonical_rejected_evidence_artifact() -> None:
    offenders: list[str] = []

    for relative_path, required_snippets in CANONICAL_REJECTED_EVIDENCE_OWNERS.items():
        source_text = (SOURCE_ROOT / relative_path).read_text(encoding="utf-8")
        missing = [
            snippet for snippet in required_snippets if snippet not in source_text
        ]
        if missing:
            offenders.append(f"{relative_path}: missing {', '.join(missing)}")

    assert not offenders, (
        "managed workflow owners must expose canonical rejected evidence artifacts: "
        + "; ".join(offenders)
    )
