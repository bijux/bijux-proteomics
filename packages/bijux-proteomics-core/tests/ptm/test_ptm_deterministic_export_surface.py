# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmCoordinateValidationIssue,
    PtmCoordinateValidationReport,
    PtmProteinCorrectionMode,
    PtmSiteQuantAmbiguityPolicy,
    build_ptm_ambiguity_review_report,
    build_ptm_differential_analysis_report,
    build_ptm_localization_scoring_report,
    build_ptm_protein_site_mapping_report,
    build_ptm_site_ambiguity_report,
    build_ptm_site_coverage_report,
    build_ptm_site_group_quantification_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_coordinate_validation_tsv,
    render_ptm_differential_volcano_tsv,
    render_ptm_localized_site_review_tsv,
    render_ptm_protein_site_mapping_tsv,
    render_ptm_site_ambiguity_tsv,
    render_ptm_site_coverage_tsv,
    render_ptm_site_differential_tsv,
    render_ptm_site_group_quant_matrix_tsv,
    render_ptm_site_group_quant_missingness_tsv,
    render_ptm_site_quant_excluded_tsv,
    render_ptm_site_quant_matrix_tsv,
    render_ptm_site_quant_missingness_tsv,
    render_ptm_site_table_tsv,
    render_ptm_unlocalized_group_review_tsv,
    render_ptm_unmapped_peptide_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _localization_report():
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    return build_ptm_localization_scoring_report(
        evidence.accepted_records,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y7"),
            "scan=ptm-005": ("b2",),
        },
    )


def test_ptm_quantification_renderers_are_deterministic_under_equivalent_tuple_order() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
        ambiguity_policy=PtmSiteQuantAmbiguityPolicy.EXCLUDE,
    )

    reordered = report.model_copy(
        update={
            "sample_ids": tuple(reversed(report.sample_ids)),
            "rows": tuple(
                reversed(
                    [
                        row.model_copy(
                            update={
                                "candidate_positions": tuple(
                                    reversed(row.candidate_positions)
                                ),
                                "localized_peptides": tuple(
                                    reversed(row.localized_peptides)
                                ),
                                "values": tuple(reversed(row.values)),
                            }
                        )
                        for row in report.rows
                    ]
                )
            ),
            "ambiguous_group_quantification": report.ambiguous_group_quantification,
            "excluded_ambiguous_rows": tuple(reversed(report.excluded_ambiguous_rows)),
            "excluded_ambiguous_site_keys": tuple(
                reversed(report.excluded_ambiguous_site_keys)
            ),
            "missing_summary": report.missing_summary.model_copy(
                update={"entries": tuple(reversed(report.missing_summary.entries))}
            ),
        }
    )

    assert render_ptm_site_quant_matrix_tsv(report) == render_ptm_site_quant_matrix_tsv(
        reordered
    )
    assert render_ptm_site_quant_missingness_tsv(
        report
    ) == render_ptm_site_quant_missingness_tsv(reordered)
    assert render_ptm_site_quant_excluded_tsv(
        report
    ) == render_ptm_site_quant_excluded_tsv(reordered)


def test_ptm_mapping_and_review_renderers_are_deterministic_under_equivalent_tuple_order() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    ambiguity = build_ptm_site_ambiguity_report(site_table)
    coverage = build_ptm_site_coverage_report(mappings)

    reordered_mappings = tuple(
        reversed(
            [
                mapping.model_copy(
                    update={
                        "candidate_protein_positions": tuple(
                            reversed(mapping.candidate_protein_positions)
                        )
                    }
                )
                for mapping in mappings
            ]
        )
    )
    reordered_site_table = tuple(
        reversed(
            [
                entry.model_copy(
                    update={
                        "sample_ids": tuple(reversed(entry.sample_ids)),
                        "candidate_positions": tuple(
                            reversed(entry.candidate_positions)
                        ),
                    }
                )
                for entry in site_table
            ]
        )
    )
    reordered_ambiguity = tuple(
        reversed(
            [
                entry.model_copy(
                    update={
                        "candidate_positions": tuple(
                            reversed(entry.candidate_positions)
                        ),
                        "localized_peptides": tuple(reversed(entry.localized_peptides)),
                    }
                )
                for entry in ambiguity
            ]
        )
    )
    reordered_coverage = tuple(
        reversed(
            [
                entry.model_copy(
                    update={
                        "spectra": tuple(reversed(entry.spectra)),
                        "peptides": tuple(reversed(entry.peptides)),
                    }
                )
                for entry in coverage
            ]
        )
    )
    validation = PtmCoordinateValidationReport(
        valid=False,
        issues=(
            PtmCoordinateValidationIssue(
                spectrum_id="scan=2",
                protein_ref="P11111",
                site_key="P11111:S999:Phospho",
                code="protein_position_out_of_range",
                message="protein position exceeds sequence length",
            ),
            PtmCoordinateValidationIssue(
                spectrum_id="scan=1",
                protein_ref="P11111",
                site_key="P11111:S1:Phospho",
                code="residue_mismatch",
                message="residue mismatch",
            ),
        ),
    )
    reordered_validation = validation.model_copy(
        update={"issues": tuple(reversed(validation.issues))}
    )

    assert render_ptm_protein_site_mapping_tsv(
        mappings
    ) == render_ptm_protein_site_mapping_tsv(reordered_mappings)
    assert render_ptm_site_table_tsv(site_table) == render_ptm_site_table_tsv(
        reordered_site_table
    )
    assert render_ptm_site_ambiguity_tsv(ambiguity) == render_ptm_site_ambiguity_tsv(
        reordered_ambiguity
    )
    assert render_ptm_site_coverage_tsv(coverage) == render_ptm_site_coverage_tsv(
        reordered_coverage
    )
    assert render_ptm_coordinate_validation_tsv(
        validation
    ) == render_ptm_coordinate_validation_tsv(reordered_validation)


def test_ptm_unmapped_renderer_is_deterministic_under_equivalent_tuple_order(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / "unmapped.tsv"
    evidence_path.write_text(
        "\n".join(
            (
                "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                "C1\tscan=unmapped-1\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP40404\t0.990\t1\ttarget",
                "C1\tscan=unmapped-2\tT[Phospho]IDE\t2\t90.0\t0.020\tP50505\t0.700\t1\ttarget",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = parse_ptm_localization_tsv(evidence_path)
    report = build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    reordered = tuple(reversed(report.unmapped_peptides))

    assert render_ptm_unmapped_peptide_tsv(
        report.unmapped_peptides
    ) == render_ptm_unmapped_peptide_tsv(reordered)


def test_ptm_ambiguity_and_differential_renderers_are_deterministic_under_equivalent_tuple_order() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    localization = _localization_report()
    review = build_ptm_ambiguity_review_report(
        site_table,
        localization_scoring_report=localization,
        protein_sequences=_protein_sequences(),
    )
    group_quant = build_ptm_site_group_quantification_report(
        site_table,
        feature_records=features.accepted_records,
        localization_scoring_report=localization,
        protein_sequences=_protein_sequences(),
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    differential = build_ptm_differential_analysis_report(
        build_ptm_site_quantification_report(
            site_table,
            feature_records=features.accepted_records,
        ),
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=features.accepted_records,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )

    reordered_review = review.model_copy(
        update={
            "localized_sites": tuple(
                reversed(
                    [
                        entry.model_copy(
                            update={
                                "localized_peptides": tuple(
                                    reversed(entry.localized_peptides)
                                ),
                                "sample_ids": tuple(reversed(entry.sample_ids)),
                            }
                        )
                        for entry in review.localized_sites
                    ]
                )
            ),
            "unlocalized_groups": tuple(
                reversed(
                    [
                        entry.model_copy(
                            update={
                                "candidate_positions": tuple(
                                    reversed(entry.candidate_positions)
                                ),
                                "possible_residues": tuple(
                                    reversed(entry.possible_residues)
                                ),
                                "site_keys": tuple(reversed(entry.site_keys)),
                                "localized_peptides": tuple(
                                    reversed(entry.localized_peptides)
                                ),
                                "sample_ids": tuple(reversed(entry.sample_ids)),
                            }
                        )
                        for entry in review.unlocalized_groups
                    ]
                )
            ),
        }
    )
    reordered_group_quant = group_quant.model_copy(
        update={
            "sample_ids": tuple(reversed(group_quant.sample_ids)),
            "rows": tuple(
                reversed(
                    [
                        row.model_copy(
                            update={
                                "candidate_positions": tuple(
                                    reversed(row.candidate_positions)
                                ),
                                "possible_residues": tuple(
                                    reversed(row.possible_residues)
                                ),
                                "values": tuple(reversed(row.values)),
                            }
                        )
                        for row in group_quant.rows
                    ]
                )
            ),
            "missing_summary": group_quant.missing_summary.model_copy(
                update={"entries": tuple(reversed(group_quant.missing_summary.entries))}
            ),
        }
    )
    reordered_differential = differential.differential_report.model_copy(
        update={
            "entries": tuple(
                reversed(
                    [
                        entry.model_copy(
                            update={
                                "localized_peptides": tuple(
                                    reversed(entry.localized_peptides)
                                ),
                                "condition_a": "treated",
                                "condition_b": "control",
                            }
                        )
                        for entry in differential.differential_report.entries
                    ]
                )
            )
        }
    ).model_copy(
        update={
            "condition_a": differential.differential_report.condition_a,
            "condition_b": differential.differential_report.condition_b,
            "entries": tuple(
                entry.model_copy(
                    update={
                        "condition_a": differential.differential_report.condition_a,
                        "condition_b": differential.differential_report.condition_b,
                    }
                )
                for entry in reversed(differential.differential_report.entries)
            ),
        }
    )
    reordered_volcano = differential.volcano_plot.model_copy(
        update={"points": tuple(reversed(differential.volcano_plot.points))}
    )

    assert render_ptm_localized_site_review_tsv(
        review
    ) == render_ptm_localized_site_review_tsv(reordered_review)
    assert render_ptm_unlocalized_group_review_tsv(
        review
    ) == render_ptm_unlocalized_group_review_tsv(reordered_review)
    assert render_ptm_site_group_quant_matrix_tsv(
        group_quant
    ) == render_ptm_site_group_quant_matrix_tsv(reordered_group_quant)
    assert render_ptm_site_group_quant_missingness_tsv(
        group_quant
    ) == render_ptm_site_group_quant_missingness_tsv(reordered_group_quant)
    assert render_ptm_site_differential_tsv(
        differential.differential_report
    ) == render_ptm_site_differential_tsv(reordered_differential)
    assert render_ptm_differential_volcano_tsv(
        differential.volcano_plot
    ) == render_ptm_differential_volcano_tsv(reordered_volcano)
