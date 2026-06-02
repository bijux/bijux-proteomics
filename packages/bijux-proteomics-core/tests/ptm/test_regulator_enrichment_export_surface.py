# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm.regulator_enrichment import (
    PtmRegulatorDirection,
    PtmRegulatorEnrichmentEntry,
    PtmRegulatorEnrichmentPolicy,
    PtmRegulatorEnrichmentReport,
    PtmRegulatorEnrichmentSummary,
    PtmRegulatorKind,
    export_ptm_regulator_enrichment_summary_tsv,
    export_ptm_regulator_enrichment_tsv,
)


def test_ptm_regulator_enrichment_exports_preserve_supporting_site_ledgers(
    tmp_path: Path,
) -> None:
    report = PtmRegulatorEnrichmentReport(
        condition_a="control",
        condition_b="treated",
        policy=PtmRegulatorEnrichmentPolicy(),
        entries=(
            PtmRegulatorEnrichmentEntry(
                regulator="AKT1",
                regulator_kind=PtmRegulatorKind.KINASE,
                direction=PtmRegulatorDirection.UPREGULATED,
                supporting_site_count=2,
                supporting_sites=("P11111:S5:Phospho", "P11111:S9:Phospho"),
                regulated_site_count=2,
                annotated_regulated_site_count=2,
                background_annotated_site_count=3,
                regulator_background_site_count=2,
                expected_supporting_site_count=1.333333,
                annotation_coverage_fraction=1.0,
                enrichment_ratio=1.5,
                p_value=0.1,
                adjusted_p_value=0.1,
            ),
        ),
        summary=PtmRegulatorEnrichmentSummary(
            eligible_site_count=3,
            upregulated_site_count=2,
            downregulated_site_count=1,
            annotated_upregulated_site_count=2,
            annotated_downregulated_site_count=1,
            evaluated_regulator_count=1,
            kinase_result_count=1,
            phosphatase_result_count=0,
            enriched_regulator_count=1,
        ),
        note="synthetic report for export coverage",
    )

    summary_path = tmp_path / "ptm.regulator_enrichment.summary.tsv"
    results_path = tmp_path / "ptm.regulator_enrichment.results.tsv"

    export_ptm_regulator_enrichment_summary_tsv(
        report,
        summary_path,
    )
    export_ptm_regulator_enrichment_tsv(
        report,
        results_path,
    )

    assert summary_path.read_text().splitlines()[0] == (
        "condition_a\tcondition_b\teligible_site_count\tupregulated_site_count\t"
        "downregulated_site_count\tannotated_upregulated_site_count\t"
        "annotated_downregulated_site_count\tevaluated_regulator_count\t"
        "kinase_result_count\tphosphatase_result_count\tenriched_regulator_count"
    )
    assert (
        "AKT1\tkinase\tupregulated\t2\tP11111:S5:Phospho;P11111:S9:Phospho"
        in results_path.read_text()
    )
