# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""MS1 feature-table parsing and protein LFQ rollup for biological reports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
    parse_ms1_feature_table_chunked,
)


def _resolve_biological_ms1_feature_mapping(
    mapping: Ms1FeatureColumnMapping | None,
) -> Ms1FeatureColumnMapping:
    if mapping is not None:
        return mapping
    return Ms1FeatureColumnMapping(
        sample_id="sample_id",
        feature_id="feature_id",
        peptide="peptide",
        intensity="intensity",
        protein_refs="proteins",
        charge="charge",
        mz="mz",
        retention_time_seconds="retention_time_seconds",
        missing_reason="missing_reason",
        protein_separator=";",
    )


def _build_biological_quant_table_from_ms1_feature_input(
    input_tsv_path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None,
    aggregation_method: QuantRollupMethod,
    top_n: int,
    chunk_size_rows: int | None,
) -> LabelFreeQuantTable:
    active_mapping = _resolve_biological_ms1_feature_mapping(mapping)
    parse_report = (
        parse_ms1_feature_table_chunked(
            input_tsv_path,
            mapping=active_mapping,
            chunk_size_rows=chunk_size_rows,
        )
        if chunk_size_rows is not None
        else parse_ms1_feature_table(input_tsv_path, mapping=active_mapping)
    )
    return build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )


__all__ = [
    "_build_biological_quant_table_from_ms1_feature_input",
    "_resolve_biological_ms1_feature_mapping",
]
