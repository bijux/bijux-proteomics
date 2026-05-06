# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.pathways import (
    EnrichmentCorrectionMethod,
    build_enrichment_background_provenance,
)


def test_build_enrichment_background_provenance_captures_statistical_inputs() -> None:
    report = build_enrichment_background_provenance(
        analysis_id="enrich-1",
        universe_id="universe-reviewed-v1",
        filter_expression="q_value<=0.01 and fold_change>=1.5",
        statistical_test="fisher_exact",
        correction_method=EnrichmentCorrectionMethod.BENJAMINI_HOCHBERG,
        input_evidence_ids=("ev-3", "ev-1", "ev-3"),
        notes=("cohort=treated", "database=reactome"),
    )

    assert report.correction_method is EnrichmentCorrectionMethod.BENJAMINI_HOCHBERG
    assert report.input_evidence_ids == ("ev-1", "ev-3")
