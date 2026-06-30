# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific artifact inventory sections for biological report HTML."""

from __future__ import annotations

from ..biological_report_artifact_path_contracts import (
    BiologicalResultReportArtifactPaths,
)


def _build_biological_scientific_artifact_sections(
    artifacts: BiologicalResultReportArtifactPaths,
) -> list[tuple[str, str | None]]:
    return [
        ("Differential proteins", artifacts.differential_tsv),
        ("Protein card summary", artifacts.protein_card_summary_tsv),
        ("Protein cards", artifacts.protein_card_tsv),
        ("Pathway cards", artifacts.pathway_card_tsv),
        (
            "Protein mechanism card summary",
            artifacts.protein_mechanism_card_summary_tsv,
        ),
        ("Protein mechanism cards", artifacts.protein_mechanism_card_tsv),
        (
            "Experiment confidence summary",
            artifacts.experiment_confidence_summary_tsv,
        ),
        (
            "Experiment confidence components",
            artifacts.experiment_confidence_components_tsv,
        ),
        ("Report section confidence", artifacts.section_confidence_tsv),
        ("Evidence-aware ranking", artifacts.evidence_aware_ranking_tsv),
        ("Claim validation summary", artifacts.claim_validation_summary_tsv),
        ("Supported biological claims", artifacts.supported_claim_tsv),
        ("Rejected biological claims", artifacts.rejected_claim_tsv),
        (
            "Biological hypothesis summary",
            artifacts.biological_hypothesis_summary_tsv,
        ),
        ("Biological hypotheses", artifacts.biological_hypothesis_tsv),
        (
            "Rejected hypothesis candidates",
            artifacts.rejected_hypothesis_candidate_tsv,
        ),
        (
            "Enrichment foreground/background summary",
            artifacts.foreground_background_summary_tsv,
        ),
        (
            "Enrichment foreground/background entries",
            artifacts.foreground_background_entry_tsv,
        ),
        (
            "Enrichment foreground/background issues",
            artifacts.foreground_background_issue_tsv,
        ),
        (
            "Regulator inference summary",
            artifacts.regulator_inference_summary_tsv,
        ),
        ("Regulator inference", artifacts.regulator_inference_tsv),
        (
            "Regulator inference unresolved targets",
            artifacts.regulator_inference_unresolved_tsv,
        ),
        (
            "Regulator evidence rejected rows",
            artifacts.regulator_evidence_rejected_tsv,
        ),
        ("Annotation summary", artifacts.annotation_summary_tsv),
        ("Annotated proteins", artifacts.annotation_tsv),
        ("Unmapped annotations", artifacts.annotation_unmapped_tsv),
    ]
