# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)
from bijux_proteomics.proteoforms.assembly import (
    ProteoformPeptideEvidence,
    ProteoformPtmEvidence,
    assemble_proteoform_candidates,
)
from bijux_proteomics.proteoforms.quantification import (
    ProteoformQuantificationConfidence,
    quantify_supported_proteoforms,
    render_proteoform_quantification_tsv,
)


def test_quantify_supported_proteoforms_requires_unique_support_before_emitting_abundance() -> (
    None
):
    candidates = _assembled_candidates()
    feature_matrix = QuantMatrix(
        matrix_id="proteoform_feature_matrix",
        entity_kind=QuantEntityKind.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("shared_backbone", "modified_site", "unmodified_peptide"),
        sample_ids=("sample_a", "sample_b"),
        values=((100.0, 90.0), (40.0, None), (60.0, 55.0)),
        missing_value_states=(
            (MissingValueState.OBSERVED, MissingValueState.OBSERVED),
            (MissingValueState.OBSERVED, MissingValueState.NOT_OBSERVED),
            (MissingValueState.OBSERVED, MissingValueState.OBSERVED),
        ),
        support_counts=((1, 1), (1, 0), (1, 1)),
        row_metadata=(
            {"protein_id": "P11111", "peptide_ids": "pep_backbone"},
            {
                "protein_id": "P11111",
                "peptide_ids": "pep_modified",
                "site_ids": "P11111:S7:Phospho",
            },
            {"protein_id": "P11111", "peptide_ids": "pep_unmodified"},
        ),
    )

    report = quantify_supported_proteoforms(candidates, feature_matrix)
    rendered = render_proteoform_quantification_tsv(report)

    modified_id = next(
        entry.proteoform_id for entry in candidates if entry.required_sites
    )
    unmodified_id = next(
        entry.proteoform_id for entry in candidates if not entry.required_sites
    )
    entry_lookup = {
        (entry.proteoform_id, entry.sample_id): entry for entry in report.entries
    }

    modified_sample_a = entry_lookup[(modified_id, "sample_a")]
    modified_sample_b = entry_lookup[(modified_id, "sample_b")]
    unmodified_sample_a = entry_lookup[(unmodified_id, "sample_a")]
    unmodified_sample_b = entry_lookup[(unmodified_id, "sample_b")]

    assert modified_sample_a.abundance == 40.0
    assert modified_sample_a.unique_support_count == 1
    assert (
        modified_sample_a.quantification_confidence
        is ProteoformQuantificationConfidence.SITE_SPECIFIC_UNIQUE_SUPPORT
    )

    assert modified_sample_b.abundance is None
    assert modified_sample_b.unique_support_count == 0
    assert (
        modified_sample_b.quantification_confidence
        is ProteoformQuantificationConfidence.INSUFFICIENT_UNIQUE_SUPPORT
    )

    assert unmodified_sample_a.abundance == 60.0
    assert unmodified_sample_a.unique_support_count == 1
    assert (
        unmodified_sample_a.quantification_confidence
        is ProteoformQuantificationConfidence.PEPTIDE_SPECIFIC_UNIQUE_SUPPORT
    )

    assert unmodified_sample_b.abundance == 55.0
    assert unmodified_sample_b.unique_support_count == 1
    assert (
        unmodified_sample_b.quantification_confidence
        is ProteoformQuantificationConfidence.PEPTIDE_SPECIFIC_UNIQUE_SUPPORT
    )

    assert rendered.startswith(
        "proteoform_id\tsample_id\tabundance\tunique_support_count\tquantification_confidence\n"
    )
    assert "\t\t0\tinsufficient_unique_support\n" in rendered


def test_quantify_supported_proteoforms_withholds_shared_only_signal_for_competing_candidates() -> (
    None
):
    candidates = _assembled_candidates()
    feature_matrix = QuantMatrix(
        matrix_id="shared_only_feature_matrix",
        entity_kind=QuantEntityKind.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("shared_backbone",),
        sample_ids=("sample_a",),
        values=((100.0,),),
        missing_value_states=((MissingValueState.OBSERVED,),),
        support_counts=((1,),),
        row_metadata=(({"protein_id": "P11111", "peptide_ids": "pep_backbone"}),),
    )

    report = quantify_supported_proteoforms(candidates, feature_matrix)

    assert all(entry.abundance is None for entry in report.entries)
    assert all(entry.unique_support_count == 0 for entry in report.entries)
    assert all(
        entry.quantification_confidence
        is ProteoformQuantificationConfidence.INSUFFICIENT_UNIQUE_SUPPORT
        for entry in report.entries
    )


def _assembled_candidates():
    return assemble_proteoform_candidates(
        (
            ProteoformPeptideEvidence(
                peptide_id="pep_backbone",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
            ),
            ProteoformPeptideEvidence(
                peptide_id="pep_unmodified",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
                excluded_sites=("P11111:S7:Phospho",),
            ),
        ),
        (
            ProteoformPtmEvidence(
                site_id="P11111:S7:Phospho",
                protein_id="P11111",
                supporting_peptides=("pep_modified",),
            ),
        ),
    )
