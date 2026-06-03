# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_proteomics.interpretation import OrthologRecord
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    CrossStudyProteinStudyInput,
    build_biological_result_report_bundle,
    build_proteomics_study_result,
    compare_studies,
    render_multi_study_comparison_summary_tsv,
    render_multi_study_conflicting_effects_tsv,
    render_multi_study_harmonized_proteins_tsv,
    render_multi_study_shared_effects_tsv,
    render_multi_study_shared_pathways_tsv,
    render_multi_study_study_specific_pathways_tsv,
    render_multi_study_unresolved_proteins_tsv,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinUnresolvedReason,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _base_biological_report() -> BiologicalResultReportBundle:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    return cast(
        BiologicalResultReportBundle,
        build_biological_result_report_bundle(
            _fixture("biological_report_features.tsv"),
            build_experiment_design(design_entries),
            proteins_fasta_path=_fixture("biological_report_reference.fasta"),
            pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
            condition_a="control",
            condition_b="treatment",
        ),
    )


def _study_input(
    study_id: str,
    report: BiologicalResultReportBundle,
    *,
    species: str,
) -> CrossStudyProteinStudyInput:
    return CrossStudyProteinStudyInput(
        study_id=study_id,
        study_result=build_proteomics_study_result(report),
        species=species,
    )


def _report_with_changed_effects_and_pathways(
    base_report: BiologicalResultReportBundle,
) -> tuple[BiologicalResultReportBundle, BiologicalResultReportBundle]:
    updated_cards = []
    for card in base_report.protein_cards.cards:
        if card.representative_protein_ref == "Q9Y243":
            updated_cards.append(
                card.model_copy(
                    update={
                        "differential_result": card.differential_result.model_copy(
                            update={
                                "mean_log2_abundance_a": 5.0,
                                "mean_log2_abundance_b": 7.9,
                                "log2_fold_change": 2.9,
                            }
                        )
                    }
                )
            )
            continue
        updated_cards.append(card)

    updated_entries = []
    for entry in base_report.differential_report.entries:
        if entry.entity_id == "Q9Y243":
            updated_entries.append(
                entry.model_copy(
                    update={
                        "mean_log2_abundance_a": 5.0,
                        "mean_log2_abundance_b": 7.9,
                        "log2_fold_change": 2.9,
                    }
                )
            )
            continue
        updated_entries.append(entry)

    assert base_report.pathway_enrichment_report is not None
    shared_pathway = base_report.pathway_enrichment_report.entries[0]
    study_specific_inactive = shared_pathway.model_copy(
        update={
            "pathway_id": "custom:study_specific",
            "pathway_name": "Study specific pathway",
            "source_name": "custom",
            "source_accession": "SPEC-01",
            "foreground_overlap_count": 1,
            "background_member_count": 3,
            "expected_overlap_count": 1.0,
            "enrichment_ratio": 1.0,
            "p_value": 0.2,
            "adjusted_p_value": 0.2,
            "foreground_member_ids": ("P04637",),
            "background_member_ids": ("P04637", "O14920", "Q9Y243"),
        }
    )
    study_specific_active = study_specific_inactive.model_copy(
        update={
            "enrichment_ratio": 2.0,
            "p_value": 0.01,
            "adjusted_p_value": 0.01,
        }
    )

    return (
        base_report.model_copy(
            update={
                "protein_cards": base_report.protein_cards.model_copy(
                    update={"cards": tuple(updated_cards)}
                ),
                "differential_report": base_report.differential_report.model_copy(
                    update={"entries": tuple(updated_entries)}
                ),
                "pathway_enrichment_report": base_report.pathway_enrichment_report.model_copy(
                    update={
                        "entries": (
                            shared_pathway,
                            study_specific_active,
                        )
                    }
                ),
            }
        ),
        base_report.model_copy(
            update={
                "pathway_enrichment_report": base_report.pathway_enrichment_report.model_copy(
                    update={
                        "entries": (
                            shared_pathway,
                            study_specific_inactive,
                        )
                    }
                )
            }
        ),
    )


def _single_protein_report(
    base_report: BiologicalResultReportBundle,
    protein_ref: str,
) -> BiologicalResultReportBundle:
    cards = tuple(
        card
        for card in base_report.protein_cards.cards
        if card.representative_protein_ref == protein_ref
    )
    entries = tuple(
        entry
        for entry in base_report.differential_report.entries
        if entry.entity_id == protein_ref
    )
    return base_report.model_copy(
        update={
            "protein_cards": base_report.protein_cards.model_copy(
                update={"cards": cards}
            ),
            "differential_report": base_report.differential_report.model_copy(
                update={"entries": entries}
            ),
            "pathway_activity_report": None,
            "pathway_enrichment_report": None,
        }
    )


def _ambiguous_mouse_report(
    base_report: BiologicalResultReportBundle,
) -> BiologicalResultReportBundle:
    source_card = next(
        card
        for card in base_report.protein_cards.cards
        if card.representative_protein_ref == "P04637"
    )
    source_entry = next(
        entry
        for entry in base_report.differential_report.entries
        if entry.entity_id == "P04637"
    )
    mouse_cards = (
        source_card.model_copy(
            update={
                "card_id": "mouse-card-1",
                "protein_group_id": "mouse-group-1",
                "representative_protein_ref": "Q9MOUSE1",
                "protein_refs": ("Q9MOUSE1",),
                "annotation": source_card.annotation.model_copy(
                    update={
                        "organism": "Mus musculus",
                        "gene_symbol": "Trp53",
                        "accession_aliases": (),
                    }
                ),
            }
        ),
        source_card.model_copy(
            update={
                "card_id": "mouse-card-2",
                "protein_group_id": "mouse-group-2",
                "representative_protein_ref": "Q9MOUSE2",
                "protein_refs": ("Q9MOUSE2",),
                "annotation": source_card.annotation.model_copy(
                    update={
                        "organism": "Mus musculus",
                        "gene_symbol": "Trp53",
                        "accession_aliases": (),
                    }
                ),
            }
        ),
    )
    mouse_entries = (
        source_entry.model_copy(update={"entity_id": "Q9MOUSE1"}),
        source_entry.model_copy(update={"entity_id": "Q9MOUSE2"}),
    )
    return base_report.model_copy(
        update={
            "protein_cards": base_report.protein_cards.model_copy(
                update={"cards": mouse_cards}
            ),
            "differential_report": base_report.differential_report.model_copy(
                update={"entries": mouse_entries}
            ),
            "pathway_activity_report": None,
            "pathway_enrichment_report": None,
        }
    )


def test_multi_study_comparison_outputs_harmonized_shared_conflicting_and_study_specific_surfaces() -> (
    None
):
    base_report = _base_biological_report()
    study_b_report, study_a_report = _report_with_changed_effects_and_pathways(
        base_report
    )

    report = compare_studies(
        (
            _study_input("study_a", study_a_report, species="Homo sapiens"),
            _study_input("study_b", study_b_report, species="Homo sapiens"),
        )
    )

    assert report.summary.harmonized_protein_group_count >= 5
    assert any(
        "P04637" in entry.representative_protein_refs for entry in report.shared_effects
    )
    assert any(
        "Q9Y243" in entry.representative_protein_refs
        for entry in report.conflicting_effects
    )
    assert any(
        entry.pathway_id == "custom:response" for entry in report.shared_pathways
    )
    assert any(
        entry.pathway_id == "custom:study_specific"
        for entry in report.study_specific_pathways
    )
    assert (
        report.manifest.artifacts.harmonized_proteins_tsv
        == "multi_study_harmonized_proteins.tsv"
    )
    assert (
        report.artifacts["conflicting_effects_tsv"]
        == "multi_study_conflicting_effects.tsv"
    )
    assert {warning.warning_code for warning in report.warnings} == {
        "conflicting_effects_present"
    }
    assert report.rejected_evidence == ()
    assert (
        "harmonized_protein_group_count"
        in render_multi_study_comparison_summary_tsv(report)
    )
    assert "harmonized_id" in render_multi_study_harmonized_proteins_tsv(report)
    assert "replicated_hit" in render_multi_study_shared_effects_tsv(report)
    assert "conflicting_hit" in render_multi_study_conflicting_effects_tsv(report)
    assert "shared_signal" in render_multi_study_shared_pathways_tsv(report)
    assert "study_specific_signal" in render_multi_study_study_specific_pathways_tsv(
        report
    )


def test_multi_study_comparison_keeps_ambiguous_cross_species_mappings_unresolved() -> (
    None
):
    base_report = _base_biological_report()
    human_report = _single_protein_report(base_report, "P04637")
    mouse_report = _ambiguous_mouse_report(base_report)

    report = compare_studies(
        (
            _study_input("human", human_report, species="Homo sapiens"),
            _study_input("mouse", mouse_report, species="Mus musculus"),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P04637",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
                source_gene_symbol="TP53",
                target_gene_symbol="Trp53",
            ),
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P04637",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE2",
                source_gene_symbol="TP53",
                target_gene_symbol="Trp53",
            ),
        ),
    )

    assert report.harmonized_proteins == ()
    assert report.shared_effects == ()
    assert report.conflicting_effects == ()
    assert report.summary.ambiguous_ortholog_unresolved_count == 3
    assert {entry.reason for entry in report.unresolved_proteins} == {
        CrossStudyProteinUnresolvedReason.AMBIGUOUS_ORTHOLOG_MAPPING
    }
    assert {warning.warning_code for warning in report.warnings} == {
        "ambiguous_ortholog_unresolved"
    }
    assert len(report.rejected_evidence) == 3
    assert {entry.reason_code for entry in report.rejected_evidence} == {
        "ambiguous_ortholog_mapping"
    }
    unresolved_tsv = render_multi_study_unresolved_proteins_tsv(report)
    assert "ambiguous_ortholog_mapping" in unresolved_tsv
    assert "Q9MOUSE1" in unresolved_tsv
    assert "Q9MOUSE2" in unresolved_tsv
