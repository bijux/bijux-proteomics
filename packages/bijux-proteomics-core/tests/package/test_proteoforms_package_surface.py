# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

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
