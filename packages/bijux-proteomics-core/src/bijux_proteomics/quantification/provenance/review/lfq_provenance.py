# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""LFQ provenance builders for review-grade quantification surfaces."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import (
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    build_label_free_provenance_bundle,
)
from bijux_proteomics.quantification.missingness import summarize_missing_values
from bijux_proteomics.quantification.normalization import normalize_label_free_table
from bijux_proteomics.quantification.provenance.review.models import (
    LfqFeaturePeptideProteinProvenanceReport,
)


def build_lfq_feature_peptide_protein_provenance_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.MEDIAN,
    top_n: int = 3,
) -> LfqFeaturePeptideProteinProvenanceReport:
    """Build LFQ provenance preserving feature, peptide, protein, and missingness context."""
    bundle = build_label_free_provenance_bundle(
        records,
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        top_n=top_n,
    )
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(
            peptide_table, method=normalization_method
        )
        protein_table = normalize_label_free_table(
            protein_table, method=normalization_method
        )

    peptide_missingness = summarize_missing_values(peptide_table)
    protein_missingness = summarize_missing_values(protein_table)
    return LfqFeaturePeptideProteinProvenanceReport(
        provenance_bundle=bundle,
        peptide_missingness=peptide_missingness,
        protein_missingness=protein_missingness,
        feature_entry_count=len(bundle.feature_entries),
        peptide_entry_count=len(bundle.peptide_entries),
        protein_entry_count=len(bundle.protein_entries),
        normalization_method=normalization_method,
        note=(
            "lfq provenance preserves feature-to-peptide-to-protein evidence while retaining missingness and normalization context"
        ),
    )


__all__ = ["build_lfq_feature_peptide_protein_provenance_report"]
