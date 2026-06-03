# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow import (
    load_surprising_demo_manifest,
    surprising_demo_root,
)


def test_surprising_demo_assets_stay_compact_and_self_contained() -> None:
    example_root = surprising_demo_root()
    manifest = load_surprising_demo_manifest(example_root)

    asset_paths = (
        manifest.tmt_result_tsv,
        manifest.tmt_design_tsv,
        manifest.ptm_evidence_tsv,
        manifest.ptm_feature_tsv,
        manifest.ptm_proteins_fasta,
        manifest.ptm_design_tsv,
        manifest.ptm_annotation_tsv,
        manifest.biological_feature_tsv,
        manifest.biological_design_tsv,
        manifest.biological_pathway_tsv,
        manifest.targeted_result_tsv,
        manifest.targeted_design_tsv,
        manifest.targeted_discovery_claims_json,
        manifest.targeted_panel_assays_json,
    )
    resolved = tuple(example_root / relative_path for relative_path in asset_paths)

    assert example_root.name == "surprising_demo"
    assert example_root.parent.name == "examples"
    assert manifest.example_id == "surprising_demo"
    assert manifest.expected_strong_protein_id == "P11111"
    assert manifest.expected_downgraded_protein_id == "P22222"
    assert manifest.expected_ambiguous_site_key == "P11111:S17:Phospho"
    assert manifest.expected_qc_issue_candidate_id == "protein:P001"
    assert manifest.expected_validation_candidate_id == "protein:P001"
    assert all(path.exists() for path in resolved)
    assert (
        sum(len(path.read_text(encoding="utf-8").splitlines()) for path in resolved)
        < 250
    )
