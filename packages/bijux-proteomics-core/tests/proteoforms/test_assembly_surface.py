# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.proteoforms import (
    ProteoformCandidateAmbiguityClass,
    ProteoformPeptideEvidence,
    ProteoformPtmEvidence,
    assemble_proteoform_candidates,
    render_proteoform_candidate_tsv,
)


def test_assemble_proteoform_candidates_separates_incompatible_peptide_and_ptm_evidence() -> None:
    entries = assemble_proteoform_candidates(
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

    assert len(entries) == 2
    modified = next(entry for entry in entries if entry.required_sites)
    unmodified = next(entry for entry in entries if not entry.required_sites)

    assert modified.required_sites == ("P11111:S7:Phospho",)
    assert modified.required_peptides == ("pep_backbone", "pep_modified")
    assert modified.excluded_by_evidence == ("pep_unmodified",)
    assert modified.ambiguity_class is (
        ProteoformCandidateAmbiguityClass.INCOMPATIBLE_EVIDENCE
    )

    assert unmodified.required_peptides == ("pep_backbone", "pep_unmodified")
    assert unmodified.excluded_by_evidence == ("P11111:S7:Phospho",)
    assert unmodified.ambiguity_class is (
        ProteoformCandidateAmbiguityClass.INCOMPATIBLE_EVIDENCE
    )


def test_assemble_proteoform_candidates_renders_surface_and_marks_ambiguous_support() -> None:
    entries = assemble_proteoform_candidates(
        (
            ProteoformPeptideEvidence(
                peptide_id="pep_site",
                protein_id="P22222",
                peptide_sequence="MSTYQ",
                start=3,
                end=7,
                required_sites=("P22222:T5:Phospho",),
            ),
        ),
        (
            ProteoformPtmEvidence(
                site_id="P22222:T5:Phospho",
                protein_id="P22222",
                supporting_peptides=("pep_site",),
                ambiguous=True,
            ),
        ),
    )
    rendered = render_proteoform_candidate_tsv(entries)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.ambiguity_class is (
        ProteoformCandidateAmbiguityClass.AMBIGUOUS_SITE_SUPPORT
    )
    assert rendered.startswith(
        "proteoform_id\tprotein_id\trequired_peptides\trequired_sites\texcluded_by_evidence\tambiguity_class\n"
    )
    assert "ambiguous_site_support" in rendered
