# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.falsifiers import (
    ClaimFalsifierEntry,
    ClaimFalsifierType,
    generate_falsifiers,
    render_claim_falsifiers_tsv,
)
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimStatus,
    ClaimType,
    EvidenceClaim,
)


def test_generate_falsifiers_emits_distinct_types_for_protein_ptm_pathway_regulator_and_biomarker_claims() -> (
    None
):
    protein = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-protein",
            target_id="protein:p11111",
            statement="protein abundance increases",
            direction="increase",
            magnitude=1.2,
            evidence_ids=["evidence-protein"],
            resolution_assays=["discovery rerun"],
            status=ClaimStatus.SUPPORTED,
        )
    )
    ptm = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-ptm",
            target_id="ptm_site:p11111:s5:phospho",
            statement="site-specific phosphorylation increases",
            direction="increase",
            magnitude=1.8,
            evidence_ids=["evidence-ptm"],
            assumptions=[
                "protein_correction_status=high_confidence_corrected",
                "mechanism_class=site_specific",
            ],
            resolution_assays=["site localization rerun"],
            status=ClaimStatus.SUPPORTED,
        )
    )
    pathway = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-pathway",
            target_id="pathway:stress_response",
            statement="stress response pathway is activated",
            direction="increase",
            magnitude=1.0,
            evidence_ids=["evidence-pathway"],
            resolution_assays=["member overlap confirmation"],
            status=ClaimStatus.SUPPORTED,
        )
    )
    regulator = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-regulator",
            target_id="regulator:kinase_a",
            statement="kinase A activity increases",
            direction="increase",
            magnitude=1.1,
            evidence_ids=["evidence-regulator"],
            resolution_assays=["substrate panel rerun"],
            status=ClaimStatus.SUPPORTED,
        )
    )
    biomarker = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-biomarker",
            target_id="biomarker:panel_alpha",
            statement="panel alpha separates responders",
            direction="increase",
            magnitude=1.4,
            evidence_ids=["evidence-biomarker"],
            resolution_assays=["independent cohort replication"],
            status=ClaimStatus.SUPPORTED,
            claim_type=ClaimType.BIOMARKER,
        )
    )

    assert protein.entries == (
        ClaimFalsifierEntry(
            claim_id="claim-protein",
            falsifier_type=ClaimFalsifierType.ORTHOGONAL_PROTEIN_QUANT_FAILURE,
            required_evidence=(
                "discovery rerun",
                "orthogonal protein rerun",
                "protein-specific peptide support audit",
                "direction reversal check",
            ),
            why_it_matters=(
                "Protein claims fall when the retained abundance direction disappears, "
                "reverses, or turns out not to be protein-specific."
            ),
        ),
    )
    assert ptm.entries[0].falsifier_type is (
        ClaimFalsifierType.SITE_LOCALIZATION_OR_CORRECTION_FAILURE
    )
    assert pathway.entries[0].falsifier_type is (
        ClaimFalsifierType.PATHWAY_MEMBER_SUPPORT_COLLAPSE
    )
    assert regulator.entries[0].falsifier_type is (
        ClaimFalsifierType.REGULATOR_SUBSTRATE_ACTIVITY_COLLAPSE
    )
    assert biomarker.entries[0].falsifier_type is (
        ClaimFalsifierType.BIOMARKER_REPLICATION_FAILURE
    )


def test_render_claim_falsifiers_tsv_preserves_required_fields() -> None:
    report = generate_falsifiers(
        EvidenceClaim(
            claim_id="claim-biomarker",
            target_id="biomarker:panel_beta",
            statement="panel beta predicts response",
            direction="increase",
            magnitude=1.3,
            evidence_ids=["evidence-biomarker"],
            resolution_assays=["independent cohort replication"],
            status=ClaimStatus.SUPPORTED,
            claim_type=ClaimType.BIOMARKER,
        )
    )

    assert render_claim_falsifiers_tsv(report.entries).splitlines()[0] == (
        "claim_id\tfalsifier_type\trequired_evidence\twhy_it_matters"
    )
