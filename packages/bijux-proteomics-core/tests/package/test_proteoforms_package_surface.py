# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix,
    QuantMeasureKind,
)
import bijux_proteomics.proteoforms as proteoforms


def test_proteoforms_package_exports_candidate_assembly_surface() -> None:
    entries = proteoforms.assemble_proteoform_candidates(
        (
            proteoforms.ProteoformPeptideEvidence(
                peptide_id="pep_backbone",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
            ),
            proteoforms.ProteoformPeptideEvidence(
                peptide_id="pep_unmodified",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
                excluded_sites=("P11111:S7:Phospho",),
            ),
        ),
        (
            proteoforms.ProteoformPtmEvidence(
                site_id="P11111:S7:Phospho",
                protein_id="P11111",
                supporting_peptides=("pep_modified",),
            ),
        ),
    )
    rendered = proteoforms.render_proteoform_candidate_tsv(entries)

    assert hasattr(proteoforms, "assemble_proteoform_candidates")
    assert hasattr(proteoforms, "render_proteoform_candidate_tsv")
    assert len(entries) == 2
    assert any(entry.required_sites == ("P11111:S7:Phospho",) for entry in entries)
    assert "ambiguity_class" in rendered


def test_proteoforms_package_exports_quantification_guard_surface() -> None:
    candidates = proteoforms.assemble_proteoform_candidates(
        (
            proteoforms.ProteoformPeptideEvidence(
                peptide_id="pep_backbone",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
            ),
            proteoforms.ProteoformPeptideEvidence(
                peptide_id="pep_unmodified",
                protein_id="P11111",
                peptide_sequence="AASTYK",
                start=5,
                end=10,
                excluded_sites=("P11111:S7:Phospho",),
            ),
        ),
        (
            proteoforms.ProteoformPtmEvidence(
                site_id="P11111:S7:Phospho",
                protein_id="P11111",
                supporting_peptides=("pep_modified",),
            ),
        ),
    )
    feature_matrix = QuantMatrix(
        matrix_id="proteoform_quant_surface",
        entity_kind=QuantEntityKind.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        entity_ids=("shared_backbone", "modified_site", "unmodified_peptide"),
        sample_ids=("sample_a",),
        values=((100.0,), (40.0,), (60.0,)),
        missing_value_states=(
            (MissingValueState.OBSERVED,),
            (MissingValueState.OBSERVED,),
            (MissingValueState.OBSERVED,),
        ),
        support_counts=((1,), (1,), (1,)),
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

    report = proteoforms.quantify_supported_proteoforms(candidates, feature_matrix)
    rendered = proteoforms.render_proteoform_quantification_tsv(report)

    assert hasattr(proteoforms, "quantify_supported_proteoforms")
    assert hasattr(proteoforms, "render_proteoform_quantification_tsv")
    assert any(entry.abundance == 40.0 for entry in report.entries)
    assert "quantification_confidence" in rendered
