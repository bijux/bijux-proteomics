# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import shutil

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli import cli
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak, render_mgf

FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def _similarity_spectrum(
    spectrum_id: str,
    peaks: tuple[tuple[float, float], ...],
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=tuple(
            SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks
        ),
    )


def test_program_template_writes_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "program-template",
                "--program-id",
                "prog-1",
                "--name",
                "demo",
                "--objective",
                "screen candidates",
                "--target-id",
                "tgt-1",
                "--target-name",
                "Target",
                "--sequence",
                "ACDEFGHIKLMNPQRSTVWY",
                "--organism",
                "human",
                "--mechanism",
                "stabilize binding state",
                "--out",
                "program.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["program_id"] == "prog-1"
        manifest = json.loads(Path("program.json").read_text())
        assert manifest["document_schema"]["schema_version"] == "1.0.0"


def test_annotate_proteins_command_emits_mapped_unmapped_and_rejected_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_input.tsv",
            "protein_annotation_input.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "annotate-proteins",
                "protein_annotation_input.tsv",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "protein_annotation.summary.tsv",
                "--mapped-tsv-out",
                "protein_annotation.mapped.tsv",
                "--unmapped-tsv-out",
                "protein_annotation.unmapped.tsv",
                "--rejected-input-tsv-out",
                "protein_annotation.input_rejected.tsv",
                "--rejected-annotation-tsv-out",
                "protein_annotation.annotation_rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_report"]["summary"]["input_entry_count"] == 6
        assert payload["mapping_report"]["summary"]["mapped_entry_count"] == 6
        assert payload["mapping_report"]["summary"]["unmapped_entry_count"] == 0
        assert Path("protein_annotation.summary.tsv").read_text().splitlines()[
            0
        ].startswith("input_entry_count\tmapped_entry_count")
        assert "TRP53" in Path("protein_annotation.mapped.tsv").read_text()
        assert (
            Path("protein_annotation.unmapped.tsv").read_text().splitlines()[0]
            == "row_number\tsource_row_id\tinput_protein_ref\tprotein_ref\tinput_metadata\treason"
        )
        assert (
            "protein row requires at least one protein reference"
            in Path("protein_annotation.input_rejected.tsv").read_text()
        )
        assert (
            "duplicate protein annotation for P04637"
            in Path("protein_annotation.annotation_rejected.tsv").read_text()
        )


def test_map_orthologs_command_emits_mapped_unmapped_and_rejected_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(interpretation_fixture_dir / "ortholog_input.tsv", "ortholog_input.tsv")
        shutil.copy(
            interpretation_fixture_dir / "ortholog_cli.tsv",
            "ortholog_cli.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "map-orthologs",
                "ortholog_input.tsv",
                "ortholog_cli.tsv",
                "--source-species",
                "human",
                "--target-species",
                "mouse",
                "--summary-tsv-out",
                "ortholog.summary.tsv",
                "--mapped-tsv-out",
                "ortholog.mapped.tsv",
                "--unmapped-tsv-out",
                "ortholog.unmapped.tsv",
                "--rejected-input-tsv-out",
                "ortholog.input_rejected.tsv",
                "--rejected-ortholog-tsv-out",
                "ortholog.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_report"]["summary"]["input_entry_count"] == 7
        assert payload["mapping_report"]["summary"]["mapped_entry_count"] == 9
        assert payload["mapping_report"]["summary"]["unmapped_entry_count"] == 1
        assert Path("ortholog.summary.tsv").read_text().splitlines()[0].startswith(
            "source_species\ttarget_species\tinput_entry_count\tmapped_entry_count"
        )
        assert "P005\thuman\tmouse\tM005" in Path("ortholog.mapped.tsv").read_text()
        assert "P999\thuman\tmouse" in Path("ortholog.unmapped.tsv").read_text()
        assert (
            Path("ortholog.input_rejected.tsv").read_text().splitlines()[0]
            == "row_number\tvalues\treason"
        )
        assert (
            "duplicate ortholog relationship for human:P001 -> mouse:M001"
            in Path("ortholog.rejected.tsv").read_text()
        )


def test_protein_set_score_command_emits_matrix_condition_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        quant_fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(quant_fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(quant_fixture_dir / "quant.design.tsv", "quant.design.tsv")
        shutil.copy(interpretation_fixture_dir / "protein_sets.tsv", "protein_sets.tsv")
        shutil.copy(
            interpretation_fixture_dir / "protein_sets_invalid.tsv",
            "protein_sets_invalid.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "protein-set-score",
                "ms1_features.tsv",
                "protein_sets.tsv",
                "--design",
                "quant.design.tsv",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "protein_set_score.summary.tsv",
                "--matrix-tsv-out",
                "protein_set_score.matrix.tsv",
                "--sample-score-tsv-out",
                "protein_set_score.samples.tsv",
                "--condition-score-tsv-out",
                "protein_set_score.conditions.tsv",
                "--condition-comparison-tsv-out",
                "protein_set_score.comparisons.tsv",
                "--unresolved-tsv-out",
                "protein_set_score.unresolved.tsv",
                "--rejected-set-tsv-out",
                "protein_set_score.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["report"]["summary"]["set_count"] == 3
        assert payload["report"]["summary"]["condition_comparison_count"] == 3
        assert payload["outputs"]["matrix_tsv"] == "protein_set_score.matrix.tsv"
        assert "set_id\tset_name\tsource_name\tC1\tC2\tT1\tT2" in Path(
            "protein_set_score.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\tactivity_score" in Path(
            "protein_set_score.samples.tsv"
        ).read_text(encoding="utf-8")
        assert "condition\tsample_count\tscored_sample_count" in Path(
            "protein_set_score.conditions.tsv"
        ).read_text(encoding="utf-8")
        assert "condition_a\tcondition_b\tmean_activity_score_a" in Path(
            "protein_set_score.comparisons.tsv"
        ).read_text(encoding="utf-8")
        assert "P999" in Path("protein_set_score.unresolved.tsv").read_text(
            encoding="utf-8"
        )
        assert Path("protein_set_score.rejected.tsv").read_text(encoding="utf-8").splitlines()[
            0
        ] == "row_number\tvalues\treason"


def test_go_enrichment_command_emits_term_and_unannotated_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "go_foreground.tsv",
            "go_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "go_background.tsv",
            "go_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "go_annotations.tsv",
            "go_annotations.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "go-enrichment",
                "go_foreground.tsv",
                "go_background.tsv",
                "go_annotations.tsv",
                "--summary-tsv-out",
                "go_enrichment.summary.tsv",
                "--term-tsv-out",
                "go_enrichment.term.tsv",
                "--unannotated-tsv-out",
                "go_enrichment.unannotated.tsv",
                "--rejected-annotation-tsv-out",
                "go_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "0.6",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_term_count"] == 3
        assert Path("go_enrichment.summary.tsv").read_text().splitlines()[0].startswith(
            "foreground_size\tbackground_size"
        )
        assert "GO:0006915" in Path("go_enrichment.term.tsv").read_text()
        assert "background\tQ88888" in Path("go_enrichment.unannotated.tsv").read_text()
        assert (
            "duplicate GO membership for P04637 and GO:0006915"
            in Path("go_enrichment.rejected.tsv").read_text()
        )


def test_pathway_enrichment_command_emits_pathway_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "pathway_foreground.tsv",
            "pathway_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "pathway_background.tsv",
            "pathway_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "pathway_memberships.tsv",
            "pathway_memberships.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "pathway-enrichment",
                "pathway_foreground.tsv",
                "pathway_background.tsv",
                "pathway_memberships.tsv",
                "--fasta",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "pathway_enrichment.summary.tsv",
                "--pathway-tsv-out",
                "pathway_enrichment.pathway.tsv",
                "--unresolved-tsv-out",
                "pathway_enrichment.unresolved.tsv",
                "--rejected-pathway-tsv-out",
                "pathway_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_entry_count"] == 5
        assert Path("pathway_enrichment.summary.tsv").read_text().splitlines()[
            0
        ].startswith("foreground_size\tbackground_size")
        assert "hsa04115" in Path("pathway_enrichment.pathway.tsv").read_text()
        assert (
            "background\tQ88888\t"
            in Path("pathway_enrichment.unresolved.tsv").read_text()
        )
        assert (
            "duplicate pathway membership for custom:stress and gene member TP53"
            in Path("pathway_enrichment.rejected.tsv").read_text()
        )


def test_complex_enrichment_command_emits_complex_and_unresolved_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        interpretation_fixture_dir = FIXTURE_ROOT / "interpretation"
        shutil.copy(
            interpretation_fixture_dir / "complex_foreground.tsv",
            "complex_foreground.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "complex_background.tsv",
            "complex_background.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "complex_memberships.tsv",
            "complex_memberships.tsv",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_reference.fasta",
            "protein_annotation_reference.fasta",
        )
        shutil.copy(
            interpretation_fixture_dir / "protein_annotation_custom.tsv",
            "protein_annotation_custom.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "interpretation",
                "complex-enrichment",
                "complex_foreground.tsv",
                "complex_background.tsv",
                "complex_memberships.tsv",
                "--fasta",
                "protein_annotation_reference.fasta",
                "--annotation-tsv",
                "protein_annotation_custom.tsv",
                "--summary-tsv-out",
                "complex_enrichment.summary.tsv",
                "--complex-tsv-out",
                "complex_enrichment.complex.tsv",
                "--unresolved-tsv-out",
                "complex_enrichment.unresolved.tsv",
                "--rejected-complex-tsv-out",
                "complex_enrichment.rejected.tsv",
                "--max-adjusted-p-value",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["foreground_size"] == 3
        assert payload["report"]["summary"]["background_size"] == 6
        assert payload["report"]["summary"]["evaluated_entry_count"] == 4
        assert Path("complex_enrichment.summary.tsv").read_text().splitlines()[
            0
        ].startswith("foreground_size\tbackground_size")
        assert "CORUM:0176" in Path("complex_enrichment.complex.tsv").read_text()
        assert (
            "background\tQ88888\t"
            in Path("complex_enrichment.unresolved.tsv").read_text()
        )
        assert (
            "duplicate complex membership for custom:stressosome and gene member TP53"
            in Path("complex_enrichment.rejected.tsv").read_text()
        )


def test_fasta_commands_cover_parse_stats_dedup_filter_provenance_and_decoy(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(fasta_fixture_dir / "dedup_input.fasta", "dedup.fasta")
        shutil.copy(
            fasta_fixture_dir / "external_contaminants.fasta",
            "external_contaminants.fasta",
        )
        shutil.copy(
            fasta_fixture_dir / "production_grade_database.fasta",
            "production.fasta",
        )

        parse_result = runner.invoke(
            cli, ["fasta-parse", "valid.fasta", "--mode", "strict"]
        )
        assert parse_result.exit_code == 0
        parse_payload = json.loads(parse_result.output)
        assert parse_payload["total_records"] == 3
        assert parse_payload["database_composition"]["accepted_record_count"] == 3
        assert parse_payload["duplicate_accessions"] == []

        stats_result = runner.invoke(
            cli,
            [
                "fasta-stats",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
            ],
        )
        assert stats_result.exit_code == 0
        stats_payload = json.loads(stats_result.output)
        assert stats_payload["duplicate_accession_count"] == 1
        assert stats_payload["duplicate_sequence_count"] == 2

        contaminant_build_result = runner.invoke(
            cli,
            [
                "fasta-contaminants",
                "valid.fasta",
                "--mode",
                "strict",
                "--contaminant-fasta",
                "external_contaminants.fasta",
                "--out-fasta",
                "target_with_contaminants.fasta",
            ],
        )
        assert contaminant_build_result.exit_code == 0
        contaminant_build_payload = json.loads(contaminant_build_result.output)
        assert contaminant_build_payload["appended_builtin_record_count"] == 4
        assert contaminant_build_payload["appended_external_record_count"] == 2
        assert contaminant_build_payload["output_record_count"] == 9
        combined_fasta = Path("target_with_contaminants.fasta").read_text()
        assert combined_fasta.count(">") == 9
        assert ">CON__trypsin_lab" in combined_fasta
        assert ">CON__sp|P02769|ALBU_BOVIN" in combined_fasta

        profile_result = runner.invoke(
            cli,
            [
                "fasta-profile",
                "production.fasta",
                "--mode",
                "strict",
                "--summary-tsv-out",
                "production.summary.tsv",
                "--length-tsv-out",
                "production.length.tsv",
                "--organism-tsv-out",
                "production.organism.tsv",
                "--invalid-sequence-tsv-out",
                "production.invalid.tsv",
            ],
        )
        assert profile_result.exit_code == 0
        profile_payload = json.loads(profile_result.output)
        assert profile_payload["summary"]["input_record_count"] == 9
        assert profile_payload["summary"]["protein_count"] == 6
        assert profile_payload["summary"]["target_count"] == 5
        assert profile_payload["summary"]["decoy_count"] == 1
        assert profile_payload["summary"]["contaminant_count"] == 1
        assert profile_payload["summary"]["organism_annotated_count"] == 5
        assert [row["source_identifier"] for row in profile_payload["invalid_sequence_report"]] == [
            "custom_empty",
            "custom_invalid",
        ]
        assert profile_payload["organism_distribution"] == [
            {
                "organism": "Homo sapiens",
                "protein_count": 4,
                "target_count": 3,
                "decoy_count": 1,
                "contaminant_count": 1,
            },
            {
                "organism": "Mus musculus",
                "protein_count": 1,
                "target_count": 1,
                "decoy_count": 0,
                "contaminant_count": 0,
            },
        ]
        assert (
            Path("production.summary.tsv")
            .read_text()
            .splitlines()[0]
            .startswith("input_record_count\tprotein_count\trejected_record_count")
        )
        assert "1-99\t1\t99\t6\t116" in Path("production.length.tsv").read_text()
        assert "Homo sapiens\t4\t3\t1\t1" in Path("production.organism.tsv").read_text()
        assert (
            "custom_empty\tcustom_empty Example empty\tempty_sequence\tsequence must contain at least one amino-acid residue"
            in Path("production.invalid.tsv").read_text()
        )
        assert (
            "custom_invalid\tcustom_invalid Example invalid\tinvalid_character\tsequence contains invalid non-residue characters"
            in Path("production.invalid.tsv").read_text()
        )

        dedup_result = runner.invoke(
            cli,
            [
                "fasta-dedup",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
                "--out-fasta",
                "deduped.fasta",
            ],
        )
        assert dedup_result.exit_code == 0
        dedup_payload = json.loads(dedup_result.output)
        assert dedup_payload["output_records"] == 2
        assert Path("deduped.fasta").read_text().count(">") == 2

        filter_result = runner.invoke(
            cli,
            [
                "fasta-filter",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
                "--organism",
                "Homo sapiens",
                "--exclude-contaminants",
                "--out-fasta",
                "filtered.fasta",
            ],
        )
        assert filter_result.exit_code == 0
        filter_payload = json.loads(filter_result.output)
        assert filter_payload["excluded_as_contaminant"] == 1
        assert "CON__CRAP" not in Path("filtered.fasta").read_text()

        provenance_result = runner.invoke(
            cli,
            [
                "fasta-provenance",
                "valid.fasta",
                "--mode",
                "strict",
                "--out",
                "provenance.json",
            ],
        )
        assert provenance_result.exit_code == 0
        provenance_payload = json.loads(Path("provenance.json").read_text())
        assert (
            provenance_payload["document_schema"]["document_kind"]
            == "fasta_provenance_manifest"
        )

        production_result = runner.invoke(
            cli, ["fasta-parse", "production.fasta", "--mode", "strict"]
        )
        assert production_result.exit_code == 0
        production_payload = json.loads(production_result.output)
        assert production_payload["duplicate_accession_policy"] == "reject"
        assert production_payload["duplicate_accessions"] == ["uniprot:P04637"]
        assert production_payload["database_composition"] == {
            "accepted_record_count": 6,
            "target_count": 5,
            "decoy_count": 1,
            "contaminant_count": 1,
            "accession_namespace_counts": {
                "custom": 2,
                "ensembl": 1,
                "refseq": 1,
                "uniprot": 2,
            },
        }

        permissive_duplicate_parse = runner.invoke(
            cli,
            [
                "fasta-parse",
                "dedup.fasta",
                "--mode",
                "permissive",
                "--duplicate-accession-policy",
                "accept_with_warning",
            ],
        )
        assert permissive_duplicate_parse.exit_code == 0
        permissive_duplicate_payload = json.loads(permissive_duplicate_parse.output)
        assert permissive_duplicate_payload["duplicate_accession_policy"] == (
            "accept_with_warning"
        )
        assert len(permissive_duplicate_payload["accepted_records"]) == 4

        decoy_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "valid.fasta",
                "--mode",
                "strict",
                "--decoy-mode",
                "reverse",
                "--out-fasta",
                "target_decoy.fasta",
                "--manifest-out",
                "target_decoy.manifest.json",
            ],
        )
        assert decoy_result.exit_code == 0
        decoy_payload = json.loads(decoy_result.output)
        assert decoy_payload["valid"] is True
        assert len(decoy_payload["reproducibility_hash"]) == 64
        assert decoy_payload["generation_report"]["input_target_count"] == 3
        assert decoy_payload["generation_report"]["generated_decoy_count"] == 3
        assert decoy_payload["generation_report"]["decoy_mode"] == "reverse"
        assert Path("target_decoy.fasta").read_text().count(">") == 6
        decoy_manifest = json.loads(Path("target_decoy.manifest.json").read_text())
        assert (
            decoy_manifest["document_schema"]["document_kind"]
            == "decoy_generation_manifest"
        )
        assert (
            decoy_manifest["reproducibility_hash"]
            == decoy_payload["reproducibility_hash"]
        )


def test_sequence_checksum_and_target_decoy_validate_commands(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        checksum_result = runner.invoke(
            cli,
            ["sequence-checksum", "--sequence", " acd ef "],
        )
        assert checksum_result.exit_code == 0
        checksum_payload = json.loads(checksum_result.output)
        assert checksum_payload["normalized_sequence"] == "ACDEF"
        assert len(checksum_payload["sequence_checksum"]) == 64

        shutil.copy(
            fasta_fixture_dir / "target_decoy_valid.fasta", "target_decoy_valid.fasta"
        )
        validation_result = runner.invoke(
            cli,
            ["target-decoy-validate", "target_decoy_valid.fasta"],
        )
        assert validation_result.exit_code == 0
        validation_payload = json.loads(validation_result.output)
        assert validation_payload["valid"] is True


def test_fasta_decoy_command_reports_shuffle_caveats_and_prefix_collisions() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("homopolymer.fasta").write_text(
            ">sp|P00001|HOMO_HUMAN Homopolymer OS=Homo sapiens GN=HOMO\nAAAAAA\n"
        )
        shuffle_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "homopolymer.fasta",
                "--mode",
                "strict",
                "--decoy-mode",
                "shuffle",
                "--seed",
                "11",
                "--out-fasta",
                "homopolymer_decoy.fasta",
            ],
        )
        assert shuffle_result.exit_code == 0
        shuffle_payload = json.loads(shuffle_result.output)
        assert shuffle_payload["generation_report"]["unchanged_sequence_count"] == 1
        assert (
            shuffle_payload["generation_report"]["target_sequence_collision_count"] == 1
        )

        Path("collision.fasta").write_text(
            ">target_one Alpha target [Homo sapiens]\nMPEPTIDE\n"
            ">LAB_target_one Existing prefixed target [Homo sapiens]\nMSEQENCE\n"
        )
        collision_result = runner.invoke(
            cli,
            [
                "fasta-decoy",
                "collision.fasta",
                "--mode",
                "strict",
                "--prefix",
                "LAB_",
                "--out-fasta",
                "collision_decoy.fasta",
            ],
        )
        assert collision_result.exit_code != 0
        assert "collide with existing target accessions" in collision_result.output


def test_digest_command_writes_export_and_manifest(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--missed-cleavages",
                "1",
                "--digestion-mode",
                "full",
                "--min-length",
                "3",
                "--format",
                "jsonl",
                "--out",
                "peptides.jsonl",
                "--manifest-out",
                "digest.manifest.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["output_peptide_count"] > 0
        assert len(payload["policy_hash"]) == 64
        assert Path("peptides.jsonl").exists()
        manifest = json.loads(Path("digest.manifest.json").read_text())
        assert manifest["document_schema"]["document_kind"] == "peptide_digest_manifest"
        assert manifest["policy_hash"] == payload["policy_hash"]


def test_digest_command_supports_fasta_export_and_peptide_protein_sidecar(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--format",
                "fasta",
                "--out",
                "peptides.fasta",
                "--peptide-protein-table-out",
                "peptide_protein_table.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["export_format"] == "fasta"
        assert payload["peptide_protein_table_path"] == "peptide_protein_table.tsv"
        assert len(payload["peptide_protein_table_sha256"]) == 64

        fasta_lines = Path("peptides.fasta").read_text().splitlines()
        assert fasta_lines[0].startswith(">")
        assert "|len=" in fasta_lines[0]
        assert "|mass=" in fasta_lines[0]

        table_lines = Path("peptide_protein_table.tsv").read_text().splitlines()
        assert table_lines[0].startswith("sequence\tlength\tneutral_mass")


def test_digest_command_reports_invalid_protease_and_invalid_fasta(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "mixed_quality.fasta", "mixed_quality.fasta")

        invalid_protease = runner.invoke(
            cli,
            [
                "digest",
                "mixed_quality.fasta",
                "--protease",
                "not-a-protease",
                "--out",
                "peptides.tsv",
            ],
        )
        assert invalid_protease.exit_code != 0
        assert "unknown protease rule" in invalid_protease.output

        invalid_fasta = runner.invoke(
            cli,
            [
                "digest",
                "mixed_quality.fasta",
                "--protease",
                "trypsin",
                "--mode",
                "strict",
                "--out",
                "peptides.tsv",
            ],
        )
        assert invalid_fasta.exit_code != 0
        assert "rejected records" in invalid_fasta.output


def test_digest_command_supports_builtin_aspn_and_custom_rules() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nMPEPDADAA\n"
        )

        aspn_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--protease",
                "Asp-N",
                "--out",
                "aspn.tsv",
            ],
        )
        assert aspn_result.exit_code == 0
        aspn_payload = json.loads(aspn_result.output)
        assert aspn_payload["protease"] == "aspn"
        assert aspn_payload["custom_protease"] is None
        aspn_lines = Path("aspn.tsv").read_text().splitlines()
        assert any("\tMPEPDA\t" in line for line in aspn_lines[1:])
        assert any("\tDAA\t" in line for line in aspn_lines[1:])

        custom_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--custom-protease",
                "before=D;block_previous=P",
                "--custom-protease-name",
                "acidic",
                "--out",
                "custom.tsv",
            ],
        )
        assert custom_result.exit_code == 0
        custom_payload = json.loads(custom_result.output)
        assert custom_payload["protease"] == "acidic"
        assert custom_payload["custom_protease"] == "before=D;block_previous=P"
        custom_lines = Path("custom.tsv").read_text().splitlines()
        assert any("\tMPEPDA\t" in line for line in custom_lines[1:])

        conflict_result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--protease",
                "lysc",
                "--custom-protease",
                "before=D;block_previous=P",
                "--out",
                "conflict.tsv",
            ],
        )
        assert conflict_result.exit_code != 0
        assert "cannot be combined" in conflict_result.output


def test_digest_command_supports_regex_custom_protease_rule() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nPEPDADAA\n"
        )

        result = runner.invoke(
            cli,
            [
                "digest",
                "proteins.fasta",
                "--custom-protease",
                "pattern=(?<!P)(?P<site>D);cut_before=site",
                "--custom-protease-name",
                "acidic_regex",
                "--out",
                "regex.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "acidic_regex"
        assert (
            payload["custom_protease"]
            == "pattern=(?<!P)(?P<site>D);cut_before=site"
        )
        regex_lines = Path("regex.tsv").read_text().splitlines()
        assert any("\tPEPDA\t" in line for line in regex_lines[1:])
        assert any("\tDAA\t" in line for line in regex_lines[1:])


def test_digest_command_reports_invalid_output_path(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")

        result = runner.invoke(
            cli,
            [
                "digest",
                "valid.fasta",
                "--protease",
                "trypsin",
                "--out",
                "missing/peptides.tsv",
            ],
        )

        assert result.exit_code != 0
        assert "No such file or directory" in result.output


def test_theoretical_digest_command_writes_governed_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("proteins.fasta").write_text(
            ">sp|P12345|CHEM Protein chemistry\nACDMK\n"
        )

        result = runner.invoke(
            cli,
            [
                "theoretical-digest",
                "proteins.fasta",
                "--protease",
                "trypsin",
                "--static-mod",
                "Carbamidomethyl",
                "--variable-mod",
                "Oxidation",
                "--out-dir",
                "digest_bundle",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["static_modification_names"] == ["Carbamidomethyl"]
        assert payload["variable_modification_names"] == ["Oxidation"]
        assert payload["output_candidate_peptide_count"] == 2
        assert Path("digest_bundle/digest_peptides.tsv").exists()
        assert Path("digest_bundle/peptide_to_protein.tsv").exists()
        assert Path("digest_bundle/digest_summary.tsv").exists()
        assert "ACDM[Oxidation]K" in Path("digest_bundle/digest_peptides.tsv").read_text()
        assert "Carbamidomethyl" in Path("digest_bundle/digest_summary.tsv").read_text()


def test_peptide_index_command_reports_groups_il_equivalence_and_missed_cleavages() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("database.fasta").write_text(
            ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\n"
            "MPEPTLDEKAK\n"
            ">sp|P20001|BETA_HUMAN Beta OS=Homo sapiens GN=BETA\n"
            "AKSHADEQKQQ\n"
            ">sp|P20002|GAMMA_HUMAN Gamma OS=Homo sapiens GN=GAMMA\n"
            "MKSHADEQKLL\n"
        )
        Path("groups.tsv").write_text(
            "accession\tprotein_group\nP20001\tGROUP_SHARED\nP20002\tGROUP_SHARED\n"
        )

        result = runner.invoke(
            cli,
            [
                "peptide-index",
                "database.fasta",
                "--peptide",
                "M[+15.9949]PEPTIDEK",
                "--peptide",
                "MPEPTLDEKAK",
                "--peptide",
                "SHADEQK",
                "--protease",
                "trypsin",
                "--missed-cleavages",
                "1",
                "--digestion-mode",
                "full",
                "--il-equivalent",
                "--protein-group-map",
                "groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["protease"] == "trypsin"
        assert payload["missed_cleavages"] == 1
        assert payload["il_equivalent"] is True
        assert payload["protein_group_map_supplied"] is True

        by_query = {
            entry["input_peptide"]: entry for entry in payload["report"]["entries"]
        }
        assert by_query["M[+15.9949]PEPTIDEK"]["canonical_peptide"] == "MPEPTIDEK"
        assert by_query["M[+15.9949]PEPTIDEK"]["il_equivalence_applied"] is True
        assert by_query["M[+15.9949]PEPTIDEK"]["modification_stripped"] is True
        assert by_query["M[+15.9949]PEPTIDEK"]["uniqueness_class"] == "unique"
        assert by_query["MPEPTLDEKAK"]["missed_cleavage_counts"] == [1]
        assert by_query["MPEPTLDEKAK"]["uniqueness_class"] == "unique"
        assert by_query["SHADEQK"]["protein_groups"] == ["GROUP_SHARED"]
        assert by_query["SHADEQK"]["uniqueness_class"] == "shared"
        assert by_query["SHADEQK"]["audit_class"] == "protein_group_specific"


def test_peptide_mass_command_reports_mass_fragments_and_localization() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-mass",
                "PESTIDE",
                "--mod",
                "Phospho@3",
                "--charge",
                "2",
                "--include-neutral-losses",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "PES[Phospho]TIDE"
        assert payload["charge_state"]["charge"] == 2
        assert payload["fragment_ion_count"] > 0
        assert payload["localization"]["status"] == "advisory"


def test_peptide_mass_command_rejects_invalid_modification_assignment() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-mass",
                "PEPTIDE",
                "--mod",
                "Phospho@1",
            ],
        )

        assert result.exit_code != 0
        assert "not valid on residue" in result.output


def test_isotope_envelope_command_reports_formula_charge_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "isotope-envelope",
                "PEPTIDE",
                "--charge",
                "2",
                "--charge",
                "3",
                "--tsv-out",
                "isotopes.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "PEPTIDE"
        assert payload["elemental_composition"]["formula"] == "C34H53N7O15"
        assert payload["charges"] == [2, 3]
        assert payload["max_isotope_index"] == 5
        assert len(payload["envelopes"]) == 2
        assert len(payload["envelopes"][0]["peaks"]) == 6
        assert Path("isotopes.tsv").exists()
        assert (
            "canonical_notation\tcharge\tformula\tisotope_index\tmz\tprobability"
            in Path("isotopes.tsv").read_text()
        )


def test_fragment_ions_command_reports_a_b_y_ions_with_charge_spans_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "fragment-ions",
                "PESMTIDE",
                "--mod",
                "Phospho@3",
                "--charge",
                "1",
                "--charge",
                "2",
                "--charge",
                "3",
                "--include-neutral-losses",
                "--tsv-out",
                "fragments.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["counts_by_series"]["a"] > 0
        assert payload["counts_by_series"]["b"] > 0
        assert payload["counts_by_series"]["y"] > 0
        assert payload["counts_by_charge"]["1"] > 0
        assert payload["counts_by_charge"]["2"] > 0
        assert payload["counts_by_charge"]["3"] > 0
        assert payload["neutral_loss_count"] > 0
        assert any(
            ion["series"] == "a" and ion["span_start"] == 1 and ion["span_end"] == 3
            for ion in payload["ions"]
        )
        assert Path("fragments.tsv").exists()
        assert "series\tordinal\tcharge\tspan_start\tspan_end\tsequence" in Path(
            "fragments.tsv"
        ).read_text()


def test_peptide_properties_command_reports_filtering_metrics() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-properties",
                "LVVVVVVIKAKK",
                "--charge",
                "3",
                "--protease",
                "trypsin",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["charge"] == 3
        assert payload["protease"] == "trypsin"
        assert payload["length"] == 12
        assert payload["missed_cleavages"] == 2
        assert payload["flagged_problematic"] is True
        assert "high_hydrophobicity_proxy" in payload["problem_flags"]
        assert "high_missed_cleavages" in payload["problem_flags"]


def test_peptide_properties_command_supports_modifications_and_custom_protease() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-properties",
                "MPEPTIDE",
                "--mod",
                "Oxidation@1",
                "--custom-protease",
                "before=D;block_previous=P",
                "--custom-protease-name",
                "acidic",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["canonical_notation"] == "M[Oxidation]PEPTIDE"
        assert payload["protease"] == "acidic"
        assert payload["custom_protease"] == "before=D;block_previous=P"


def test_peptide_detectability_command_reports_score_tier_and_tsv() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "peptide-detectability",
                "AKTIDEK",
                "--charge",
                "2",
                "--protease",
                "trypsin",
                "--uniqueness-class",
                "unique",
                "--observed-psm-count",
                "5",
                "--tsv-out",
                "detectability.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["detectability_tier"] == "high"
        assert payload["top_tier_length_mass_eligible"] is True
        assert payload["custom_protease"] is None
        assert Path("detectability.tsv").exists()
        assert "detectability_score" in Path("detectability.tsv").read_text()


def test_precursor_mass_error_command_reports_summary_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("precursors.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tobserved_mz\tcharge",
                    "scan=1\tPEPTIDE\t400.0\t2",
                    "scan=2\tPEPM[Oxidation]IDE\t500.0\t2",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "precursor-mass-error",
                "precursors.tsv",
                "--summary-tsv-out",
                "summary.tsv",
                "--observations-tsv-out",
                "observations.tsv",
                "--ppm-distribution-tsv-out",
                "ppm.tsv",
                "--charge-distribution-tsv-out",
                "charge.tsv",
                "--isotope-distribution-tsv-out",
                "isotope.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["observation_count"] == 2
        assert payload["input_row_count"] == 2
        assert len(payload["observations"]) == 2
        assert Path("summary.tsv").exists()
        assert Path("observations.tsv").exists()
        assert Path("ppm.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("isotope.tsv").exists()


def test_modified_peptide_parse_command_normalizes_engine_dialects() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "_(Acetyl (Protein N-term))M(Oxidation (M))PEPTIDE_",
                "--dialect",
                "maxquant",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect"] == "maxquant"
        assert payload["residue_sequence"] == "MPEPTIDE"
        assert (
            payload["canonical_notation"]
            == "[Acetyl@protein-n-term]-M[Oxidation]PEPTIDE"
        )
        assert payload["at_protein_n_term"] is True


def test_modified_peptide_parse_command_distinguishes_lysine_acetylation() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "_PEPK(Acetyl (K))IDE_",
                "--dialect",
                "maxquant",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect"] == "maxquant"
        assert payload["canonical_notation"] == "PEPK[AcetylLys]IDE"
        assert payload["modified_peptide_record"]["modification_names"] == [
            "AcetylLys"
        ]


def test_modified_peptide_parse_command_rejects_malformed_engine_notation() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "modified-peptide-parse",
                "M[15.994915PEPTIDE",
                "--dialect",
                "comet",
            ],
        )

        assert result.exit_code != 0
        assert "unterminated bracket modification token" in result.output


def test_modification_resolve_command_reports_builtin_and_unknown_tokens() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        resolved = runner.invoke(
            cli,
            [
                "modification-resolve",
                "deamidation",
                "--residue",
                "N",
            ],
        )
        unknown = runner.invoke(
            cli,
            [
                "modification-resolve",
                "NoSuchModification",
                "--residue",
                "M",
            ],
        )

        assert resolved.exit_code == 0
        resolved_payload = json.loads(resolved.output)
        assert resolved_payload["resolved"] is True
        assert resolved_payload["modification_name"] == "Deamidated"
        assert resolved_payload["controlled_id"] == "UNIMOD:7"
        assert resolved_payload["source"] == "builtin"
        assert resolved_payload["residue_allowed"] is True

        assert unknown.exit_code == 0
        unknown_payload = json.loads(unknown.output)
        assert unknown_payload["resolved"] is False
        assert unknown_payload["source"] == "unknown"
        assert unknown_payload["issues"]


def test_modification_resolve_command_supports_custom_registry() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("registry.json").write_text(
            json.dumps(
                {
                    "document_schema": {
                        "created_by": "bijux-proteomics-core-tests",
                        "document_kind": "peptide_modification_registry",
                        "package_name": "bijux-proteomics-core",
                        "schema_version": "1.0.0",
                        "status": "generated",
                    },
                    "static_modifications": [],
                    "variable_modifications": [
                        {
                            "application": "variable",
                            "controlled_id": "CUSTOM:LYSTAG",
                            "mass_delta_average": 114.1,
                            "mass_delta_monoisotopic": 114.042927,
                            "max_occurrences": 1,
                            "name": "LysTag",
                            "neutral_losses": [],
                            "position": "anywhere",
                            "residues": ["K"],
                        }
                    ],
                }
            )
        )

        result = runner.invoke(
            cli,
            [
                "modification-resolve",
                "CUSTOM:LYSTAG",
                "--residue",
                "K",
                "--registry",
                "registry.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["resolved"] is True
        assert payload["source"] == "registry"
        assert payload["modification_name"] == "LysTag"
        assert payload["controlled_id"] == "CUSTOM:LYSTAG"
        assert payload["residue_allowed"] is True


def test_psm_inspect_command_reports_summaries_and_writes_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "representative_results.tsv"
        shutil.copy(source, "results.tsv")

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "results.tsv",
                "--jsonl-out",
                "normalized.jsonl",
                "--tsv-out",
                "normalized.tsv",
                "--provenance-out",
                "provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 3
        assert payload["psm_summary"]["decoy_psms"] == 1
        assert payload["inspection"]["accepted_rows"] == 3
        assert payload["inspection"]["rejected_rows"] == 0
        assert Path("normalized.jsonl").exists()
        assert Path("normalized.tsv").exists()
        manifest = json.loads(Path("provenance.json").read_text())
        assert (
            manifest["document_schema"]["document_kind"]
            == "search_result_provenance_manifest"
        )


def test_psm_inspect_command_supports_canonical_schema_columns() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "generic_mapper_results.tsv",
                "--run-id-column",
                "run_name",
                "--spectrum-id-column",
                "scan_ref",
                "--peptide-column",
                "sequence_text",
                "--modified-peptide-column",
                "modified_sequence",
                "--charge-column",
                "z",
                "--score-column",
                "state_score",
                "--q-value-column",
                "qvalue",
                "--protein-refs-column",
                "accessions",
                "--decoy-label-column",
                "decoy_state",
                "--contaminant-label-column",
                "contaminant_state",
                "--tsv-out",
                "normalized.tsv",
            ],
        )

        assert result.exit_code == 0
        normalized_tsv = Path("normalized.tsv").read_text(encoding="utf-8")
        assert "run_id" in normalized_tsv
        assert "peptide_sequence" in normalized_tsv
        assert "modified_peptide" in normalized_tsv
        assert "contaminant_flag" in normalized_tsv
        assert "PES[Phospho]TIDE" in normalized_tsv


def test_psm_inspect_command_reports_quality_distributions_and_writes_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("inspection.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins",
                    "scan=1001\tPEPTIDE\t2\t55.0\t0.005\tP12345",
                    "scan=1002\tAKTIDEK\t3\t44.0\t0.02\tP12345",
                    "scan=1003\tLVVVVVVIKAKK\t2\t31.0\t0.08\tP12345",
                    "scan=1004\tPEPTIDER\tbad\t20.0\t0.2\tP12345",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "inspection.tsv",
                "--summary-tsv-out",
                "inspection.summary.tsv",
                "--score-distribution-tsv-out",
                "inspection.score.tsv",
                "--q-value-distribution-tsv-out",
                "inspection.qvalue.tsv",
                "--charge-distribution-tsv-out",
                "inspection.charge.tsv",
                "--peptide-length-distribution-tsv-out",
                "inspection.length.tsv",
                "--missed-cleavage-distribution-tsv-out",
                "inspection.missed.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["inspection"]["total_rows"] == 4
        assert payload["inspection"]["accepted_rows"] == 3
        assert payload["inspection"]["rejected_rows"] == 1
        assert payload["inspection"]["protease"] == "trypsin"
        assert Path("inspection.summary.tsv").exists()
        assert Path("inspection.score.tsv").exists()
        assert Path("inspection.qvalue.tsv").exists()
        assert Path("inspection.charge.tsv").exists()
        assert Path("inspection.length.tsv").exists()
        assert Path("inspection.missed.tsv").exists()
        assert "0\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")
        assert "1\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")
        assert "2\t1" in Path("inspection.missed.tsv").read_text(encoding="utf-8")


def test_fdr_command_filters_by_threshold_and_writes_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--jsonl-out",
                "accepted.jsonl",
                "--provenance-out",
                "fdr.provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.5
        assert payload["accepted_psms"] == 3
        assert Path("accepted.jsonl").exists()
        manifest = json.loads(Path("fdr.provenance.json").read_text())
        assert manifest["fdr_policy"]["threshold"] == 0.5


def test_fdr_command_writes_ranked_summary_and_entry_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--summary-tsv-out",
                "fdr.summary.tsv",
                "--entries-tsv-out",
                "fdr.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["fdr_report"]["total_psm_count"] == 5
        assert payload["fdr_report"]["accepted_psm_count"] == 3
        assert payload["score_separation"]["summary"]["warning_tier"] == "unstable"
        assert payload["fdr_unstable"] is True
        assert payload["fdr_reproducibility_hash"]
        assert Path("fdr.summary.tsv").exists()
        assert Path("fdr.entries.tsv").exists()
        summary_tsv = Path("fdr.summary.tsv").read_text(encoding="utf-8")
        entries_tsv = Path("fdr.entries.tsv").read_text(encoding="utf-8")
        assert summary_tsv.startswith(
            "score_orientation\ttie_handling\tthreshold\ttotal_psm_count"
        )
        assert "reproducibility_hash" in summary_tsv
        assert entries_tsv.startswith(
            "rank\ttie_group_rank\ttie_group_size\tspectrum_id\tcanonical_peptide"
        )
        assert "\t0.5\ttrue\n" in entries_tsv


def test_fdr_command_marks_unstable_score_separation_and_writes_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "psm" / "fdr_unstable_results.tsv"
        shutil.copy(source, "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--score-separation-summary-tsv-out",
                "score_separation.summary.tsv",
                "--score-separation-bins-tsv-out",
                "score_separation.bins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["fdr_unstable"] is True
        assert payload["score_separation"]["summary"]["warning_tier"] == "unstable"
        assert payload["score_separation"]["summary"]["overlap_metric"] == 0.75
        assert Path("score_separation.summary.tsv").exists()
        assert Path("score_separation.bins.tsv").exists()
        assert "warning_tier\tfdr_unstable" in Path(
            "score_separation.summary.tsv"
        ).read_text(encoding="utf-8")
        assert Path("score_separation.bins.tsv").read_text(
            encoding="utf-8"
        ).startswith(
            "bin_lower\tbin_upper\ttarget_count\tdecoy_count\tmixed_count\tunknown_count"
        )


def test_fdr_command_preserves_imported_pep_and_writes_error_rate_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "psm" / "pep_results.tsv", "pep_results.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "pep_results.tsv",
                "--threshold",
                "0.5",
                "--pep-column",
                "pep",
                "--error-rate-summary-tsv-out",
                "error_rate.summary.tsv",
                "--error-rate-entries-tsv-out",
                "error_rate.entries.tsv",
                "--tsv-out",
                "accepted.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["error_rate_annotation"]["summary"]["imported_pep_count"] == 3
        assert payload["error_rate_annotation"]["summary"]["computed_local_fdr_count"] == 0
        assert Path("error_rate.summary.tsv").exists()
        assert Path("error_rate.entries.tsv").exists()
        assert "imported_pep_count\tcomputed_local_fdr_count" in Path(
            "error_rate.summary.tsv"
        ).read_text(encoding="utf-8")
        entries_text = Path("error_rate.entries.tsv").read_text(encoding="utf-8")
        accepted_text = Path("accepted.tsv").read_text(encoding="utf-8")
        assert "posterior_error_probability\tlocal_fdr\terror_rate_provenance" in entries_text
        assert "\t0.002\t\timported_pep\n" in entries_text
        assert "posterior_error_probability\tlocal_fdr\terror_rate_provenance" in accepted_text
        assert "\t0.008\t\timported_pep\tQ11111" in accepted_text


def test_fdr_command_computes_local_fdr_when_pep_is_absent() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "psm" / "fdr_results.tsv", "fdr.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr.tsv",
                "--threshold",
                "0.5",
                "--error-rate-summary-tsv-out",
                "error_rate.summary.tsv",
                "--error-rate-entries-tsv-out",
                "error_rate.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["error_rate_annotation"]["summary"]["imported_pep_count"] == 0
        assert payload["error_rate_annotation"]["summary"]["computed_local_fdr_count"] == 5
        entries_text = Path("error_rate.entries.tsv").read_text(encoding="utf-8")
        assert "\t\t1.0\tcomputed_local_fdr\n" in entries_text


def test_fdr_reference_check_command_writes_summary_and_entry_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "identification" / "target_decoy_reference_cases.json",
            "reference_cases.json",
        )

        result = runner.invoke(
            cli,
            [
                "fdr-reference-check",
                "reference_cases.json",
                "--summary-tsv-out",
                "reference.summary.tsv",
                "--entries-tsv-out",
                "reference.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["valid"] is True
        assert payload["case_count"] == 2
        assert payload["failed_entry_count"] == 0
        assert Path("reference.summary.tsv").exists()
        assert Path("reference.entries.tsv").exists()
        assert "concatenated_higher_better_reference" in Path(
            "reference.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "scan=5005" in Path("reference.entries.tsv").read_text(encoding="utf-8")


def test_fdr_levels_command_reports_threshold_counts_and_contaminants() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("levels.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tcharge\tscore\tproteins",
                    "scan=1001\tPEPTIDE\t2\t100.0\tP11111",
                    "scan=1002\tAKTIDEK\t2\t95.0\tCON__KERATIN_HUMAN",
                    "scan=1003\tDECOYPEP\t2\t90.0\tDECOY_P99999",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "fdr-levels",
                "levels.tsv",
                "--summary-tsv-out",
                "levels.summary.tsv",
                "--entries-tsv-out",
                "levels.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["thresholds"] == [0.01, 0.05, 0.1]
        assert payload["accepted_rows"] == 3
        summary_rows = payload["summaries"]
        psm_one_percent = next(
            row
            for row in summary_rows
            if row["threshold"] == 0.01 and row["evidence_level"] == "psm"
        )
        assert psm_one_percent["accepted_count"] == 2
        assert psm_one_percent["accepted_contaminant_count"] == 1
        assert psm_one_percent["total_decoy_count"] == 1
        assert Path("levels.summary.tsv").exists()
        assert Path("levels.entries.tsv").exists()
        assert "0.01\tpsm\t3\t2\t1\t0\t0\t1\t2\t2\t0\t0\t0\t1" in Path(
            "levels.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "0.05\tprotein\tCON__KERATIN_HUMAN" in Path(
            "levels.entries.tsv"
        ).read_text(encoding="utf-8")


def test_picked_protein_fdr_command_reports_pairs_groups_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "grouped_picked_fdr_edge_cases.tsv",
            "picked.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "picked-protein-fdr",
                "picked.tsv",
                "--summary-tsv-out",
                "picked.summary.tsv",
                "--entries-tsv-out",
                "picked.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["thresholds"] == [0.01, 0.05, 0.1]
        assert payload["accepted_rows"] == 10
        summary_rows = payload["summaries"]
        threshold_tenth = next(row for row in summary_rows if row["threshold"] == 0.1)
        assert threshold_tenth["total_count"] == 5
        assert threshold_tenth["grouped_protein_count"] == 2
        assert threshold_tenth["accepted_count"] == 4
        entries = payload["entries"]
        picked_p22222 = next(row for row in entries if row["protein_ref"] == "P22222")
        assert picked_p22222["pair_id"] == "picked:P22222"
        assert picked_p22222["target_ref"] == "P22222"
        assert picked_p22222["decoy_ref"] == "DECOY_P22222"
        assert picked_p22222["partner_ref"] == "DECOY_P22222"
        assert picked_p22222["protein_group_ids"]
        assert Path("picked.summary.tsv").exists()
        assert Path("picked.entries.tsv").exists()
        assert "0.1\t5\t4\t1\t0\t2\t4\t4\t0\t0\t2" in Path(
            "picked.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "picked:P22222\tP22222\tP22222\tDECOY_P22222\tP22222\tDECOY_P22222"
            in Path("picked.entries.tsv").read_text(encoding="utf-8")
        )


def test_protein_groups_command_reports_leading_proteins_and_group_table() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-groups",
                "protein_inference_results.tsv",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_groups.summary.tsv",
                "--group-tsv-out",
                "protein_groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.05
        assert payload["grouped_rows"] == 4
        assert payload["summary"]["total_groups"] == 3
        assert payload["summary"]["ambiguous_group_count"] == 1
        ambiguous = next(
            entry
            for entry in payload["groups"]
            if entry["protein_refs"] == ["P22222", "P44444"]
        )
        assert ambiguous["leading_protein"] == "P22222"
        assert ambiguous["leading_rationale"] == "lexicographic_tiebreak"
        assert ambiguous["shared_peptides"] == ["GLYGLYK", "SHAREDK"]
        assert Path("protein_groups.summary.tsv").exists()
        assert Path("protein_groups.tsv").exists()
        assert "ambiguous_group_count\t1" in Path(
            "protein_groups.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P22222\tlexicographic_tiebreak\tP22222;P44444\tGLYGLYK;SHAREDK\t\tGLYGLYK;SHAREDK"
            in Path("protein_groups.tsv").read_text(encoding="utf-8")
        )


def test_protein_ambiguity_command_reports_ambiguous_groups_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_ambiguity_cases.tsv",
            "protein_ambiguity_cases.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-ambiguity",
                "protein_ambiguity_cases.tsv",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_ambiguity.summary.tsv",
                "--ambiguity-tsv-out",
                "protein_ambiguity.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["threshold"] == 0.05
        assert payload["accepted_rows"] == 4
        assert payload["grouped_rows"] == 4
        assert payload["ambiguity_rows"] == 3
        assert payload["summary"]["total_ambiguity_groups"] == 3
        assert payload["summary"]["indistinguishable_group_count"] == 1
        mixed = next(
            entry
            for entry in payload["entries"]
            if entry["protein_refs"] == ["P10001", "P20002"]
        )
        assert mixed["ambiguity_reason"] == "mixed"
        assert mixed["outside_group_proteins"] == ["P30003"]
        external = next(
            entry for entry in payload["entries"] if entry["protein_refs"] == ["P30003"]
        )
        assert external["ambiguity_reason"] == "external_shared_peptides"
        assert external["unique_peptides"] == ["UNIQUEB"]
        assert Path("protein_ambiguity.summary.tsv").exists()
        assert Path("protein_ambiguity.tsv").exists()
        assert "total_ambiguity_groups\t3" in Path(
            "protein_ambiguity.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P10001\tP10001;P20002\tP10001;P20002\tSHAREDX;SHAREDY\t\tP30003\tmixed"
            in Path("protein_ambiguity.tsv").read_text(encoding="utf-8")
        )


def test_protein_inference_benchmarks_command_emits_catalog_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "protein-inference-benchmarks",
                "--picked-threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_inference_benchmarks.summary.tsv",
                "--scenarios-tsv-out",
                "protein_inference_benchmarks.scenarios.tsv",
                "--assessments-tsv-out",
                "protein_inference_benchmarks.assessments.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["picked_threshold"] == 0.05
        assert payload["scenario_count"] == 8
        assert payload["homolog_family_scenario_count"] == 1
        assert payload["contaminant_scenario_count"] == 1
        assert payload["all_decoy_scenario_count"] == 1
        assert payload["all_target_scenario_count"] == 1
        assert payload["tied_score_scenario_count"] == 1
        assert payload["missing_fasta_scenario_count"] == 1
        assert payload["hidden_ambiguity_scenario_count"] == 0
        assert payload["reports"][0]["method_assessments"]
        assert Path("protein_inference_benchmarks.summary.tsv").exists()
        assert Path("protein_inference_benchmarks.scenarios.tsv").exists()
        assert Path("protein_inference_benchmarks.assessments.tsv").exists()
        assert "homolog_family_scenario_count\t1" in Path(
            "protein_inference_benchmarks.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "tied-score-ambiguity" in Path(
            "protein_inference_benchmarks.scenarios.tsv"
        ).read_text(encoding="utf-8")
        assert "selected_missing_fasta_proteins" in Path(
            "protein_inference_benchmarks.assessments.tsv"
        ).read_text(encoding="utf-8")


def test_protein_coverage_command_reports_regions_and_shared_peptides() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        psm_fixture_dir = FIXTURE_ROOT / "psm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            psm_fixture_dir / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )
        shutil.copy(
            fasta_fixture_dir / "protein_inference.fasta",
            "protein_inference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "protein-coverage",
                "protein_inference_results.tsv",
                "--fasta",
                "protein_inference.fasta",
                "--threshold",
                "0.05",
                "--summary-tsv-out",
                "protein_coverage.summary.tsv",
                "--coverage-tsv-out",
                "protein_coverage.tsv",
                "--regions-tsv-out",
                "protein_coverage.regions.tsv",
                "--uncovered-tsv-out",
                "protein_coverage.uncovered.tsv",
                "--peptide-coordinate-tsv-out",
                "protein_coverage.coordinates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 4
        assert payload["summary"]["total_proteins"] == 4
        assert payload["summary"]["proteins_with_shared_peptides"] == 3
        p11111 = next(
            entry for entry in payload["entries"] if entry["protein_ref"] == "P11111"
        )
        assert p11111["covered_ranges"] == [[2, 9], [13, 19]]
        assert p11111["uncovered_ranges"] == [[1, 1], [10, 12], [20, 21]]
        assert p11111["unique_peptides"] == ["PEPTIDEK"]
        assert p11111["shared_peptides"] == ["SHAREDK"]
        assert payload["regions"][0]["protein_ref"] == "P11111"
        assert payload["uncovered_regions"][0]["protein_ref"] == "P11111"
        assert payload["peptide_coordinates"][0]["protein_ref"] == "P11111"
        assert Path("protein_coverage.summary.tsv").exists()
        assert Path("protein_coverage.tsv").exists()
        assert Path("protein_coverage.regions.tsv").exists()
        assert Path("protein_coverage.uncovered.tsv").exists()
        assert Path("protein_coverage.coordinates.tsv").exists()
        assert "proteins_with_shared_peptides\t3" in Path(
            "protein_coverage.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t21\t15\t0.7142857142857143\t2-9;13-19" in Path(
            "protein_coverage.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t2\t13\t19\t7" in Path("protein_coverage.regions.tsv").read_text(
            encoding="utf-8"
        )
        assert "P11111\t1\t1\t1\t1" in Path(
            "protein_coverage.uncovered.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\tPEPTIDEK\tPEPTIDEK\tmatched\t1\t2\t9" in Path(
            "protein_coverage.coordinates.tsv"
        ).read_text(encoding="utf-8")


def test_protein_coverage_plot_command_emits_positions_svg_and_html() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("protein_plot.tsv").write_text(
            "\n".join(
                (
                    "spectrum_id\tpeptide\tmodified_peptide\tcharge\tscore\tintensity\tq_value\tproteins",
                    "scan=1\tPEPTIDEK\tPEPTIDEK\t2\t90.0\t1000\t0.005\tP11111",
                    "scan=2\tACDMK\tACDM[Oxidation]K\t2\t70.0\t500\t0.02\tP11111;P22222",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("protein_plot.fasta").write_text(
            "\n".join(
                (
                    ">sp|P11111|PROT1 Example protein 1 OS=Homo sapiens GN=PROT1",
                    "MPEPTIDEKAAACDMKGG",
                    ">sp|P22222|PROT2 Example protein 2 OS=Homo sapiens GN=PROT2",
                    "QQACDMKRR",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "protein-coverage-plot",
                "protein_plot.tsv",
                "--fasta",
                "protein_plot.fasta",
                "--modified-peptide-column",
                "modified_peptide",
                "--intensity-column",
                "intensity",
                "--positions-tsv-out",
                "protein_plot.positions.tsv",
                "--svg-out",
                "protein_plot.svg",
                "--html-out",
                "protein_plot.html",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 2
        assert payload["summary"]["total_position_rows"] == 3
        assert payload["summary"]["modified_position_count"] == 2
        assert payload["summary"]["intensity_position_count"] == 3
        modified = next(
            entry
            for track in payload["tracks"]
            for entry in track["positions"]
            if entry["canonical_peptide"] == "ACDM[Oxidation]K"
            and entry["protein_ref"] == "P11111"
        )
        assert modified["start_residue"] == 12
        assert modified["end_residue"] == 16
        assert modified["confidence_label"] == "medium"
        assert modified["peptide_q_value"] == 0.02
        assert modified["best_intensity"] == 500.0
        assert Path("protein_plot.positions.tsv").exists()
        assert Path("protein_plot.svg").read_text(encoding="utf-8").startswith("<svg")
        assert (
            Path("protein_plot.html").read_text(encoding="utf-8").startswith("<html>")
        )
        assert "ACDM[Oxidation]K" in Path("protein_plot.positions.tsv").read_text(
            encoding="utf-8"
        )


def test_protein_parsimony_command_reports_selected_set_and_ambiguities() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_parsimony_variants.tsv",
            "protein_parsimony_variants.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-parsimony",
                "protein_parsimony_variants.tsv",
                "--threshold",
                "0.05",
                "--variant",
                "greedy_coverage",
                "--review-variant",
                "greedy_coverage",
                "--review-variant",
                "unique_evidence_priority",
                "--summary-tsv-out",
                "protein_parsimony.summary.tsv",
                "--protein-tsv-out",
                "protein_parsimony.proteins.tsv",
                "--ambiguity-tsv-out",
                "protein_parsimony.ambiguities.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["variant"] == "greedy_coverage"
        assert payload["summary"]["selected_protein_count"] == 2
        assert payload["summary"]["unresolved_ambiguity_count"] == 2
        assert payload["unexplained_peptides"] == []
        assert payload["selected_proteins"][0]["protein_ref"] == "P10001"
        assert payload["selected_proteins"][1]["protein_ref"] == "P20002"
        bravoq = next(
            entry
            for entry in payload["unresolved_ambiguities"]
            if entry["subject_id"] == "BRAVOK"
        )
        assert bravoq["candidate_proteins"] == ["P10001", "P20002"]
        assert Path("protein_parsimony.summary.tsv").exists()
        assert Path("protein_parsimony.proteins.tsv").exists()
        assert Path("protein_parsimony.ambiguities.tsv").exists()
        assert "selected_protein_count\t2" in Path(
            "protein_parsimony.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "greedy_coverage\t1\tP10001\tpg-001\tP10001\tALPHAK;BRAVOK;CHARLIEK;DELTAK"
            in Path("protein_parsimony.proteins.tsv").read_text(encoding="utf-8")
        )
        assert "BRAVOK\tpeptide_assignment\tP10001;P20002" in Path(
            "protein_parsimony.ambiguities.tsv"
        ).read_text(encoding="utf-8")


def test_peptide_evidence_command_reports_classes_and_tags() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "peptide_evidence_classes.tsv",
            "peptide_evidence_classes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-evidence",
                "peptide_evidence_classes.tsv",
                "--threshold",
                "0.05",
                "--strong-q-value",
                "0.01",
                "--summary-tsv-out",
                "peptide_evidence.summary.tsv",
                "--entries-tsv-out",
                "peptide_evidence.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_peptides"] == 8
        assert payload["summary"]["strong_count"] == 1
        assert payload["summary"]["moderate_count"] == 1
        assert payload["summary"]["weak_count"] == 2
        assert payload["summary"]["shared_count"] == 1
        assert payload["summary"]["ambiguous_count"] == 1
        assert payload["summary"]["modified_count"] == 1
        assert payload["summary"]["contaminant_count"] == 1
        assert payload["summary"]["decoy_count"] == 1
        by_peptide = {entry["canonical_peptide"]: entry for entry in payload["entries"]}
        assert by_peptide["STRONGK"]["primary_class"] == "strong"
        assert by_peptide["SHAREDFINEK"]["primary_class"] == "shared"
        assert by_peptide["SHAREDK"]["primary_class"] == "weak"
        assert "shared" in by_peptide["SHAREDK"]["tags"]
        assert "modified" in by_peptide["ACDM[Oxidation]K"]["tags"]
        assert by_peptide["AMBIGK"]["primary_class"] == "ambiguous"
        assert by_peptide["CONTAMK"]["primary_class"] == "contaminant"
        assert by_peptide["DECOYSEQ"]["primary_class"] == "decoy"
        assert Path("peptide_evidence.summary.tsv").exists()
        assert Path("peptide_evidence.entries.tsv").exists()
        assert "strong_count\t1" in Path("peptide_evidence.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "CONTAMK\tCONTAMK\tcontaminant\tunique;contaminant" in Path(
            "peptide_evidence.entries.tsv"
        ).read_text(encoding="utf-8")


def test_protein_evidence_command_reports_tiers_and_downgrade_reasons() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "protein_evidence_cases.tsv",
            "protein_evidence_cases.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "protein_evidence.design.tsv",
            "protein_evidence.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-evidence",
                "protein_evidence_cases.tsv",
                "--design-tsv",
                "protein_evidence.design.tsv",
                "--run-id-column",
                "run_id",
                "--summary-tsv-out",
                "protein_evidence.summary.tsv",
                "--entries-tsv-out",
                "protein_evidence.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_groups"] == 6
        assert payload["summary"]["high_confidence_count"] == 1
        assert payload["summary"]["moderate_count"] == 1
        assert payload["summary"]["weak_count"] == 1
        assert payload["summary"]["ambiguous_count"] == 1
        assert payload["summary"]["contaminant_count"] == 1
        assert payload["summary"]["decoy_count"] == 1
        by_protein = {
            entry["representative_protein"]: entry for entry in payload["entries"]
        }
        assert by_protein["P11111"]["evidence_tier"] == "high_confidence"
        assert by_protein["P22222"]["evidence_tier"] == "moderate"
        assert by_protein["P22222"]["downgrade_reasons"] == ["single_run_only"]
        assert by_protein["P33333"]["evidence_tier"] == "ambiguous"
        assert by_protein["P33333"]["downgrade_reasons"] == ["shared_peptide_only"]
        assert by_protein["P66666"]["evidence_tier"] == "weak"
        assert Path("protein_evidence.summary.tsv").exists()
        assert Path("protein_evidence.entries.tsv").exists()
        assert "shared_peptide_only_count\t1" in Path(
            "protein_evidence.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "\tambiguous\tshared_peptide_only\t" in Path(
            "protein_evidence.entries.tsv"
        ).read_text(encoding="utf-8")


def test_cross_run_reproducibility_command_reports_detection_consistency() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "cross_run_reproducibility.tsv",
            "cross_run_reproducibility.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "cross_run_reproducibility.design.tsv",
            "cross_run_reproducibility.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "cross-run-reproducibility",
                "cross_run_reproducibility.tsv",
                "--design-tsv",
                "cross_run_reproducibility.design.tsv",
                "--run-id-column",
                "run_id",
                "--summary-tsv-out",
                "cross_run_reproducibility.summary.tsv",
                "--entries-tsv-out",
                "cross_run_reproducibility.entries.tsv",
                "--exploratory-entity",
                "PEPC",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["total_entries"] == 4
        assert payload["summary"]["condition_specific_count"] == 1
        assert payload["summary"]["single_run_only_count"] == 1
        assert payload["summary"]["exploratory_count"] == 1
        by_entity = {entry["entity_id"]: entry for entry in payload["entries"]}
        assert by_entity["PEPA"]["reproducibility_class"] == "condition_specific"
        assert by_entity["PEPB"]["reproducibility_class"] == "single_run_only"
        assert by_entity["PEPC"]["reproducibility_class"] == "exploratory"
        assert by_entity["PEPD"]["reproducibility_class"] == "reproducible"
        assert by_entity["PEPD"]["condition_specificity"] == 0.5
        assert Path("cross_run_reproducibility.summary.tsv").exists()
        assert Path("cross_run_reproducibility.entries.tsv").exists()
        assert "condition_specific_count\t1" in Path(
            "cross_run_reproducibility.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPB\t1\t4\t0.25" in Path(
            "cross_run_reproducibility.entries.tsv"
        ).read_text(encoding="utf-8")


def test_spectrum_stats_command_reports_collection_summary_and_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "multi.mgf"
        shutil.copy(source, "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-stats",
                "multi.mgf",
                "--provenance-out",
                "multi.provenance.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["spectrum_count"] == 2
        assert payload["metrics"][0]["peak_count"] >= 1
        provenance = json.loads(Path("multi.provenance.json").read_text())
        assert (
            provenance["document_schema"]["document_kind"]
            == "spectrum_provenance_manifest"
        )


def test_spectrum_parse_command_reports_rejections_and_streaming_profile() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "malformed.mgf", "malformed.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-parse",
                "malformed.mgf",
                "--chunk-size",
                "2",
                "--accepted-jsonl-out",
                "accepted.jsonl",
                "--rejected-json-out",
                "rejected.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["parse_report"]["total_blocks"] == 2
        assert len(payload["parse_report"]["accepted_spectra"]) == 0
        assert len(payload["parse_report"]["rejected_blocks"]) == 2
        assert payload["streaming_profile"]["chunk_size"] == 2
        assert payload["streaming_profile"]["spectrum_count"] == 0
        assert Path("accepted.jsonl").exists()
        assert Path("rejected.json").exists()
        assert json.loads(Path("rejected.json").read_text())[0]["issues"]


def test_spectrum_parse_command_exports_accepted_spectra_details() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-parse",
                "multi.mgf",
                "--chunk-size",
                "1",
                "--accepted-jsonl-out",
                "accepted.jsonl",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["spectrum_count"] == 2
        assert payload["streaming_profile"]["chunk_count"] == 2
        accepted_rows = Path("accepted.jsonl").read_text().strip().splitlines()
        assert len(accepted_rows) == 2
        first_row = json.loads(accepted_rows[0])
        assert first_row["precursor_mz"] > 0.0
        assert first_row["peaks"]


def test_spectrum_summary_command_reports_mgf_tables_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-summary",
                "multi.mgf",
                "--summary-tsv-out",
                "summary.tsv",
                "--charge-tsv-out",
                "charge.tsv",
                "--precursor-tsv-out",
                "precursor.tsv",
                "--peak-count-tsv-out",
                "peak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mgf"
        assert payload["ms_level_policy"] == "mgf_assumed_ms2"
        assert payload["ms2_spectrum_count"] == 2
        assert Path("summary.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("precursor.tsv").exists()
        assert Path("peak.tsv").exists()


def test_spectrum_qc_command_reports_mgf_run_qc_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        spectra = (
            SpectrumModel(
                spectrum_id="scan=1",
                precursor_mz=500.2,
                precursor_intensity=500.0,
                precursor_charge=2,
                retention_time_seconds=15.0,
                peaks=(
                    SpectrumPeak(mz=100.0, intensity=50.0),
                    SpectrumPeak(mz=150.0, intensity=40.0),
                    SpectrumPeak(mz=200.0, intensity=30.0),
                ),
            ),
            SpectrumModel(
                spectrum_id="scan=2",
                precursor_mz=600.2,
                precursor_intensity=5000.0,
                precursor_charge=3,
                retention_time_seconds=75.0,
                peaks=(SpectrumPeak(mz=250.0, intensity=15.0),),
            ),
        )
        Path("qc.mgf").write_text(render_mgf(spectra), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-qc",
                "qc.mgf",
                "--summary-tsv-out",
                "summary.tsv",
                "--msms-tsv-out",
                "msms.tsv",
                "--tic-tsv-out",
                "tic.tsv",
                "--bpc-tsv-out",
                "bpc.tsv",
                "--charge-tsv-out",
                "charge.tsv",
                "--precursor-intensity-tsv-out",
                "precursor.tsv",
                "--flagged-tsv-out",
                "flagged.tsv",
                "--spectrum-qc-tsv-out",
                "spectrum_qc.tsv",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mgf"
        assert payload["chromatogram_source"] == "spectrum_derived"
        assert payload["precursor_intensity_observation_count"] == 2
        assert payload["noisy_spectrum_count"] == 1
        assert Path("summary.tsv").exists()
        assert Path("msms.tsv").exists()
        assert Path("tic.tsv").exists()
        assert Path("bpc.tsv").exists()
        assert Path("charge.tsv").exists()
        assert Path("precursor.tsv").exists()
        assert Path("flagged.tsv").exists()
        assert Path("spectrum_qc.tsv").exists()
        assert Path("plot.json").exists()
        assert "quality_tier" in Path("spectrum_qc.tsv").read_text()


def test_spectrum_qc_command_prefers_reported_mzml_chromatograms() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "spectrum-qc",
                "practical_review.mzml",
                "--kind",
                "mzml",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mzml"
        assert payload["chromatogram_source"] == "reported_mzml_chromatograms"
        assert payload["precursor_intensity_observation_count"] == 2
        assert len(payload["tic_trace"]) == 3
        assert Path("plot.json").exists()


def test_spectrum_annotate_command_writes_annotation_and_plot_payload() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "simple.mgf"
        shutil.copy(source, "simple.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-annotate",
                "simple.mgf",
                "--peptide",
                "PEPTIDE",
                "--tsv-out",
                "annotation.tsv",
                "--unmatched-peak-tsv-out",
                "unmatched.tsv",
                "--plot-out",
                "plot.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["annotation"]["document_schema"]["document_kind"]
            == "spectrum_annotation"
        )
        assert (
            payload["peak_matching_report"]["document_schema"]["document_kind"]
            == "spectrum_peak_matching_report"
        )
        assert payload["annotation"]["matches"]
        assert payload["annotation"]["matched_peak_count"] > 0
        assert payload["annotation"]["explained_intensity_fraction"] > 0.0
        assert payload["peak_matching_report"]["matched_peak_count"] > 0
        assert Path("annotation.tsv").exists()
        assert Path("unmatched.tsv").exists()
        assert Path("plot.json").exists()
        assert (
            Path("unmatched.tsv").read_text().splitlines()[0]
            == "spectrum_id\tpeptide\ttolerance_mode\tmz\tintensity"
        )


def test_spectrum_annotate_command_supports_ppm_tolerance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = FIXTURE_ROOT / "spectra" / "simple.mgf"
        shutil.copy(source, "simple.mgf")

        result = runner.invoke(
            cli,
            [
                "spectrum-annotate",
                "simple.mgf",
                "--peptide",
                "PEPTIDE",
                "--tolerance-ppm",
                "20",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["annotation"]["tolerance_unit"] == "ppm"
        assert payload["annotation"]["tolerance_da"] is None
        assert payload["annotation"]["tolerance_ppm"] == 20.0
        assert payload["peak_matching_report"]["tolerance_mode"] == "ppm"
        assert payload["peak_matching_report"]["tolerance_da"] is None
        assert payload["peak_matching_report"]["tolerance_ppm"] == 20.0


def test_spectrum_similarity_command_reports_pairwise_comparison() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "query",
            ((100.01, 1.0), (150.01, 0.9), (200.01, 0.7)),
        )
        reference = _similarity_spectrum(
            "reference",
            ((100.0, 1.0), (150.0, 0.9), (200.0, 0.7)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        Path("reference.mgf").write_text(render_mgf((reference,)), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-similarity",
                "query.mgf",
                "reference.mgf",
                "--query-spectrum-id",
                "query",
                "--reference-spectrum-id",
                "reference",
                "--tolerance-da",
                "0.02",
                "--tsv-out",
                "similarity.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["comparison"]["classification"] == "duplicate_like"
        assert payload["comparison"]["score"] > 0.99
        assert (
            payload["library_report"]["matches"][0]["reference_spectrum_id"]
            == "reference"
        )
        assert Path("similarity.tsv").exists()


def test_spectrum_similarity_command_supports_library_ranking_with_binning() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "query",
            ((100.21, 1.0), (150.19, 0.8), (200.18, 0.6)),
        )
        best = _similarity_spectrum(
            "best-match",
            ((100.0, 1.0), (150.0, 0.8), (200.0, 0.6)),
        )
        other = _similarity_spectrum(
            "other-match",
            ((400.0, 1.0), (450.0, 0.8), (500.0, 0.6)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        Path("library.mgf").write_text(render_mgf((other, best)), encoding="utf-8")

        result = runner.invoke(
            cli,
            [
                "spectrum-similarity",
                "query.mgf",
                "library.mgf",
                "--query-spectrum-id",
                "query",
                "--bin-width-da",
                "1.0",
                "--max-matches",
                "2",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["comparison"] is None
        assert payload["library_report"]["parameters"]["matching_mode"] == "binned"
        assert (
            payload["library_report"]["matches"][0]["reference_spectrum_id"]
            == "best-match"
        )
        assert (
            payload["library_report"]["matches"][0]["classification"]
            == "duplicate_like"
        )


def test_spectral_library_import_command_reports_msp_summary_and_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.msp", "review_library.msp"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-import",
                "review_library.msp",
                "--precursor-mz",
                "508.18",
                "--tolerance-da",
                "0.05",
                "--peptide",
                "PEPM[Oxidation]TIDE",
                "--summary-tsv-out",
                "summary.tsv",
                "--candidates-tsv-out",
                "candidates.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "msp"
        assert payload["summary"]["modified_entry_count"] == 1
        assert payload["candidates"]["candidate_count"] == 1
        assert (
            payload["candidates"]["matches"][0]["canonical_peptide"]
            == "PEPM[Oxidation]TIDE"
        )
        assert Path("summary.tsv").exists()
        assert Path("candidates.tsv").exists()


def test_spectral_library_import_command_supports_mgf_library_indexing() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.mgf", "review_library.mgf"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-import",
                "review_library.mgf",
                "--kind",
                "mgf",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "mgf"
        assert payload["index"]["entry_count"] == 2
        assert "PEPM[Oxidation]TIDE" in payload["index"]["peptide_index"]
        assert payload["candidates"] is None


def test_spectral_library_search_command_reports_ranked_decoy_aware_matches() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "library_search_query.mgf",
            "library_search_query.mgf",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "library_search_reference.msp",
            "library_search_reference.msp",
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-search",
                "library_search_query.mgf",
                "library_search_reference.msp",
                "--query-kind",
                "mgf",
                "--library-kind",
                "msp",
                "--precursor-tolerance-da",
                "0.03",
                "--tolerance-da",
                "0.02",
                "--tsv-out",
                "library_search.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "msp"
        assert payload["library_summary"]["decoy_entry_count"] == 1
        assert payload["search_report"]["search_strategy"] == "concatenated"
        assert payload["search_report"]["advisory_warning"] is None
        assert payload["warnings"] == []
        assert (
            payload["search_report"]["top_match_library_entry_id"] == "msp:1:PEPTIDE/2"
        )
        assert payload["search_report"]["matches"][0]["q_value"] == 0.0
        assert Path("library_search.tsv").exists()


def test_spectral_library_search_command_supports_mgf_library_search_without_decoys() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        query = _similarity_spectrum(
            "review-query",
            ((100.01, 1500.0), (250.01, 800.0)),
        )
        Path("query.mgf").write_text(render_mgf((query,)), encoding="utf-8")
        shutil.copy(
            FIXTURE_ROOT / "formats" / "review_library.mgf", "review_library.mgf"
        )

        result = runner.invoke(
            cli,
            [
                "spectral-library-search",
                "query.mgf",
                "review_library.mgf",
                "--library-kind",
                "mgf",
                "--tolerance-da",
                "0.02",
                "--max-matches",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["source_format"] == "mgf"
        assert payload["search_report"]["search_strategy"] == "no_decoy_advisory"
        assert payload["search_report"]["candidate_count"] == 1
        assert payload["search_report"]["top_match_canonical_peptide"] == "PEPTIDE"
        assert payload["search_report"]["top_match_q_value"] is None
        assert payload["search_report"]["advisory_warning"] == (
            "library search ran without decoy entries; q-values are withheld and this report is advisory only"
        )
        assert payload["warnings"] == [
            "library search ran without decoy entries; q-values are withheld and this report is advisory only"
        ]


def test_validate_command_supports_fasta_psm_mgf_and_mod_registry(
    fasta_fixture_dir: Path,
) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(
            FIXTURE_ROOT / "psm" / "representative_results.tsv",
            "results.tsv",
        )
        shutil.copy(FIXTURE_ROOT / "spectra" / "simple.mgf", "simple.mgf")
        shutil.copy(
            FIXTURE_ROOT / "modifications" / "valid_registry.json",
            "registry.json",
        )

        fasta_result = runner.invoke(
            cli, ["validate", "valid.fasta", "--kind", "fasta"]
        )
        psm_result = runner.invoke(cli, ["validate", "results.tsv", "--kind", "psm"])
        mgf_result = runner.invoke(cli, ["validate", "simple.mgf", "--kind", "mgf"])
        registry_result = runner.invoke(
            cli, ["validate", "registry.json", "--kind", "mod-registry"]
        )

        assert fasta_result.exit_code == 0
        assert json.loads(fasta_result.output)["valid"] is True
        assert psm_result.exit_code == 0
        assert json.loads(psm_result.output)["valid"] is True
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["valid"] is True
        assert registry_result.exit_code == 0
        assert (
            json.loads(registry_result.output)["summary"]["variable_modifications"] >= 1
        )


def test_summarize_command_supports_fasta_psm_and_mgf(fasta_fixture_dir: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(
            FIXTURE_ROOT / "psm" / "representative_results.tsv",
            "results.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_results.tsv",
            "contaminant_results.tsv",
        )
        shutil.copy(FIXTURE_ROOT / "spectra" / "multi.mgf", "multi.mgf")

        fasta_result = runner.invoke(
            cli, ["summarize", "valid.fasta", "--kind", "fasta"]
        )
        psm_result = runner.invoke(cli, ["summarize", "results.tsv", "--kind", "psm"])
        contaminant_psm_result = runner.invoke(
            cli, ["summarize", "contaminant_results.tsv", "--kind", "psm"]
        )
        mgf_result = runner.invoke(cli, ["summarize", "multi.mgf", "--kind", "mgf"])

        assert fasta_result.exit_code == 0
        fasta_payload = json.loads(fasta_result.output)
        assert fasta_payload["summary"]["total_records"] == 3
        assert fasta_payload["profile"]["summary"]["protein_count"] == 3
        assert fasta_payload["profile"]["summary"]["organism_annotated_count"] == 2
        assert fasta_payload["database_composition"]["target_count"] == 3
        assert fasta_payload["duplicate_accessions"] == []
        assert psm_result.exit_code == 0
        psm_payload = json.loads(psm_result.output)
        assert psm_payload["psm_summary"]["total_psms"] == 3
        assert psm_payload["inspection"]["accepted_rows"] == 3
        assert contaminant_psm_result.exit_code == 0
        contaminant_payload = json.loads(contaminant_psm_result.output)
        assert contaminant_payload["contaminant_report"]["contaminant_psm_count"] == 2
        assert contaminant_payload["inspection"]["accepted_rows"] == 3
        assert (
            contaminant_payload["contaminant_report"]["mixed_reference_psm_count"] == 1
        )
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["summary"]["spectrum_count"] == 2


def test_psm_contaminants_command_reports_contaminant_matches() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_results.tsv",
            "contaminant_results.tsv",
        )

        result = runner.invoke(
            cli,
            ["psm-contaminants", "contaminant_results.tsv"],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["contaminant_psm_count"] == 2
        assert payload["pure_contaminant_psm_count"] == 1
        assert payload["mixed_reference_psm_count"] == 1
        assert payload["contaminant_protein_counts"] == {
            "CON__K1C10_HUMAN": 1,
            "CON__TRYP_PIG": 1,
        }


def test_psm_contaminants_command_exports_burden_and_protein_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "psm" / "contaminant_burden_results.tsv",
            "contaminant_burden_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "psm-contaminants",
                "contaminant_burden_results.tsv",
                "--run-id-column",
                "run_id",
                "--intensity-column",
                "intensity",
                "--burden-tsv-out",
                "contaminant_burden.tsv",
                "--protein-tsv-out",
                "contaminant_proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["contaminant_evidence"]["summary"]["contaminant_psm_count"] == 3
        assert payload["contaminant_evidence"]["summary"]["contaminant_intensity"] == 1050.0
        assert (
            payload["contaminant_evidence"]["burden_entries"][0][
                "heavy_contaminant_warning"
            ]
            is True
        )
        assert (
            "run-a\t\t3\t2\t1\t1\t2\t2\t2000.0\t1000.0\t0.6666666666666666\t0.5\ttrue"
            in Path("contaminant_burden.tsv").read_text(encoding="utf-8")
        )
        assert (
            "CON__K1C10_HUMAN\trun-a;run-b\t\t2\t2\t850.0"
            in Path("contaminant_proteins.tsv").read_text(encoding="utf-8")
        )


def test_validate_and_summarize_commands_support_mzml_and_design_tables() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "simple.mzml",
            "simple.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "valid.design.tsv",
            "design.tsv",
        )

        validate_mzml = runner.invoke(
            cli, ["validate", "simple.mzml", "--kind", "mzml"]
        )
        summarize_mzml = runner.invoke(
            cli, ["summarize", "simple.mzml", "--kind", "mzml"]
        )
        validate_design = runner.invoke(
            cli, ["validate", "design.tsv", "--kind", "design-table"]
        )
        summarize_design = runner.invoke(
            cli, ["summarize", "design.tsv", "--kind", "design-table"]
        )

        assert validate_mzml.exit_code == 0
        assert json.loads(validate_mzml.output)["detected_format"] == "mzml"
        assert summarize_mzml.exit_code == 0
        assert json.loads(summarize_mzml.output)["metadata"]["run_id"] == "RUN_001"
        assert validate_design.exit_code == 0
        assert json.loads(validate_design.output)["detected_format"] == "design-table"
        assert summarize_design.exit_code == 0
        assert json.loads(summarize_design.output)["accepted_entries"] == 1


def test_mzml_inspect_command_reports_decoding_and_chromatograms() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "mzml-inspect",
                "practical_review.mzml",
                "--spectra-jsonl-out",
                "spectra.jsonl",
                "--chromatograms-json-out",
                "chromatograms.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata"]["run_id"] == "RUN_PRACTICAL_01"
        assert payload["decoding_support"]["supported"] is True
        assert payload["chromatograms"]["total_chromatograms"] == 2
        assert Path("spectra.jsonl").exists()
        assert Path("chromatograms.json").exists()


def test_mzml_inspect_command_surfaces_tic_and_bpc_trace_kinds() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "mzml-inspect",
                "practical_review.mzml",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        kinds = {trace["kind"] for trace in payload["chromatograms"]["accepted_traces"]}
        assert kinds == {"tic", "bpc"}
        assert payload["summary"]["spectrum_count"] == 2


def test_spectrum_summary_command_reports_mzml_ms1_ms2_counts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "practical_review.mzml",
            "practical_review.mzml",
        )

        result = runner.invoke(
            cli,
            [
                "spectrum-summary",
                "practical_review.mzml",
                "--kind",
                "mzml",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "mzml"
        assert payload["ms_level_policy"] == "reported"
        assert payload["ms1_spectrum_count"] == 1
        assert payload["ms2_spectrum_count"] == 1


def test_format_convert_and_bundle_run_commands_materialize_normalized_outputs() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(
            FIXTURE_ROOT / "formats" / "simple.mzml",
            "simple.mzml",
        )
        shutil.copy(
            FIXTURE_ROOT / "formats" / "valid.design.tsv",
            "design.tsv",
        )
        shutil.copy(
            FIXTURE_ROOT / "first_useful_run" / "results.tsv",
            "results.tsv",
        )

        convert_result = runner.invoke(
            cli,
            [
                "format-convert",
                "simple.mzml",
                "--kind",
                "mzml",
                "--to",
                "mgf",
                "--out",
                "converted.mgf",
            ],
        )
        bundle_result = runner.invoke(
            cli,
            [
                "bundle-run",
                "--spectra",
                "simple.mzml",
                "--identifications",
                "results.tsv",
                "--design",
                "design.tsv",
                "--out-dir",
                "bundle",
            ],
        )

        assert convert_result.exit_code == 0
        assert json.loads(convert_result.output)["written_record_count"] == 2
        assert Path("converted.mgf").exists()
        assert "BEGIN IONS" in Path("converted.mgf").read_text()
        assert bundle_result.exit_code == 0
        bundle_manifest = json.loads(bundle_result.output)
        assert bundle_manifest["spectrum_count"] == 2
        assert bundle_manifest["psm_count"] == 2
        assert Path("bundle/bundle.manifest.json").exists()


def test_search_adapter_inspect_and_normalize_commands_work() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(fixture_dir / "sage_results.tsv", "sage_results.tsv")
        shutil.copy(fixture_dir / "sage_config.json", "sage_config.json")
        shutil.copy(fixture_dir / "generic_results.tsv", "generic_results.tsv")
        shutil.copy(fixture_dir / "generic_mapping.json", "generic_mapping.json")

        inspect_result = runner.invoke(
            cli, ["search-adapter", "inspect", "--adapter", "sage"]
        )
        matrix_result = runner.invoke(cli, ["search-adapter", "inspect"])
        normalize_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "normalize",
                "sage",
                "sage_results.tsv",
                "--adapter-version",
                "0.16.0",
                "--config",
                "sage_config.json",
                "--jsonl-out",
                "sage.jsonl",
                "--provenance-out",
                "sage.provenance.json",
            ],
        )
        generic_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "normalize",
                "generic",
                "generic_results.tsv",
                "--mapping-json",
                "generic_mapping.json",
            ],
        )

        assert inspect_result.exit_code == 0
        assert json.loads(inspect_result.output)["adapter_kind"] == "sage"
        assert matrix_result.exit_code == 0
        assert any(
            row["adapter_kind"] == "comet"
            for row in json.loads(matrix_result.output)["capabilities"]
        )
        assert normalize_result.exit_code == 0
        normalize_payload = json.loads(normalize_result.output)
        assert normalize_payload["accepted_rows"] == 2
        assert Path("sage.jsonl").exists()
        assert Path("sage.provenance.json").exists()
        assert generic_result.exit_code == 0
        assert json.loads(generic_result.output)["adapter"]["adapter_kind"] == "generic"


def test_search_adapter_params_compare_and_conformance_commands_work() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(fixture_dir / "comet.params", "comet.params")
        shutil.copy(fixture_dir / "comet_invalid.params", "comet_invalid.params")
        shutil.copy(fixture_dir / "sage_results.tsv", "sage_results.tsv")
        shutil.copy(fixture_dir / "sage_mapping.json", "sage_mapping.json")
        shutil.copy(fixture_dir / "sage_malformed.tsv", "sage_malformed.tsv")

        params_result = runner.invoke(
            cli,
            ["search-adapter", "params", "comet", "comet.params"],
        )
        validate_result = runner.invoke(
            cli,
            ["search-adapter", "validate-config", "comet", "comet_invalid.params"],
        )
        compare_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "compare",
                "sage",
                "sage_results.tsv",
                "generic",
                "sage_results.tsv",
                "--right-mapping-json",
                "sage_mapping.json",
            ],
        )
        conformance_result = runner.invoke(
            cli,
            [
                "search-adapter",
                "conformance",
                "sage",
                "sage_malformed.tsv",
            ],
        )

        assert params_result.exit_code == 0
        assert json.loads(params_result.output)["enzyme"] == "trypsin"
        assert validate_result.exit_code == 0
        validate_payload = json.loads(validate_result.output)
        assert validate_payload["valid"] is False
        assert any(
            issue["code"] == "missing_decoy_strategy"
            for issue in validate_payload["issues"]
        )
        assert compare_result.exit_code == 0
        compare_payload = json.loads(compare_result.output)
        assert compare_payload["exact_match_count"] == 2
        assert conformance_result.exit_code == 0
        conformance_payload = json.loads(conformance_result.output)
        assert conformance_payload["passes"] is False
        assert conformance_payload["rejection_issue_counts"]["invalid_q_value"] == 1


def test_fragpipe_import_command_reports_bundle_summary_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "fragpipe"
        shutil.copy(fixture_dir / "psm.tsv", "psm.tsv")
        shutil.copy(fixture_dir / "combined_peptide.tsv", "combined_peptide.tsv")
        shutil.copy(fixture_dir / "combined_protein.tsv", "combined_protein.tsv")
        shutil.copy(fixture_dir / "combined_quant.tsv", "combined_quant.tsv")

        result = runner.invoke(
            cli,
            [
                "fragpipe-import",
                "psm.tsv",
                "--peptide-tsv",
                "combined_peptide.tsv",
                "--protein-tsv",
                "combined_protein.tsv",
                "--quant-tsv",
                "combined_quant.tsv",
                "--summary-tsv-out",
                "fragpipe.summary.tsv",
                "--canonical-psm-tsv-out",
                "fragpipe.canonical_psm.tsv",
                "--psm-tsv-out",
                "fragpipe.psm.tsv",
                "--peptide-review-tsv-out",
                "fragpipe.peptide.tsv",
                "--protein-review-tsv-out",
                "fragpipe.protein.tsv",
                "--open-search-tsv-out",
                "fragpipe.open_search.tsv",
                "--protein-quantity-tsv-out",
                "fragpipe.quant.tsv",
                "--rejected-tsv-out",
                "fragpipe.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["open_search_psm_count"] == 1
        assert payload["summary"]["peptide_row_count"] == 2
        assert payload["summary"]["protein_row_count"] == 3
        assert payload["summary"]["canonical_psm_count"] == 3
        assert payload["summary"]["open_search_evidence_count"] == 2
        assert payload["summary"]["protein_quantity_count"] == 6
        assert (
            payload["psm_normalization"]["adapter"]["display_name"]
            == "FragPipe psm export"
        )
        assert payload["canonical_psms"][1]["open_search_candidate"] is True
        assert payload["psm_rows"][1]["open_search_candidate"] is True
        assert payload["open_search_evidence"][0]["mass_difference"] == 42.0106
        assert payload["protein_quantity_rows"][0]["quantity_kind"] == "maxlfq_intensity"
        assert payload["rejected_evidence_rows"] == []
        assert Path("fragpipe.summary.tsv").exists()
        assert Path("fragpipe.canonical_psm.tsv").exists()
        assert Path("fragpipe.psm.tsv").exists()
        assert Path("fragpipe.peptide.tsv").exists()
        assert Path("fragpipe.protein.tsv").exists()
        assert Path("fragpipe.open_search.tsv").exists()
        assert Path("fragpipe.quant.tsv").exists()
        assert Path("fragpipe.rejected.tsv").exists()
        assert Path("fragpipe.rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )


def test_fragpipe_benchmark_command_reports_import_fidelity_and_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "fragpipe"
        shutil.copy(fixture_dir / "psm.tsv", "psm.tsv")
        shutil.copy(fixture_dir / "combined_peptide.tsv", "combined_peptide.tsv")
        shutil.copy(fixture_dir / "combined_protein.tsv", "combined_protein.tsv")

        result = runner.invoke(
            cli,
            [
                "fragpipe-benchmark",
                "psm.tsv",
                "--peptide-tsv",
                "combined_peptide.tsv",
                "--protein-tsv",
                "combined_protein.tsv",
                "--summary-tsv-out",
                "fragpipe.benchmark.summary.tsv",
                "--count-comparisons-tsv-out",
                "fragpipe.benchmark.counts.tsv",
                "--protein-groups-tsv-out",
                "fragpipe.benchmark.proteins.tsv",
                "--psm-qvalues-tsv-out",
                "fragpipe.benchmark.psm_qvalues.tsv",
                "--peptide-qvalues-tsv-out",
                "fragpipe.benchmark.peptide_qvalues.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["psm_count_matched"] is True
        assert payload["summary"]["peptide_count_matched"] is True
        assert payload["summary"]["protein_group_count_matched"] is True
        assert payload["summary"]["q_value_behavior_matched"] is True
        assert payload["protein_group_comparison"]["matched"] is True
        assert payload["q_value_behavior"]["max_psm_absolute_difference"] == 0.0
        assert Path("fragpipe.benchmark.summary.tsv").exists()
        assert Path("fragpipe.benchmark.counts.tsv").exists()
        assert Path("fragpipe.benchmark.proteins.tsv").exists()
        assert Path("fragpipe.benchmark.psm_qvalues.tsv").exists()
        assert Path("fragpipe.benchmark.peptide_qvalues.tsv").exists()
        assert "source_psm_count" in Path(
            "fragpipe.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "comparison_id" in Path(
            "fragpipe.benchmark.counts.tsv"
        ).read_text(encoding="utf-8")
        assert "missing_in_import" in Path(
            "fragpipe.benchmark.proteins.tsv"
        ).read_text(encoding="utf-8")
        assert "absolute_difference" in Path(
            "fragpipe.benchmark.psm_qvalues.tsv"
        ).read_text(encoding="utf-8")


def test_sage_import_command_reports_scores_and_modifications() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "sage"
        shutil.copy(fixture_dir / "sage_psm.tsv", "sage_psm.tsv")
        shutil.copy(fixture_dir / "sage_search.json", "sage_search.json")

        result = runner.invoke(
            cli,
            [
                "sage-import",
                "sage_psm.tsv",
                "--config",
                "sage_search.json",
                "--summary-tsv-out",
                "sage.summary.tsv",
                "--canonical-psm-tsv-out",
                "sage.canonical_psm.tsv",
                "--psm-tsv-out",
                "sage.psm.tsv",
                "--rejected-tsv-out",
                "sage.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect_id"] == "sage-psm"
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["canonical_psm_count"] == 3
        assert payload["summary"]["modified_psm_count"] == 2
        assert payload["summary"]["hyperscore_psm_count"] == 3
        assert payload["summary"]["multi_protein_psm_count"] == 1
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert payload["canonical_psms"][0]["record"]["run_id"] == "run01.mzML"
        assert payload["canonical_psms"][1]["record"]["protein_refs"] == [
            "sp|P23456|TRANSFER_HUMAN",
            "sp|P34567|TRANSFER_MOUSE",
        ]
        assert payload["psm_rows"][0]["hyperscore"] == 41.2
        assert payload["rejected_evidence_rows"] == []
        assert Path("sage.summary.tsv").exists()
        assert Path("sage.canonical_psm.tsv").exists()
        assert Path("sage.psm.tsv").exists()
        assert Path("sage.rejected.tsv").exists()


def test_comet_import_command_reports_tabular_and_pepxml_imports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "comet"
        shutil.copy(fixture_dir / "comet_psm.tsv", "comet_psm.tsv")
        shutil.copy(fixture_dir / "comet.params", "comet.params")
        shutil.copy(fixture_dir / "comet_results.pepxml", "comet_results.pepxml")

        tabular_result = runner.invoke(
            cli,
            [
                "comet-import",
                "comet_psm.tsv",
                "--config",
                "comet.params",
                "--summary-tsv-out",
                "comet.summary.tsv",
                "--canonical-psm-tsv-out",
                "comet.canonical_psm.tsv",
                "--psm-tsv-out",
                "comet.psm.tsv",
                "--rejected-tsv-out",
                "comet.rejected.tsv",
            ],
        )
        pepxml_result = runner.invoke(cli, ["comet-import", "comet_results.pepxml"])

        assert tabular_result.exit_code == 0
        tabular_payload = json.loads(tabular_result.output)
        assert tabular_payload["import_kind"] == "tabular"
        assert tabular_payload["summary"]["accepted_psm_count"] == 3
        assert tabular_payload["summary"]["canonical_psm_count"] == 3
        assert tabular_payload["summary"]["modified_psm_count"] == 2
        assert tabular_payload["summary"]["xcorr_psm_count"] == 3
        assert tabular_payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            tabular_payload["canonical_psms"][1]["record"]["protein_refs"]
            == ["sp|P23456|TRANSFER_HUMAN", "sp|P34567|TRANSFER_MOUSE"]
        )
        assert tabular_payload["rejected_evidence_rows"] == []
        assert Path("comet.summary.tsv").exists()
        assert Path("comet.canonical_psm.tsv").exists()
        assert Path("comet.psm.tsv").exists()
        assert Path("comet.rejected.tsv").exists()

        assert pepxml_result.exit_code == 0
        pepxml_payload = json.loads(pepxml_result.output)
        assert pepxml_payload["canonical_psms"][0]["record"]["run_id"] == "run01.mzML"
        assert pepxml_payload["import_kind"] == "pepxml"
        assert pepxml_payload["summary"]["accepted_psm_count"] == 3
        assert pepxml_payload["psm_rows"][0]["xcorr"] == 3.52
        assert pepxml_payload["rejected_evidence_rows"] == []


def test_maxquant_import_command_reports_bundle_experiments_and_lfq() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "maxquant"
        shutil.copy(fixture_dir / "evidence.txt", "evidence.txt")
        shutil.copy(fixture_dir / "peptides.txt", "peptides.txt")
        shutil.copy(fixture_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(fixture_dir / "maxquant_settings.txt", "maxquant_settings.txt")

        result = runner.invoke(
            cli,
            [
                "maxquant-import",
                "evidence.txt",
                "--peptides-txt",
                "peptides.txt",
                "--protein-groups-txt",
                "proteinGroups.txt",
                "--config",
                "maxquant_settings.txt",
                "--summary-tsv-out",
                "maxquant.summary.tsv",
                "--evidence-tsv-out",
                "maxquant.evidence.tsv",
                "--peptide-tsv-out",
                "maxquant.peptides.tsv",
                "--protein-group-tsv-out",
                "maxquant.proteins.tsv",
                "--lfq-candidate-tsv-out",
                "maxquant.lfq_candidates.tsv",
                "--rejected-tsv-out",
                "maxquant.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_evidence_count"] == 4
        assert payload["summary"]["peptide_row_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["lfq_candidate_count"] == 4
        assert payload["summary"]["experiment_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["lfq_experiment_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["contaminant_evidence_count"] == 1
        assert payload["summary"]["reverse_evidence_count"] == 1
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            payload["evidence_normalization"]["adapter"]["display_name"]
            == "MaxQuant bundle evidence"
        )
        assert (
            payload["protein_group_rows"][0]["lfq_intensities"][0]["experiment_name"]
            == "raw_A"
        )
        assert payload["lfq_matrix_candidates"][2]["contaminant_flag"] is True
        assert payload["lfq_matrix_candidates"][0]["member_peptides"] == ["PESTIDE"]
        assert payload["rejected_evidence_rows"] == []
        assert Path("maxquant.summary.tsv").exists()
        assert Path("maxquant.evidence.tsv").exists()
        assert Path("maxquant.peptides.tsv").exists()
        assert Path("maxquant.proteins.tsv").exists()
        assert Path("maxquant.lfq_candidates.tsv").exists()
        assert Path("maxquant.rejected.tsv").exists()


def test_diann_import_command_reports_runs_samples_and_quantities() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")
        shutil.copy(fixture_dir / "diann_config.json", "diann_config.json")

        result = runner.invoke(
            cli,
            [
                "diann-import",
                "diann_report.tsv",
                "--config",
                "diann_config.json",
                "--summary-tsv-out",
                "diann.summary.tsv",
                "--precursor-tsv-out",
                "diann.precursors.tsv",
                "--protein-group-tsv-out",
                "diann.protein_groups.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["run_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["sample_names"] == ["sample_A", "sample_B"]
        assert payload["summary"]["precursor_quantity_count"] == 4
        assert payload["summary"]["protein_group_quantity_count"] == 4
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert payload["normalization"]["adapter"]["display_name"] == "DIA-NN"
        assert payload["precursor_rows"][0]["run_name"] == "raw_A"
        assert payload["precursor_rows"][2]["modified_peptide"] == "ACDM[Oxidation]K"
        assert payload["dia_native_report"]["imported_count"] == 4
        assert payload["dia_native_report"]["imported_protein_groups"][0]["quantity"] == 3400000.0
        assert payload["rejected_evidence_rows"] == []
        assert Path("diann.summary.tsv").exists()
        assert Path("diann.precursors.tsv").exists()
        assert Path("diann.protein_groups.tsv").exists()


def test_diann_import_command_exports_rejected_rows_without_failing() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("diann_invalid.tsv").write_text(
            "\n".join(
                (
                    "Precursor.Id\tStripped.Sequence\tModified.Sequence\tPrecursor.Charge\tQ.Value\tProtein.Group\tProtein.Ids\tRun\tSample\tPrecursor.Quantity\tPG.Quantity\tDecoy",
                    "raw_A_PEPTIDE_2\tPEPTIDE\tPEPTIDE\t2\t0.01\tPG001\tP11111\traw_A\tsample_A\t50\t1000\t0",
                    "raw_B_BADQ_2\tBADQ\tBADQ\t2\t1.2\tPG002\tP22222\traw_B\tsample_B\t120\t2000\t0",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "diann-import",
                "diann_invalid.tsv",
                "--summary-tsv-out",
                "diann.summary.tsv",
                "--rejected-tsv-out",
                "diann.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 1
        assert payload["summary"]["rejected_precursor_count"] == 1
        assert payload["rejected_evidence_rows"][0]["reason_code"] == "invalid_q_value"
        assert Path("diann.rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )
        assert payload["normalization"] is None
        assert payload["rejected_rows"][0]["issues"][0]["code"] == "invalid_q_value"
        assert Path("diann.rejected.tsv").read_text(encoding="utf-8").count(
            "raw_B_BADQ_2"
        ) == 1


def test_diann_precursor_matrix_command_emits_sample_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")

        result = runner.invoke(
            cli,
            [
                "diann-precursor-matrix",
                "diann_report.tsv",
                "--summary-tsv-out",
                "diann.matrix.summary.tsv",
                "--matrix-tsv-out",
                "diann.matrix.tsv",
                "--qvalue-tsv-out",
                "diann.qvalues.tsv",
                "--metadata-tsv-out",
                "diann.metadata.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["policy"]["q_value_filter_timing"] == "before_matrix_construction"
        assert payload["summary"]["precursor_row_count"] == 2
        assert payload["summary"]["observed_cell_count"] == 3
        assert payload["summary"]["excluded_decoy_count"] == 1
        assert payload["rows"][0]["modified_peptide"] == "ACDM[Oxidation]K"
        assert payload["outputs"]["summary_tsv"] == "diann.matrix.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "diann.matrix.tsv"
        assert payload["outputs"]["qvalue_tsv"] == "diann.qvalues.tsv"
        assert payload["outputs"]["metadata_tsv"] == "diann.metadata.tsv"
        assert Path("diann.matrix.summary.tsv").exists()
        assert Path("diann.matrix.tsv").exists()
        assert Path("diann.qvalues.tsv").exists()
        assert Path("diann.metadata.tsv").exists()
        assert "precursor_key\tpeptide_sequence\tmodified_peptide" in Path(
            "diann.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "source_name\tsample_count\trun_count\tprecursor_row_count" in Path(
            "diann.matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "\t0.0021\t0.0024\n" in Path("diann.qvalues.tsv").read_text(
            encoding="utf-8"
        )
        assert "retained_observation_count" in Path("diann.metadata.tsv").read_text(
            encoding="utf-8"
        )


def test_spectronaut_precursor_matrix_command_emits_sample_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-precursor-matrix",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.matrix.summary.tsv",
                "--matrix-tsv-out",
                "spectronaut.matrix.tsv",
                "--qvalue-tsv-out",
                "spectronaut.qvalues.tsv",
                "--metadata-tsv-out",
                "spectronaut.metadata.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "Spectronaut"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["summary"]["precursor_row_count"] == 2
        assert payload["summary"]["excluded_decoy_count"] == 1
        assert payload["outputs"]["metadata_tsv"] == "spectronaut.metadata.tsv"
        assert Path("spectronaut.matrix.summary.tsv").exists()
        assert Path("spectronaut.matrix.tsv").exists()
        assert Path("spectronaut.qvalues.tsv").exists()
        assert Path("spectronaut.metadata.tsv").exists()
        assert "precursor_key\tpeptide_sequence\tmodified_peptide" in Path(
            "spectronaut.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_observation_count" in Path(
            "spectronaut.metadata.tsv"
        ).read_text(encoding="utf-8")


def test_diann_protein_matrix_command_emits_peptide_and_protein_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(fixture_dir / "diann_report.tsv", "diann_report.tsv")

        result = runner.invoke(
            cli,
            [
                "diann-protein-matrix",
                "diann_report.tsv",
                "--target-kind",
                "protein_group",
                "--shared-peptides",
                "include",
                "--summary-tsv-out",
                "diann.protein.summary.tsv",
                "--peptide-tsv-out",
                "diann.peptide.matrix.tsv",
                "--protein-tsv-out",
                "diann.protein.matrix.tsv",
                "--rollup-evidence-tsv-out",
                "diann.rollup.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["peptide_rollup_method"] == "max"
        assert payload["target_kind"] == "protein_group"
        assert payload["shared_peptide_policy"] == "include"
        assert payload["protein_rollup_method"] == "sum"
        assert payload["peptide_summary"]["peptide_row_count"] == 2
        assert payload["protein_summary"]["protein_row_count"] == 2
        assert payload["protein_summary"]["observed_cell_count"] == 3
        assert payload["protein_summary"]["rollup_evidence_entry_count"] >= 6
        assert payload["protein_rows"][0]["entity_id"] == "PG001"
        assert payload["outputs"]["summary_tsv"] == "diann.protein.summary.tsv"
        assert payload["outputs"]["peptide_tsv"] == "diann.peptide.matrix.tsv"
        assert payload["outputs"]["protein_tsv"] == "diann.protein.matrix.tsv"
        assert payload["outputs"]["rollup_evidence_tsv"] == "diann.rollup.evidence.tsv"
        assert Path("diann.protein.summary.tsv").exists()
        assert Path("diann.peptide.matrix.tsv").exists()
        assert Path("diann.protein.matrix.tsv").exists()
        assert Path("diann.rollup.evidence.tsv").exists()
        assert "peptide_key\tpeptide_sequence\tmodified_peptide" in Path(
            "diann.peptide.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\ttarget_kind\tprotein_refs\tpeptide_count" in Path(
            "diann.protein.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "rollup_stage\ttarget_entity_level\ttarget_entity_id" in Path(
            "diann.rollup.evidence.tsv"
        ).read_text(encoding="utf-8")
        assert "source_name\ttarget_kind\tshared_peptide_policy\trollup_method" in (
            Path("diann.protein.summary.tsv").read_text(encoding="utf-8")
        )


def test_spectronaut_protein_matrix_command_emits_rollup_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-protein-matrix",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.protein.summary.tsv",
                "--peptide-tsv-out",
                "spectronaut.peptide.matrix.tsv",
                "--protein-tsv-out",
                "spectronaut.protein.matrix.tsv",
                "--rollup-evidence-tsv-out",
                "spectronaut.rollup.evidence.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "Spectronaut"
        assert payload["sample_ids"] == ["sample_A", "sample_B"]
        assert payload["protein_summary"]["protein_row_count"] == 2
        assert payload["outputs"]["rollup_evidence_tsv"] == "spectronaut.rollup.evidence.tsv"
        assert Path("spectronaut.rollup.evidence.tsv").exists()
        assert "rollup_stage\ttarget_entity_level\ttarget_entity_id" in Path(
            "spectronaut.rollup.evidence.tsv"
        ).read_text(encoding="utf-8")


def test_diann_run_qc_command_emits_qc_ledgers_and_outlier_calls() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        shutil.copy(
            fixture_dir / "diann_run_qc_report.tsv",
            "diann_run_qc_report.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-run-qc",
                "diann_run_qc_report.tsv",
                "--summary-tsv-out",
                "diann.run_qc.summary.tsv",
                "--run-tsv-out",
                "diann.run_qc.runs.tsv",
                "--intensity-tsv-out",
                "diann.run_qc.intensity.tsv",
                "--correlation-tsv-out",
                "diann.run_qc.correlation.tsv",
                "--outlier-tsv-out",
                "diann.run_qc.outliers.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["summary"]["run_count"] == 3
        assert payload["summary"]["flagged_run_count"] == 1
        assert payload["summary"]["weak_run_flag_count"] == 5
        assert payload["run_entries"][2]["run_name"] == "raw_C"
        assert payload["run_entries"][2]["weak_run_flag_count"] == 5
        assert payload["run_entries"][2]["flagged"] is True
        assert payload["outlier_runs"][0]["run_name"] == "raw_C"
        assert payload["outlier_runs"][0]["flags"][0]["threshold_name"] == "high_missing_fraction"
        assert payload["outputs"]["summary_tsv"] == "diann.run_qc.summary.tsv"
        assert payload["outputs"]["run_tsv"] == "diann.run_qc.runs.tsv"
        assert payload["outputs"]["intensity_tsv"] == "diann.run_qc.intensity.tsv"
        assert (
            payload["outputs"]["correlation_tsv"]
            == "diann.run_qc.correlation.tsv"
        )
        assert payload["outputs"]["outlier_tsv"] == "diann.run_qc.outliers.tsv"
        assert Path("diann.run_qc.summary.tsv").exists()
        assert Path("diann.run_qc.runs.tsv").exists()
        assert Path("diann.run_qc.intensity.tsv").exists()
        assert Path("diann.run_qc.correlation.tsv").exists()
        assert Path("diann.run_qc.outliers.tsv").exists()
        assert "run_name\tsample_name\tprecursor_id_count" in Path(
            "diann.run_qc.runs.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_run_flag_count" in Path(
            "diann.run_qc.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "run_name_a\tsample_name_a\trun_name_b\tsample_name_b" in Path(
            "diann.run_qc.correlation.tsv"
        ).read_text(encoding="utf-8")
        assert "reason_code\treason\tthreshold_name\tthreshold_value\tobserved_value" in Path(
            "diann.run_qc.outliers.tsv"
        ).read_text(encoding="utf-8")
        assert "raw_C\tsample_C\tlow_precursor_coverage" in Path(
            "diann.run_qc.outliers.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_reporter_matrix_command_emits_mapping_totals_and_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-reporter-matrix",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.summary.tsv",
                "--channel-mapping-tsv-out",
                "tmt.channel_mapping.tsv",
                "--channel-totals-tsv-out",
                "tmt.channel_totals.tsv",
                "--peptide-matrix-tsv-out",
                "tmt.peptide_matrix.tsv",
                "--protein-matrix-tsv-out",
                "tmt.protein_matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["source_report"]["summary"]["accepted_row_count"] == 4
        assert payload["feature_bundle"]["summary"]["missing_channel_count"] == 2
        assert payload["report"]["summary"]["peptide_row_count"] == 2
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["outputs"]["summary_tsv"] == "tmt.summary.tsv"
        assert payload["outputs"]["peptide_matrix_tsv"] == "tmt.peptide_matrix.tsv"
        assert Path("tmt.summary.tsv").exists()
        assert Path("tmt.channel_mapping.tsv").exists()
        assert Path("tmt.channel_totals.tsv").exists()
        assert Path("tmt.peptide_matrix.tsv").exists()
        assert Path("tmt.protein_matrix.tsv").exists()
        assert "plex_a_129N" in Path("tmt.peptide_matrix.tsv").read_text(
            encoding="utf-8"
        )
        assert "P001" in Path("tmt.protein_matrix.tsv").read_text(encoding="utf-8")
        assert "total_intensity" in Path("tmt.channel_totals.tsv").read_text(
            encoding="utf-8"
        )
        assert "mapped_to_design" in Path("tmt.channel_mapping.tsv").read_text(
            encoding="utf-8"
        )


def test_tmt_normalize_command_emits_distribution_and_normalized_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-normalize",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--method",
                "reference_channel",
                "--summary-tsv-out",
                "tmt.normalize.summary.tsv",
                "--transform-tsv-out",
                "tmt.normalize.transforms.tsv",
                "--distribution-tsv-out",
                "tmt.normalize.distributions.tsv",
                "--peptide-matrix-tsv-out",
                "tmt.normalize.peptides.tsv",
                "--protein-matrix-tsv-out",
                "tmt.normalize.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert (
            payload["report"]["summary"]["method"] == "reference_channel"
        )
        assert payload["report"]["summary"]["reference_group_count"] == 2
        assert Path("tmt.normalize.summary.tsv").exists()
        assert Path("tmt.normalize.transforms.tsv").exists()
        assert Path("tmt.normalize.distributions.tsv").exists()
        assert Path("tmt.normalize.peptides.tsv").exists()
        assert Path("tmt.normalize.proteins.tsv").exists()
        assert "reference_group_count" in Path(
            "tmt.normalize.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "reference_channel" in Path(
            "tmt.normalize.transforms.tsv"
        ).read_text(encoding="utf-8")
        assert "stage\tmultiplex_group\tmultiplex_channel" in Path(
            "tmt.normalize.distributions.tsv"
        ).read_text(encoding="utf-8")
        assert "plex_a_128N" in Path("tmt.normalize.peptides.tsv").read_text(
            encoding="utf-8"
        )
        assert "entity_id\ttarget_kind\tprotein_refs" in Path(
            "tmt.normalize.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_interference_command_emits_filtered_and_channel_summary_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_interference.tsv",
            "maxquant_tmt_interference.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-interference",
                "maxquant_tmt_interference.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.interference.summary.tsv",
                "--observation-tsv-out",
                "tmt.interference.observations.tsv",
                "--filtered-tsv-out",
                "tmt.interference.filtered.tsv",
                "--channel-summary-tsv-out",
                "tmt.interference.channels.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["observed_channel_row_count"] == 12
        assert payload["report"]["summary"]["filtered_channel_row_count"] == 6
        assert payload["report"]["summary"]["channel_summary_count"] == 6
        assert Path("tmt.interference.summary.tsv").exists()
        assert Path("tmt.interference.observations.tsv").exists()
        assert Path("tmt.interference.filtered.tsv").exists()
        assert Path("tmt.interference.channels.tsv").exists()
        assert "filtered_channel_row_count" in Path(
            "tmt.interference.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "threshold_exceeded" in Path(
            "tmt.interference.observations.tsv"
        ).read_text(encoding="utf-8")
        assert "considered unreliable" in Path(
            "tmt.interference.filtered.tsv"
        ).read_text(encoding="utf-8")
        assert "mean_interference_fraction" in Path(
            "tmt.interference.channels.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-report",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--control-channel",
                "126",
                "--output-dir",
                "tmt_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["control_channel"] == "126"
        assert payload["report"]["summary"]["sample_qc_entry_count"] == 8
        report_dir = Path("tmt_report")
        assert (report_dir / "tmt_workflow_manifest.json").exists()
        assert (report_dir / "tmt_workflow_summary.tsv").exists()
        assert (report_dir / "tmt_reporter_import_summary.tsv").exists()
        assert (report_dir / "tmt_reporter_rows.tsv").exists()
        assert (report_dir / "tmt_reporter_rejected_rows.tsv").exists()
        assert (report_dir / "tmt_metadata_summary.tsv").exists()
        assert (report_dir / "tmt_channel_assignments.tsv").exists()
        assert (report_dir / "label_based_report_manifest.json").exists()
        assert (report_dir / "label_based_report_summary.tsv").exists()
        assert (report_dir / "label_based_sample_qc.tsv").exists()
        assert (report_dir / "tmt_channel_totals.tsv").exists()
        assert (report_dir / "tmt_protein_ratios.tsv").exists()
        assert (report_dir / "label_based_differential_results.tsv").exists()
        assert "accepted_input_row_count" in (
            report_dir / "tmt_workflow_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "quality_entry_count" in (
            report_dir / "label_based_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "assay_axis" in (
            report_dir / "label_based_sample_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "total_intensity" in (
            report_dir / "tmt_channel_totals.tsv"
        ).read_text(encoding="utf-8")
        assert "ratio" in (
            report_dir / "tmt_protein_ratios.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_ratio_command_emits_peptide_protein_and_missing_ratio_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-ratios",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--control-channel",
                "126",
                "--summary-tsv-out",
                "tmt.ratio.summary.tsv",
                "--peptide-tsv-out",
                "tmt.ratio.peptides.tsv",
                "--protein-tsv-out",
                "tmt.ratio.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["control_channel"] == "126"
        assert payload["report"]["summary"]["control_channel"] == "126"
        assert payload["report"]["summary"]["normalization_method"] == "none"
        assert payload["report"]["summary"]["peptide_ratio_count"] == 12
        assert payload["report"]["summary"]["protein_ratio_count"] == 12
        assert payload["report"]["summary"]["missing_ratio_count"] == 8
        assert Path("tmt.ratio.summary.tsv").exists()
        assert Path("tmt.ratio.peptides.tsv").exists()
        assert Path("tmt.ratio.proteins.tsv").exists()
        assert "missing_ratio_count" in Path("tmt.ratio.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "sample_channel_missing" in Path(
            "tmt.ratio.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P001" in Path("tmt.ratio.proteins.tsv").read_text(encoding="utf-8")


def test_silac_quantify_command_emits_peptide_and_protein_ratio_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(fixture_dir / "silac_features.tsv", "silac_features.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-quantify",
                "silac_features.tsv",
                "--labels",
                "light,medium,heavy",
                "--collapse-charge-states",
                "--summary-tsv-out",
                "silac.summary.tsv",
                "--peptide-tsv-out",
                "silac.peptides.tsv",
                "--protein-tsv-out",
                "silac.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["import_report"]["summary"]["sample_count"] == 2
        assert payload["report"]["summary"]["expected_label_count"] == 3
        assert payload["report"]["summary"]["peptide_ratio_count"] == 8
        assert payload["report"]["summary"]["protein_ratio_count"] == 8
        assert payload["report"]["summary"]["missing_ratio_count"] == 4
        assert Path("silac.summary.tsv").exists()
        assert Path("silac.peptides.tsv").exists()
        assert Path("silac.proteins.tsv").exists()
        assert "protein_ratio_count" in Path("silac.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "numerator_label_missing" in Path("silac.peptides.tsv").read_text(
            encoding="utf-8"
        )
        assert "sample_a\tP001\tP001\tPEPTIDE\tmedium\tlight\t2000.0\t1500.0" in Path(
            "silac.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_silac_differential_command_emits_matrix_result_and_balance_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(
            fixture_dir / "silac_differential_features.tsv",
            "silac_differential_features.tsv",
        )
        shutil.copy(
            fixture_dir / "silac_differential.design.tsv",
            "silac_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-differential",
                "silac_differential_features.tsv",
                "silac_differential.design.tsv",
                "--raw-matrix-tsv-out",
                "silac.diff.raw.tsv",
                "--normalized-matrix-tsv-out",
                "silac.diff.normalized.tsv",
                "--results-tsv-out",
                "silac.diff.results.tsv",
                "--balance-tsv-out",
                "silac.diff.balance.tsv",
                "--volcano-tsv-out",
                "silac.diff.volcano.tsv",
                "--volcano-json-out",
                "silac.diff.volcano.json",
                "--volcano-svg-out",
                "silac.diff.volcano.svg",
                "--volcano-html-out",
                "silac.diff.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["design_matrix"]["sample_count"] == 4
        assert payload["report"]["differential_abundance_report"] is not None
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert Path("silac.diff.raw.tsv").exists()
        assert Path("silac.diff.normalized.tsv").exists()
        assert Path("silac.diff.results.tsv").exists()
        assert Path("silac.diff.balance.tsv").exists()
        assert Path("silac.diff.volcano.tsv").exists()
        assert Path("silac.diff.volcano.json").exists()
        assert Path("silac.diff.volcano.svg").exists()
        assert Path("silac.diff.volcano.html").exists()
        assert "member_peptides" in Path("silac.diff.raw.tsv").read_text(
            encoding="utf-8"
        )
        assert "adjusted_p_value" in Path("silac.diff.results.tsv").read_text(
            encoding="utf-8"
        )
        assert "raw_p_value" in Path(
            "silac.diff.volcano.tsv"
        ).read_text(encoding="utf-8")
        assert '"source_kind": "label_based"' in Path(
            "silac.diff.volcano.json"
        ).read_text(encoding="utf-8")
        assert "<svg" in Path("silac.diff.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("silac.diff.volcano.html").read_text(
            encoding="utf-8"
        )


def test_silac_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(
            fixture_dir / "silac_differential_features.tsv",
            "silac_differential_features.tsv",
        )
        shutil.copy(
            fixture_dir / "silac_differential.design.tsv",
            "silac_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-report",
                "silac_differential_features.tsv",
                "silac_differential.design.tsv",
                "--output-dir",
                "silac_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["sample_qc_entry_count"] == 4
        report_dir = Path("silac_report")
        assert (report_dir / "label_based_report_manifest.json").exists()
        assert (report_dir / "label_based_report_summary.tsv").exists()
        assert (report_dir / "label_based_sample_qc.tsv").exists()
        assert (report_dir / "silac_ratio_summary.tsv").exists()
        assert (report_dir / "silac_protein_ratios.tsv").exists()
        assert (report_dir / "label_based_differential_results.tsv").exists()
        assert "protein_ratio_count" in (
            report_dir / "label_based_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "assay_axis" in (
            report_dir / "label_based_sample_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "reference_label" in (
            report_dir / "silac_protein_ratios.tsv"
        ).read_text(encoding="utf-8")


def test_silac_validate_command_emits_label_distribution_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "isotope_labeling"
        shutil.copy(fixture_dir / "silac_features.tsv", "silac_features.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "silac-validate",
                "silac_features.tsv",
                "--labels",
                "light,medium,heavy",
                "--summary-tsv-out",
                "silac.validation.summary.tsv",
                "--label-tsv-out",
                "silac.validation.labels.tsv",
                "--distribution-tsv-out",
                "silac.validation.distribution.tsv",
                "--weak-tsv-out",
                "silac.validation.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["sample_count"] == 2
        assert payload["report"]["summary"]["missing_pair_member_count"] == 2
        assert payload["report"]["summary"]["abnormal_distribution_count"] == 1
        assert payload["report"]["summary"]["weak_label_count"] == 2
        assert "sample_b\tmedium\t2\t1\t1" in Path(
            "silac.validation.labels.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_b\tmedium\t1500.0\t2200.0" in Path(
            "silac.validation.distribution.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_total_intensity" in Path(
            "silac.validation.weak.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_validate_command_emits_channel_distribution_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "isotope-labeling",
                "tmt-validate",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.validation.summary.tsv",
                "--channel-tsv-out",
                "tmt.validation.channels.tsv",
                "--distribution-tsv-out",
                "tmt.validation.distribution.tsv",
                "--weak-tsv-out",
                "tmt.validation.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["expected_channel_count"] == 8
        assert payload["report"]["summary"]["missing_channel_count"] == 2
        assert payload["report"]["summary"]["weak_channel_count"] == 2
        assert "plex-a\t129N\tplex_a_129N" in Path(
            "tmt.validation.channels.tsv"
        ).read_text(encoding="utf-8")
        assert "plex-a\t126\tplex_a_126" in Path(
            "tmt.validation.distribution.tsv"
        ).read_text(encoding="utf-8")
        assert "channel_missing" in Path("tmt.validation.weak.tsv").read_text(
            encoding="utf-8"
        )


def test_multiplex_validate_metadata_command_emits_assignment_issue_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "tmt_metadata_issues.design.tsv",
            "tmt_metadata_issues.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "validate-metadata",
                "tmt_metadata_issues.design.tsv",
                "--summary-tsv-out",
                "multiplex.metadata.summary.tsv",
                "--channel-tsv-out",
                "multiplex.metadata.channels.tsv",
                "--duplicate-tsv-out",
                "multiplex.metadata.duplicates.tsv",
                "--missing-condition-tsv-out",
                "multiplex.metadata.conditions.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["report"]["summary"]["multiplex_group_count"] == 2
        assert payload["report"]["summary"]["missing_channel_assignment_count"] == 1
        assert payload["report"]["summary"]["duplicate_assignment_count"] == 2
        assert payload["report"]["summary"]["missing_condition_count"] == 1
        assert "plex-b\t129N\t\t\t\tFalse" in Path(
            "multiplex.metadata.channels.tsv"
        ).read_text(encoding="utf-8")
        assert "duplicate_channel_assignment\tplex-b\t127N" in Path(
            "multiplex.metadata.duplicates.tsv"
        ).read_text(encoding="utf-8")
        assert "plex-b\t128N\tplex_b_128N\tpooled_reference" in Path(
            "multiplex.metadata.conditions.tsv"
        ).read_text(encoding="utf-8")


def test_tmt_integrate_plexes_command_emits_alignment_effect_and_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-integrate-plexes",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--summary-tsv-out",
                "tmt.integration.summary.tsv",
                "--alignment-tsv-out",
                "tmt.integration.alignment.tsv",
                "--plex-effect-tsv-out",
                "tmt.integration.effects.tsv",
                "--protein-matrix-tsv-out",
                "tmt.integration.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["summary"]["multiplex_group_count"] == 2
        assert payload["report"]["summary"]["integrated_sample_count"] == 4
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["outputs"]["summary_tsv"] == "tmt.integration.summary.tsv"
        assert Path("tmt.integration.summary.tsv").exists()
        assert Path("tmt.integration.alignment.tsv").exists()
        assert Path("tmt.integration.effects.tsv").exists()
        assert Path("tmt.integration.proteins.tsv").exists()
        assert "bridge_sample_id" in Path(
            "tmt.integration.alignment.tsv"
        ).read_text(encoding="utf-8")
        assert "ratio_to_global_bridge_median" in Path(
            "tmt.integration.effects.tsv"
        ).read_text(encoding="utf-8")
        assert "P001" in Path("tmt.integration.proteins.tsv").read_text(
            encoding="utf-8"
        )


def test_tmt_differential_command_emits_matrix_result_and_balance_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "multiplex"
        shutil.copy(
            fixture_dir / "maxquant_tmt_evidence.tsv",
            "maxquant_tmt_evidence.tsv",
        )
        shutil.copy(fixture_dir / "tmt.design.tsv", "tmt.design.tsv")

        result = runner.invoke(
            cli,
            [
                "multiplex",
                "tmt-differential",
                "maxquant_tmt_evidence.tsv",
                "tmt.design.tsv",
                "--source-kind",
                "maxquant",
                "--raw-matrix-tsv-out",
                "tmt.diff.raw.tsv",
                "--normalized-matrix-tsv-out",
                "tmt.diff.normalized.tsv",
                "--results-tsv-out",
                "tmt.diff.results.tsv",
                "--balance-tsv-out",
                "tmt.diff.balance.tsv",
                "--volcano-tsv-out",
                "tmt.diff.volcano.tsv",
                "--volcano-json-out",
                "tmt.diff.volcano.json",
                "--volcano-svg-out",
                "tmt.diff.volcano.svg",
                "--volcano-html-out",
                "tmt.diff.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "maxquant"
        assert payload["report"]["design_matrix"]["sample_count"] == 4
        assert payload["report"]["differential_abundance_report"] is not None
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert Path("tmt.diff.raw.tsv").exists()
        assert Path("tmt.diff.normalized.tsv").exists()
        assert Path("tmt.diff.results.tsv").exists()
        assert Path("tmt.diff.balance.tsv").exists()
        assert Path("tmt.diff.volcano.tsv").exists()
        assert Path("tmt.diff.volcano.json").exists()
        assert Path("tmt.diff.volcano.svg").exists()
        assert Path("tmt.diff.volcano.html").exists()
        assert "member_peptides" in Path("tmt.diff.raw.tsv").read_text(
            encoding="utf-8"
        )
        assert "adjusted_p_value" in Path("tmt.diff.results.tsv").read_text(
            encoding="utf-8"
        )
        assert "raw_p_value" in Path("tmt.diff.volcano.tsv").read_text(
            encoding="utf-8"
        )
        assert '"source_kind": "label_based"' in Path(
            "tmt.diff.volcano.json"
        ).read_text(encoding="utf-8")
        assert "<svg" in Path("tmt.diff.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("tmt.diff.volcano.html").read_text(
            encoding="utf-8"
        )
        assert "interquartile_range" in Path("tmt.diff.balance.tsv").read_text(
            encoding="utf-8"
        )


def test_diann_library_coverage_command_emits_identity_and_scope_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            fixture_dir / "diann_library_coverage.tsv",
            "diann_library_coverage.tsv",
        )
        shutil.copy(
            format_dir / "diann_library_coverage.msp",
            "diann_library_coverage.msp",
        )
        shutil.copy(
            format_dir / "diann_library_coverage.design.tsv",
            "diann_library_coverage.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-library-coverage",
                "diann_library_coverage.tsv",
                "diann_library_coverage.msp",
                "--design",
                "diann_library_coverage.design.tsv",
                "--summary-tsv-out",
                "diann.library.summary.tsv",
                "--sample-tsv-out",
                "diann.library.samples.tsv",
                "--condition-tsv-out",
                "diann.library.conditions.tsv",
                "--peptide-tsv-out",
                "diann.library.peptides.tsv",
                "--protein-tsv-out",
                "diann.library.proteins.tsv",
                "--outside-library-peptide-tsv-out",
                "diann.library.outside.peptides.tsv",
                "--outside-library-protein-tsv-out",
                "diann.library.outside.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "DIA-NN"
        assert payload["library_source_format"] == "msp"
        assert payload["summary"]["library_peptide_count"] == 5
        assert payload["summary"]["detected_peptide_count"] == 4
        assert payload["summary"]["observed_outside_library_peptide_count"] == 1
        assert payload["summary"]["library_protein_count"] == 5
        assert payload["summary"]["detected_protein_count"] == 4
        assert payload["summary"]["observed_outside_library_protein_count"] == 1
        assert payload["condition_entries"][0]["condition"] == "control"
        assert payload["condition_entries"][0]["detected_peptide_count"] == 4
        assert payload["condition_entries"][1]["condition"] == "treatment"
        assert payload["condition_entries"][1]["detected_peptide_count"] == 1
        assert payload["peptide_entries"][0]["canonical_peptide"] == "LIVNLY"
        assert payload["peptide_entries"][0]["detected_overall"] is False
        assert payload["protein_entries"][-1]["protein_ref"] == "P44444"
        assert payload["protein_entries"][-1]["detected_overall"] is False
        assert (
            payload["observed_outside_library_peptide_entries"][0]["canonical_peptide"]
            == "PEPNOVEL"
        )
        assert (
            payload["observed_outside_library_protein_entries"][0]["protein_ref"]
            == "P55555"
        )
        assert payload["outputs"]["summary_tsv"] == "diann.library.summary.tsv"
        assert payload["outputs"]["sample_tsv"] == "diann.library.samples.tsv"
        assert (
            payload["outputs"]["condition_tsv"] == "diann.library.conditions.tsv"
        )
        assert payload["outputs"]["peptide_tsv"] == "diann.library.peptides.tsv"
        assert payload["outputs"]["protein_tsv"] == "diann.library.proteins.tsv"
        assert (
            payload["outputs"]["outside_library_peptide_tsv"]
            == "diann.library.outside.peptides.tsv"
        )
        assert (
            payload["outputs"]["outside_library_protein_tsv"]
            == "diann.library.outside.proteins.tsv"
        )
        assert Path("diann.library.summary.tsv").exists()
        assert Path("diann.library.samples.tsv").exists()
        assert Path("diann.library.conditions.tsv").exists()
        assert Path("diann.library.peptides.tsv").exists()
        assert Path("diann.library.proteins.tsv").exists()
        assert Path("diann.library.outside.peptides.tsv").exists()
        assert Path("diann.library.outside.proteins.tsv").exists()
        assert "sample_id\tdetected_peptide_count\tdetected_protein_count" in Path(
            "diann.library.samples.tsv"
        ).read_text(encoding="utf-8")
        assert "control\tsample_A;sample_B\t4\t4" in Path(
            "diann.library.conditions.tsv"
        ).read_text(encoding="utf-8")
        assert "LIVNLY\tP44444\tfalse\t0\t0" in Path(
            "diann.library.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P44444\tfalse\t0\t0" in Path(
            "diann.library.proteins.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPNOVEL\tP55555\tsample_A\tcontrol\t1\t1" in Path(
            "diann.library.outside.peptides.tsv"
        ).read_text(encoding="utf-8")
        assert "P55555\tsample_A\tcontrol\t1\t1" in Path(
            "diann.library.outside.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_target_panel_review_command_emits_dia_panel_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            fixture_dir / "diann_library_coverage.tsv",
            "diann_library_coverage.tsv",
        )
        shutil.copy(format_dir / "dia_target_panel.tsv", "dia_target_panel.tsv")

        result = runner.invoke(
            cli,
            [
                "target-panel-review",
                "diann_library_coverage.tsv",
                "dia_target_panel.tsv",
                "--source-kind",
                "dia_peptide",
                "--summary-tsv-out",
                "target.summary.tsv",
                "--target-tsv-out",
                "target.targets.tsv",
                "--missing-tsv-out",
                "target.missing.tsv",
                "--intensity-tsv-out",
                "target.intensity.tsv",
                "--matrix-tsv-out",
                "target.matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "dia_peptide"
        assert payload["source_name"] == "DIA-NN"
        assert payload["summary"]["total_target_count"] == 4
        assert payload["summary"]["matched_target_count"] == 3
        assert payload["summary"]["missing_target_count"] == 1
        assert payload["matched_targets"][0]["modified_peptide"] == "PEPALFA"
        assert payload["matched_targets"][0]["expected_charge"] == 2
        assert payload["matched_targets"][1]["target_id"] == "dia-p22222"
        assert payload["missing_targets"][0]["target_id"] == "dia-missing-protein"
        assert payload["outputs"]["summary_tsv"] == "target.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "target.matrix.tsv"
        assert Path("target.summary.tsv").exists()
        assert Path("target.targets.tsv").exists()
        assert Path("target.missing.tsv").exists()
        assert Path("target.intensity.tsv").exists()
        assert Path("target.matrix.tsv").exists()
        assert "dia-missing-protein\tprotein\t\t\t" in Path(
            "target.missing.tsv"
        ).read_text(encoding="utf-8")
        assert "dia-pepalfa\tpeptide\tPEPALFA|PG001\tPEPALFA\tPEPALFA\t2\t2\tP11111" in Path(
            "target.matrix.tsv"
        ).read_text(encoding="utf-8")


def test_target_panel_review_command_emits_lfq_protein_panel_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        quant_dir = FIXTURE_ROOT / "quant"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            quant_dir / "target_panel_ms1_features.tsv",
            "target_panel_ms1_features.tsv",
        )
        shutil.copy(format_dir / "lfq_target_panel.tsv", "lfq_target_panel.tsv")

        result = runner.invoke(
            cli,
            [
                "target-panel-review",
                "target_panel_ms1_features.tsv",
                "lfq_target_panel.tsv",
                "--source-kind",
                "lfq_protein_lfq",
                "--summary-tsv-out",
                "lfq.target.summary.tsv",
                "--target-tsv-out",
                "lfq.target.targets.tsv",
                "--missing-tsv-out",
                "lfq.target.missing.tsv",
                "--intensity-tsv-out",
                "lfq.target.intensity.tsv",
                "--matrix-tsv-out",
                "lfq.target.matrix.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "lfq_protein_lfq"
        assert payload["source_name"] == "feature"
        assert payload["summary"]["total_target_count"] == 4
        assert payload["summary"]["matched_target_count"] == 1
        assert payload["summary"]["missing_target_count"] == 3
        assert payload["matched_targets"][0]["target_id"] == "lfq-p003"
        assert payload["matched_targets"][0]["modified_peptide"] is None
        assert payload["matched_targets"][0]["expected_charge"] is None
        assert payload["missing_targets"][0]["reason"] == (
            "peptide targets require a peptide-level matrix"
        )
        assert payload["outputs"]["target_tsv"] == "lfq.target.targets.tsv"
        assert payload["outputs"]["intensity_tsv"] == "lfq.target.intensity.tsv"
        assert Path("lfq.target.summary.tsv").exists()
        assert Path("lfq.target.targets.tsv").exists()
        assert Path("lfq.target.missing.tsv").exists()
        assert Path("lfq.target.intensity.tsv").exists()
        assert Path("lfq.target.matrix.tsv").exists()
        assert "lfq-p003\tprotein\t\t\tP003\t4" in Path(
            "lfq.target.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "lfq-apeptide\tpeptide\tAPEPTIDE\t2\tpeptide targets require a peptide-level matrix" in (
            Path("lfq.target.missing.tsv").read_text(encoding="utf-8")
        )


def test_transition_qc_command_emits_transition_and_weak_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(format_dir / "transition_quant.tsv", "transition_quant.tsv")

        result = runner.invoke(
            cli,
            [
                "transition-qc",
                "transition_quant.tsv",
                "--summary-tsv-out",
                "transition.summary.tsv",
                "--transition-tsv-out",
                "transition.rows.tsv",
                "--sample-tsv-out",
                "transition.samples.tsv",
                "--weak-tsv-out",
                "transition.weak.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_name"] == "transition table"
        assert payload["sample_ids"] == ["s1", "s2", "s3"]
        assert payload["summary"]["transition_count"] == 4
        assert payload["summary"]["weak_transition_count"] == 1
        assert payload["entries"][0]["precursor_charge"] == 2
        assert payload["entries"][0]["median_retention_time_minutes"] == 12.45
        assert payload["weak_transitions"][0]["transition_id"] == "tr_y6_b"
        assert payload["outputs"]["summary_tsv"] == "transition.summary.tsv"
        assert payload["outputs"]["transition_tsv"] == "transition.rows.tsv"
        assert payload["outputs"]["sample_tsv"] == "transition.samples.tsv"
        assert payload["outputs"]["weak_tsv"] == "transition.weak.tsv"
        assert Path("transition.summary.tsv").exists()
        assert Path("transition.rows.tsv").exists()
        assert Path("transition.samples.tsv").exists()
        assert Path("transition.weak.tsv").exists()
        assert "source_name\tprecursor_count\ttransition_count" in Path(
            "transition.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "tr_y7_a\tprec_a\t2\tPEPTIDEK\tP001\ty7" in Path(
            "transition.rows.tsv"
        ).read_text(encoding="utf-8")
        assert "tr_y7_a\tprec_a\ts1\trun_a\t120000\t12.5\t0.002\t160000\t0.75\t1\ttrue" in (
            Path("transition.samples.tsv").read_text(encoding="utf-8")
        )
        assert "tr_y6_b\tprec_b\t1\t3\t0.333333\t0.0789474" in Path(
            "transition.weak.tsv"
        ).read_text(encoding="utf-8")


def test_targeted_target_matrix_command_emits_targeted_review_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_results.tsv",
            "skyline_targeted_results.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-target-matrix",
                "skyline_targeted_results.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "targeted.summary.tsv",
                "--observation-tsv-out",
                "targeted.observations.tsv",
                "--target-tsv-out",
                "targeted.targets.tsv",
                "--sample-tsv-out",
                "targeted.samples.tsv",
                "--flagged-tsv-out",
                "targeted.flagged.tsv",
                "--retained-transition-tsv-out",
                "targeted.retained.tsv",
                "--excluded-transition-tsv-out",
                "targeted.excluded.tsv",
                "--missingness-tsv-out",
                "targeted.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["source_name"] == "Skyline"
        assert payload["import_summary"]["observation_count"] == 6
        assert payload["matrix_summary"]["target_count"] == 2
        assert payload["matrix_summary"]["retained_transition_count"] == 4
        assert payload["matrix_summary"]["excluded_transition_count"] == 2
        assert payload["matrix_summary"]["quality_flag_count"] == 2
        assert payload["targets"][1]["target_id"] == "PEPTIDEK/2"
        assert payload["targets"][1]["total_intensity"] == 273000.0
        assert payload["retained_transitions"][0]["transition_id"] == "y5"
        assert payload["excluded_transitions"][-1]["transition_id"] == "y8"
        missing_entry = next(
            entry
            for entry in payload["missingness"]
            if entry["target_id"] == "ACDMPEP/3" and entry["sample_id"] == "sample_B"
        )
        assert missing_entry["missing_reason"] == "no_observation"
        assert payload["outputs"]["summary_tsv"] == "targeted.summary.tsv"
        assert payload["outputs"]["observation_tsv"] == "targeted.observations.tsv"
        assert payload["outputs"]["target_tsv"] == "targeted.targets.tsv"
        assert payload["outputs"]["sample_tsv"] == "targeted.samples.tsv"
        assert payload["outputs"]["flagged_tsv"] == "targeted.flagged.tsv"
        assert payload["outputs"]["retained_transition_tsv"] == "targeted.retained.tsv"
        assert payload["outputs"]["excluded_transition_tsv"] == "targeted.excluded.tsv"
        assert payload["outputs"]["missingness_tsv"] == "targeted.missingness.tsv"
        assert Path("targeted.summary.tsv").exists()
        assert Path("targeted.observations.tsv").exists()
        assert Path("targeted.targets.tsv").exists()
        assert Path("targeted.samples.tsv").exists()
        assert Path("targeted.flagged.tsv").exists()
        assert Path("targeted.retained.tsv").exists()
        assert Path("targeted.excluded.tsv").exists()
        assert Path("targeted.missingness.tsv").exists()
        assert "Skyline\t2\t2\t3\t1\t0\t4\t2\t2" in Path("targeted.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "skyline_export\ty8\tPEPTIDEK/2\t2\tPEPTIDEK\tsample_B\t8000" in Path(
            "targeted.observations.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tPEPTIDEK\tP001\ty7;y8\ty7;y8\ty8\t2\t1\t2\t273000" in Path(
            "targeted.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty7;y8\ty7\ty8\t2\t1\t1\t115000\t12.4\tinterference\t\ttrue" in (
            Path("targeted.samples.tsv").read_text(encoding="utf-8")
        )
        assert "PEPTIDEK/2\tPEPTIDEK\tP001\t1\t1" in Path(
            "targeted.flagged.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty7\t115000\t12.4\tpass" in Path(
            "targeted.retained.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\tsample_B\ty8\t8000\t12.7\tinterference\tquality_filter" in Path(
            "targeted.excluded.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\tsample_B\t0\t0\t0\ttrue\tno_observation" in Path(
            "targeted.missingness.tsv"
        ).read_text(encoding="utf-8")


def test_targeted_assay_qc_command_emits_targeted_qc_review_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            format_dir / "skyline_targeted_qc_results.tsv",
            "skyline_targeted_qc_results.tsv",
        )
        shutil.copy(
            format_dir / "skyline_targeted_qc.design.tsv",
            "skyline_targeted_qc.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "targeted-assay-qc",
                "skyline_targeted_qc_results.tsv",
                "skyline_targeted_qc.design.tsv",
                "--source-kind",
                "skyline_export",
                "--summary-tsv-out",
                "assay.summary.tsv",
                "--target-qc-tsv-out",
                "assay.targets.tsv",
                "--transition-tsv-out",
                "assay.transitions.tsv",
                "--transition-qc-tsv-out",
                "assay.transition_qc.tsv",
                "--fragment-ratio-tsv-out",
                "assay.fragments.tsv",
                "--retention-tsv-out",
                "assay.retention.tsv",
                "--replicate-cv-tsv-out",
                "assay.replicate_cv.tsv",
                "--unreliable-tsv-out",
                "assay.unreliable.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "skyline_export"
        assert payload["source_name"] == "Skyline"
        assert payload["import_summary"]["observation_count"] == 14
        assert payload["design_summary"]["accepted_entry_count"] == 4
        assert payload["assay_qc_summary"]["target_count"] == 2
        assert payload["assay_qc_summary"]["reliable_target_entry_count"] == 3
        assert payload["assay_qc_summary"]["flagged_replicate_cv_entry_count"] == 1
        assert payload["outputs"]["summary_tsv"] == "assay.summary.tsv"
        assert payload["outputs"]["target_qc_tsv"] == "assay.targets.tsv"
        assert payload["outputs"]["transition_tsv"] == "assay.transitions.tsv"
        assert payload["outputs"]["transition_qc_tsv"] == "assay.transition_qc.tsv"
        assert payload["outputs"]["fragment_ratio_tsv"] == "assay.fragments.tsv"
        assert payload["outputs"]["retention_tsv"] == "assay.retention.tsv"
        assert payload["outputs"]["replicate_cv_tsv"] == "assay.replicate_cv.tsv"
        assert payload["outputs"]["unreliable_tsv"] == "assay.unreliable.tsv"
        assert Path("assay.summary.tsv").exists()
        assert Path("assay.targets.tsv").exists()
        assert Path("assay.transitions.tsv").exists()
        assert Path("assay.transition_qc.tsv").exists()
        assert Path("assay.fragments.tsv").exists()
        assert Path("assay.retention.tsv").exists()
        assert Path("assay.replicate_cv.tsv").exists()
        assert Path("assay.unreliable.tsv").exists()
        assert "Skyline\t2\t4\t8\t3\t8\t16\t10\t14\t8\t2\t4\t1\t6\t2" in Path(
            "assay.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r1\ttreatment\t2\t2\t1\ty7\ty8\t102000" in Path(
            "assay.targets.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r2\t1\t2\t0.5" in Path(
            "assay.transitions.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r2\ttreatment\ty8\tfalse" in Path(
            "assay.transition_qc.tsv"
        ).read_text(encoding="utf-8")
        assert "PEPTIDEK/2\ttreat_r1\ty8\t12000\t114000\t0.105263\t0.236842\t0.131579\ttrue" in Path(
            "assay.fragments.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\ttreat_r2\t1\t20.2\t18.2\t2\ttrue" in Path(
            "assay.retention.tsv"
        ).read_text(encoding="utf-8")
        assert "ACDMPEP/3\ttreatment\t2\t2\t35000\t0.525279\ttrue" in Path(
            "assay.replicate_cv.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "PEPTIDEK/2\ttreat_r1\ttreatment\ty8\tinterference\tfewer than two passing transitions support the target; fragment-ion ratios deviate from the target reference pattern; source quality flags require review"
            in Path("assay.unreliable.tsv").read_text(encoding="utf-8")
        )


def test_dia_dda_compare_command_emits_overlap_conflict_and_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "dia_dda_comparison_diann.tsv",
            "dia_dda_comparison_diann.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dda_psms.tsv",
            "dia_dda_comparison_dda_psms.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dia_differential.tsv",
            "dia_dda_comparison_dia_differential.tsv",
        )
        shutil.copy(
            workflow_dir / "dia_dda_comparison_dda_differential.tsv",
            "dia_dda_comparison_dda_differential.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-dda-compare",
                "dia_dda_comparison_diann.tsv",
                "dia_dda_comparison_dda_psms.tsv",
                "--dia-differential-tsv",
                "dia_dda_comparison_dia_differential.tsv",
                "--dda-differential-tsv",
                "dia_dda_comparison_dda_differential.tsv",
                "--summary-tsv-out",
                "dia_dda.summary.tsv",
                "--protein-overlap-tsv-out",
                "dia_dda.protein.tsv",
                "--peptide-overlap-tsv-out",
                "dia_dda.peptide.tsv",
                "--correlation-tsv-out",
                "dia_dda.correlation.tsv",
                "--exclusive-tsv-out",
                "dia_dda.exclusive.tsv",
                "--conflicts-tsv-out",
                "dia_dda.conflicts.tsv",
                "--differential-tsv-out",
                "dia_dda.differential.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dia_source_name"] == "DIA-NN"
        assert payload["dda_source_name"] == "DDA PSM"
        assert payload["summary"]["shared_protein_count"] == 2
        assert payload["summary"]["shared_peptide_count"] == 2
        assert payload["summary"]["conflicting_peptide_count"] == 1
        assert payload["summary"]["shared_intensity_correlation_entry_count"] == 5
        assert payload["summary"]["exclusive_evidence_entry_count"] == 6
        assert payload["summary"]["conflicting_evidence_entry_count"] == 1
        assert payload["summary"]["conflicting_differential_count"] == 1
        assert payload["outputs"]["summary_tsv"] == "dia_dda.summary.tsv"
        assert payload["outputs"]["protein_overlap_tsv"] == "dia_dda.protein.tsv"
        assert payload["outputs"]["peptide_overlap_tsv"] == "dia_dda.peptide.tsv"
        assert payload["outputs"]["correlation_tsv"] == "dia_dda.correlation.tsv"
        assert payload["outputs"]["exclusive_tsv"] == "dia_dda.exclusive.tsv"
        assert payload["outputs"]["conflicts_tsv"] == "dia_dda.conflicts.tsv"
        assert payload["outputs"]["differential_tsv"] == "dia_dda.differential.tsv"
        assert Path("dia_dda.summary.tsv").exists()
        assert Path("dia_dda.protein.tsv").exists()
        assert Path("dia_dda.peptide.tsv").exists()
        assert Path("dia_dda.correlation.tsv").exists()
        assert Path("dia_dda.exclusive.tsv").exists()
        assert Path("dia_dda.conflicts.tsv").exists()
        assert Path("dia_dda.differential.tsv").exists()
        assert "DIA-NN\tDDA PSM\t4\t4\t2\t2\t2\t4\t4\t2\t1\t1\t1\t6\t1\t5\t2\t3\t4\t1\t1\t1\t1" in Path(
            "dia_dda.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P55555\tdia_only\t2\t0\t2e+06\t0" in Path(
            "dia_dda.protein.tsv"
        ).read_text(encoding="utf-8")
        assert "CONFLICTSEQ\tconflicting\t2\t2\t1.02e+06\t930000\tP77777\tP88888" in Path(
            "dia_dda.peptide.tsv"
        ).read_text(encoding="utf-8")
        assert "protein\tP22222\t2\t1.23e+06\t826000\t1" in Path(
            "dia_dda.correlation.tsv"
        ).read_text(encoding="utf-8")
        assert "dia\tpeptide\tDIAONLY\t2\t1.46e+06\tP55555" in Path(
            "dia_dda.exclusive.tsv"
        ).read_text(encoding="utf-8")
        assert "peptide\tCONFLICTSEQ\tconflicting\tprotein_assignment_mismatch" in Path(
            "dia_dda.conflicts.tsv"
        ).read_text(encoding="utf-8")
        assert "protein\tP44444\tcontrol\ttreatment\ttreatment_vs_control\tconflicting\t1.1\t-1.2\t0.02\t0.03\ttrue\ttrue\topposite\tdifferential_direction_mismatch" in Path(
            "dia_dda.differential.tsv"
        ).read_text(encoding="utf-8")


def test_biological_report_command_emits_report_directory_and_manifest() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "biological_report_features.tsv",
            "biological_report_features.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "biological-report",
                "biological_report_features.tsv",
                "biological_report.design.tsv",
                "biological_report_reference.fasta",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["protein_count"] == 5
        assert payload["report"]["summary"]["significant_protein_count"] >= 3
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        assert payload["export_manifest"]["go_summary_included"] is True
        report_dir = Path("biological_report")
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report_summary.tsv").exists()
        assert (report_dir / "biological_differential.tsv").exists()
        assert (report_dir / "biological_annotations.tsv").exists()
        assert (report_dir / "biological_go_terms.tsv").exists()
        assert (report_dir / "biological_pathway_entries.tsv").exists()
        assert (report_dir / "biological_complex_entries.tsv").exists()
        assert (report_dir / "biological_heatmap_matrix.tsv").exists()
        assert (report_dir / "biological_sample_pca_scores.tsv").exists()
        assert (report_dir / "biological_volcano.html").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "annotation_entry_count" in (
            report_dir / "biological_report_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "gene_symbol" in (
            report_dir / "biological_annotations.tsv"
        ).read_text(encoding="utf-8")
        assert "go_term_id" in (
            report_dir / "biological_go_terms.tsv"
        ).read_text(encoding="utf-8")
        assert "pathway_id" in (
            report_dir / "biological_pathway_entries.tsv"
        ).read_text(encoding="utf-8")
        assert "complex_id" in (
            report_dir / "biological_complex_entries.tsv"
        ).read_text(encoding="utf-8")
        assert "Volcano plot:" in (
            report_dir / "biological_volcano.html"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_dda_biological_report_command_emits_psm_parsimony_lfq_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "dda_biological_results.tsv",
            "dda_biological_results.tsv",
        )
        shutil.copy(
            workflow_dir / "dda_biological_mapping.json",
            "dda_biological_mapping.json",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dda-biological-report",
                "dda_biological_results.tsv",
                "biological_report.design.tsv",
                "biological_report_reference.fasta",
                "--adapter-kind",
                "generic",
                "--mapping-path",
                "dda_biological_mapping.json",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "dda_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["accepted_psm_count"] == 30
        assert payload["report"]["summary"]["filtered_psm_count"] == 3
        assert payload["report"]["summary"]["inferred_protein_count"] == 5
        assert payload["report"]["biological_report"]["summary"][
            "significant_protein_count"
        ] >= 3
        report_dir = Path("dda_biological_report")
        assert (report_dir / "dda_biological_report_manifest.json").exists()
        assert (report_dir / "dda_biological_psms.tsv").exists()
        assert (report_dir / "dda_biological_filtered_psms.tsv").exists()
        assert (report_dir / "dda_parsimony_proteins.tsv").exists()
        assert (report_dir / "dda_protein_lfq_matrix.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "filter_reasons" in (
            report_dir / "dda_biological_filtered_psms.tsv"
        ).read_text(encoding="utf-8")
        assert "selected_protein_count" in (
            report_dir / "dda_parsimony_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id" in (
            report_dir / "dda_protein_lfq_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_diann_biological_report_command_emits_matrix_qc_differential_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-biological-report",
                "diann_biological_report.tsv",
                "diann_biological.design.tsv",
                "biological_report_reference.fasta",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "diann_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["filtered_q_value_row_count"] == 1
        assert payload["report"]["summary"]["precursor_matrix_row_count"] == 5
        assert payload["report"]["summary"]["protein_matrix_row_count"] == 5
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        assert payload["report"]["summary"]["flagged_run_count"] == 0
        report_dir = Path("diann_biological_report")
        assert (report_dir / "diann_biological_report_manifest.json").exists()
        assert (report_dir / "diann_import_summary.tsv").exists()
        assert (report_dir / "diann_precursor_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_precursor_metadata.tsv").exists()
        assert (report_dir / "diann_peptide_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_protein_quantity_matrix.tsv").exists()
        assert (report_dir / "diann_protein_rollup_evidence.tsv").exists()
        assert (report_dir / "diann_run_qc_runs.tsv").exists()
        assert (report_dir / "diann_differential_results.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "accepted_precursor_count" in (
            report_dir / "diann_import_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "precursor_key" in (
            report_dir / "diann_precursor_quantity_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_observation_count" in (
            report_dir / "diann_precursor_metadata.tsv"
        ).read_text(encoding="utf-8")
        assert "peptide_key" in (
            report_dir / "diann_peptide_quantity_matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "rollup_stage" in (
            report_dir / "diann_protein_rollup_evidence.tsv"
        ).read_text(encoding="utf-8")
        assert "run_name\tsample_name\tprecursor_id_count" in (
            report_dir / "diann_run_qc_runs.tsv"
        ).read_text(encoding="utf-8")
        assert "weak_run_flag_count" in (
            report_dir / "diann_run_qc_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tcondition_a\tcondition_b" in (
            report_dir / "diann_differential_results.tsv"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_diann_benchmark_command_reports_count_and_quantity_fidelity() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "diann-benchmark",
                "diann_biological_report.tsv",
                "--summary-tsv-out",
                "diann.benchmark.summary.tsv",
                "--count-comparisons-tsv-out",
                "diann.benchmark.counts.tsv",
                "--protein-quantities-tsv-out",
                "diann.benchmark.proteins.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["precursor_count_matched"] is True
        assert payload["summary"]["q_value_filtering_matched"] is True
        assert payload["summary"]["protein_quantities_matched"] is True
        assert payload["count_comparison_count"] == 5
        assert payload["protein_quantity_comparison_count"] == 30
        assert Path("diann.benchmark.summary.tsv").exists()
        assert Path("diann.benchmark.counts.tsv").exists()
        assert Path("diann.benchmark.proteins.tsv").exists()
        assert "protein_quantities_matched\ttrue" in Path(
            "diann.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "excluded_q_value_rows\t1\t1\ttrue" in Path(
            "diann.benchmark.counts.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tT1\t1600\t1600\t0\ttrue" in Path(
            "diann.benchmark.proteins.tsv"
        ).read_text(encoding="utf-8")


def test_public_case_study_command_emits_summary_and_biological_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "public-case-study",
                "--summary-tsv-out",
                "public_case_study.summary.tsv",
                "--report-dir",
                "public_case_study_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["case_study_id"]
            == "public_case_study:lfq_cohort_biological_case_study"
        )
        assert payload["summary"]["protein_count"] == 3
        assert payload["summary"]["significant_protein_count"] == 1
        assert payload["summary"]["go_enriched_term_count"] == 1
        report_dir = Path("public_case_study_report")
        assert Path("public_case_study.summary.tsv").exists()
        assert (report_dir / "public_case_study_manifest.json").exists()
        assert (report_dir / "public_case_study_summary.tsv").exists()
        assert (report_dir / "biological-report").is_dir()
        assert (
            report_dir / "biological-report" / "biological_report_manifest.json"
        ).exists()
        assert (report_dir / "biological-report" / "biological_report.html").exists()
        assert "public_case_study:lfq_cohort_biological_case_study" in Path(
            "public_case_study.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "biological_report_summary.tsv" in (
            report_dir / "public_case_study_manifest.json"
        ).read_text(encoding="utf-8")
        assert "Biological result report" in (
            report_dir / "biological-report" / "biological_report.html"
        ).read_text(encoding="utf-8")


def test_maxquant_biological_report_command_emits_import_lfq_and_report_assets() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(
            workflow_dir / "biological_report_go.tsv",
            "biological_report_go.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "maxquant-biological-report",
                "evidence.txt",
                "peptides.txt",
                "proteinGroups.txt",
                "design.tsv",
                "biological_report_reference.fasta",
                "--config-path",
                "maxquant_settings.txt",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--output-dir",
                "maxquant_biological_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_rows"] == 6
        assert payload["report"]["summary"]["accepted_protein_group_count"] == 5
        assert payload["report"]["summary"]["filtered_protein_group_count"] == 3
        assert payload["report"]["summary"]["quantified_protein_count"] == 5
        assert payload["report"]["summary"]["go_enriched_term_count"] == 1
        report_dir = Path("maxquant_biological_report")
        assert (report_dir / "maxquant_biological_report_manifest.json").exists()
        assert (report_dir / "maxquant_import_summary.tsv").exists()
        assert (report_dir / "maxquant_accepted_protein_groups.tsv").exists()
        assert (report_dir / "maxquant_filtered_protein_groups.tsv").exists()
        assert (report_dir / "maxquant_lfq_matrix.tsv").exists()
        assert (report_dir / "biological_report_manifest.json").exists()
        assert (report_dir / "biological_report.html").exists()
        assert "accepted_evidence_count" in (
            report_dir / "maxquant_import_summary.tsv"
        ).read_text(encoding="utf-8")
        assert "filter_reasons" in (
            report_dir / "maxquant_filtered_protein_groups.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tprotein_refs\tmember_peptides" in (
            report_dir / "maxquant_lfq_matrix.tsv"
        ).read_text(encoding="utf-8")


def test_proteomics_run_command_emits_diann_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "diann",
                "--report",
                "diann_biological_report.tsv",
                "--metadata",
                "diann_biological.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "diann"
        assert payload["run"]["summary"]["protein_count"] == 5
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_run_summary.tsv").exists()
        assert (report_dir / "proteomics_qc_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert "engine\tdiann" in (report_dir / "proteomics_run_summary.tsv").read_text(
            encoding="utf-8"
        )


def test_proteomics_run_command_accepts_explicit_case_control_contrast() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "diann_biological_report.tsv",
            "diann_biological_report.tsv",
        )
        shutil.copy(
            workflow_dir / "diann_biological.design.tsv",
            "diann_biological.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "diann",
                "--report",
                "diann_biological_report.tsv",
                "--metadata",
                "diann_biological.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "case-control:treatment-control",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run"]["summary"]["condition_a"] == "treatment"
        assert payload["run"]["summary"]["condition_b"] == "control"


def test_proteomics_run_command_emits_maxquant_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "maxquant",
                "--report",
                "evidence.txt",
                "--peptides",
                "peptides.txt",
                "--protein-groups",
                "proteinGroups.txt",
                "--metadata",
                "design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--config-path",
                "maxquant_settings.txt",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "maxquant"
        assert payload["run"]["summary"]["protein_count"] == 5
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_run_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert "P04637" in (report_dir / "proteomics_normalized_matrix.tsv").read_text(
            encoding="utf-8"
        )


def test_proteomics_run_command_emits_fragpipe_result_package() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        shutil.copy(
            workflow_dir / "fragpipe_biological_psms.tsv",
            "fragpipe_biological_psms.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report.design.tsv",
            "biological_report.design.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )
        shutil.copy(workflow_dir / "biological_report_go.tsv", "biological_report_go.tsv")
        shutil.copy(
            workflow_dir / "biological_report_pathways.tsv",
            "biological_report_pathways.tsv",
        )
        shutil.copy(
            workflow_dir / "biological_report_complexes.tsv",
            "biological_report_complexes.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "fragpipe",
                "--report",
                "fragpipe_biological_psms.tsv",
                "--metadata",
                "biological_report.design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--go-annotation-tsv",
                "biological_report_go.tsv",
                "--pathway-membership-tsv",
                "biological_report_pathways.tsv",
                "--complex-membership-tsv",
                "biological_report_complexes.tsv",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metadata_rows"] == 6
        assert payload["run"]["engine"] == "fragpipe"
        assert payload["run"]["fragpipe_workflow"]["summary"]["accepted_psm_count"] == 30
        report_dir = Path("proteomics_run")
        assert (report_dir / "proteomics_run_manifest.json").exists()
        assert (report_dir / "proteomics_qc_summary.tsv").exists()
        assert (report_dir / "proteomics_normalized_matrix.tsv").exists()
        assert (report_dir / "proteomics_differential.tsv").exists()
        assert (report_dir / "proteomics_enrichment.tsv").exists()
        assert (report_dir / "proteomics_report.html").exists()
        assert "go\tgene_ontology" in (
            report_dir / "proteomics_enrichment.tsv"
        ).read_text(encoding="utf-8")


def test_proteomics_run_command_rejects_incomplete_maxquant_inputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_dir = FIXTURE_ROOT / "workflow"
        bundle_dir = workflow_dir / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(
            workflow_dir / "biological_report_reference.fasta",
            "biological_report_reference.fasta",
        )

        result = runner.invoke(
            cli,
            [
                "run",
                "--engine",
                "maxquant",
                "--report",
                "evidence.txt",
                "--metadata",
                "design.tsv",
                "--proteins-fasta",
                "biological_report_reference.fasta",
                "--contrast",
                "control-treatment",
                "--out",
                "proteomics_run",
            ],
        )

        assert result.exit_code != 0
        assert "MaxQuant runs require --peptides" in result.output


def test_maxquant_benchmark_command_reports_import_lfq_and_differential_fidelity() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        bundle_dir = FIXTURE_ROOT / "workflow" / "maxquant_biological"
        shutil.copy(bundle_dir / "evidence.txt", "evidence.txt")
        shutil.copy(bundle_dir / "peptides.txt", "peptides.txt")
        shutil.copy(bundle_dir / "proteinGroups.txt", "proteinGroups.txt")
        shutil.copy(bundle_dir / "design.tsv", "design.tsv")
        shutil.copy(bundle_dir / "maxquant_settings.txt", "maxquant_settings.txt")

        result = runner.invoke(
            cli,
            [
                "maxquant-benchmark",
                "evidence.txt",
                "--peptides-txt",
                "peptides.txt",
                "--protein-groups-txt",
                "proteinGroups.txt",
                "--config",
                "maxquant_settings.txt",
                "--design-tsv",
                "design.tsv",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--summary-tsv-out",
                "maxquant.benchmark.summary.tsv",
                "--protein-identity-tsv-out",
                "maxquant.benchmark.proteins.tsv",
                "--filtering-tsv-out",
                "maxquant.benchmark.filtering.tsv",
                "--lfq-tsv-out",
                "maxquant.benchmark.lfq.tsv",
                "--differential-tsv-out",
                "maxquant.benchmark.differential.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["protein_identity_matched"] is True
        assert payload["summary"]["lfq_values_matched"] is True
        assert payload["summary"]["differential_comparison_applied"] is True
        assert payload["summary"]["differential_matched"] is True
        assert payload["filtering_comparison_count"] == 8
        assert payload["lfq_comparison_count"] == 30
        assert payload["differential_comparison_count"] == 5
        assert Path("maxquant.benchmark.summary.tsv").exists()
        assert Path("maxquant.benchmark.proteins.tsv").exists()
        assert Path("maxquant.benchmark.filtering.tsv").exists()
        assert Path("maxquant.benchmark.lfq.tsv").exists()
        assert Path("maxquant.benchmark.differential.tsv").exists()
        assert "lfq_values_matched\ttrue" in Path(
            "maxquant.benchmark.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "CON__KRT1\tfiltered\tfiltered" in Path(
            "maxquant.benchmark.filtering.tsv"
        ).read_text(encoding="utf-8")
        assert "P04637\tT1\t1600\t1600\t0\ttrue" in Path(
            "maxquant.benchmark.lfq.tsv"
        ).read_text(encoding="utf-8")


def test_dia_differential_command_emits_matrices_results_and_plot_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        diann_dir = FIXTURE_ROOT / "search_result_bundles" / "diann"
        format_dir = FIXTURE_ROOT / "formats"
        shutil.copy(
            diann_dir / "diann_differential_report.tsv",
            "diann_differential_report.tsv",
        )
        shutil.copy(
            format_dir / "diann_differential.design.tsv",
            "diann_differential.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "dia-differential",
                "diann_differential_report.tsv",
                "diann_differential.design.tsv",
                "--source-kind",
                "diann",
                "--matrix-tsv-out",
                "dia.raw.tsv",
                "--normalized-matrix-tsv-out",
                "dia.normalized.tsv",
                "--differential-tsv-out",
                "dia.differential.tsv",
                "--qc-summary-tsv-out",
                "dia.qc.tsv",
                "--design-matrix-tsv-out",
                "dia.design.tsv",
                "--design-coefficients-tsv-out",
                "dia.coefficients.tsv",
                "--volcano-tsv-out",
                "dia.volcano.tsv",
                "--volcano-json-out",
                "dia.volcano.json",
                "--volcano-svg-out",
                "dia.volcano.svg",
                "--volcano-html-out",
                "dia.volcano.html",
                "--volcano-top-label-count",
                "1",
                "--sample-balance-tsv-out",
                "dia.balance.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["source_kind"] == "diann"
        assert payload["source_name"] == "DIA-NN"
        assert payload["matrix_summary"]["entity_count"] == 3
        assert payload["normalization_comparison"]["method"] == "median"
        assert payload["qc_summary"]["contrast_count"] == 1
        assert payload["qc_summary"]["significant_entry_count"] == 2
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert payload["differential_abundance"]["condition_b"] == "treatment"
        assert payload["volcano_plot"]["significant_point_count"] == 2
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert payload["outputs"]["matrix_tsv"] == "dia.raw.tsv"
        assert payload["outputs"]["normalized_matrix_tsv"] == "dia.normalized.tsv"
        assert payload["outputs"]["differential_tsv"] == "dia.differential.tsv"
        assert payload["outputs"]["qc_summary_tsv"] == "dia.qc.tsv"
        assert payload["outputs"]["design_matrix_tsv"] == "dia.design.tsv"
        assert payload["outputs"]["design_coefficients_tsv"] == "dia.coefficients.tsv"
        assert payload["outputs"]["volcano_tsv"] == "dia.volcano.tsv"
        assert payload["outputs"]["volcano_json"] == "dia.volcano.json"
        assert payload["outputs"]["volcano_svg"] == "dia.volcano.svg"
        assert payload["outputs"]["volcano_html"] == "dia.volcano.html"
        assert payload["outputs"]["sample_balance_tsv"] == "dia.balance.tsv"
        assert Path("dia.raw.tsv").exists()
        assert Path("dia.normalized.tsv").exists()
        assert Path("dia.differential.tsv").exists()
        assert Path("dia.qc.tsv").exists()
        assert Path("dia.design.tsv").exists()
        assert Path("dia.coefficients.tsv").exists()
        assert Path("dia.volcano.tsv").exists()
        assert Path("dia.volcano.json").exists()
        assert Path("dia.volcano.svg").exists()
        assert Path("dia.volcano.html").exists()
        assert Path("dia.balance.tsv").exists()
        assert "PG001\tP11111\tPESTIDE\t100000\t110000\t400000\t420000" in Path(
            "dia.raw.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tcontrol\ttreatment\t\t2\t2" in Path(
            "dia.differential.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\tpair_id\tintercept" in Path(
            "dia.design.tsv"
        ).read_text(encoding="utf-8")
        assert "PG001\tcondition[treatment]" in Path(
            "dia.coefficients.tsv"
        ).read_text(encoding="utf-8")
        assert "contrast_count\t1" in Path("dia.qc.tsv").read_text(encoding="utf-8")
        assert "raw_p_value" in Path("dia.volcano.tsv").read_text(encoding="utf-8")
        assert "PG001\tP11111\t2.00208\t0.00729495\t0.0136062\t1.86626\ttrue" in Path(
            "dia.volcano.tsv"
        ).read_text(encoding="utf-8")
        assert '"source_kind": "dia"' in Path("dia.volcano.json").read_text(
            encoding="utf-8"
        )
        assert "<svg" in Path("dia.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot: control vs treatment" in Path(
            "dia.volcano.html"
        ).read_text(encoding="utf-8")
        assert "C1\tbefore\t600000\t200000\t100000" in Path(
            "dia.balance.tsv"
        ).read_text(encoding="utf-8")


def test_spectronaut_import_command_reports_samples_quantities_and_modifications() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "spectronaut"
        shutil.copy(fixture_dir / "spectronaut_report.tsv", "spectronaut_report.tsv")
        shutil.copy(
            fixture_dir / "spectronaut_settings.txt",
            "spectronaut_settings.txt",
        )

        result = runner.invoke(
            cli,
            [
                "spectronaut-import",
                "spectronaut_report.tsv",
                "--config",
                "spectronaut_settings.txt",
                "--summary-tsv-out",
                "spectronaut.summary.tsv",
                "--precursor-tsv-out",
                "spectronaut.precursors.tsv",
                "--precursor-quantity-tsv-out",
                "spectronaut.precursor_quantities.tsv",
                "--protein-group-tsv-out",
                "spectronaut.protein_groups.tsv",
                "--protein-group-quantity-tsv-out",
                "spectronaut.protein_group_quantities.tsv",
                "--rejected-tsv-out",
                "spectronaut.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_precursor_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
        assert payload["summary"]["modified_precursor_count"] == 3
        assert payload["summary"]["sample_names"] == ["sample_A", "sample_B"]
        assert payload["summary"]["run_names"] == ["raw_A", "raw_B"]
        assert payload["summary"]["precursor_quantity_count"] == 4
        assert payload["summary"]["protein_group_quantity_count"] == 4
        assert payload["summary"]["precursor_quantity_row_count"] == 4
        assert payload["summary"]["protein_group_quantity_row_count"] == 4
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            payload["normalization"]["adapter"]["display_name"]
            == "Spectronaut review report"
        )
        assert payload["precursor_evidence_rows"] == payload["precursor_rows"]
        assert payload["precursor_rows"][0]["modified_peptide"] == "PES[Phospho]TIDE"
        assert payload["precursor_quantity_rows"][0]["precursor_id"] == "sn_rawA_pestide_2"
        assert payload["protein_group_quantity_rows"][0]["protein_group_id"] == "PG001"
        assert payload["rejected_evidence_rows"] == []
        assert Path("spectronaut.summary.tsv").exists()
        assert Path("spectronaut.precursors.tsv").exists()
        assert Path("spectronaut.precursor_quantities.tsv").exists()
        assert Path("spectronaut.protein_groups.tsv").exists()
        assert Path("spectronaut.protein_group_quantities.tsv").exists()
        assert Path("spectronaut.rejected.tsv").exists()


def test_psm_map_command_reports_unmapped_columns_and_normalized_rows() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )
        shutil.copy(
            fixture_dir / "generic_mapper_mapping.yaml",
            "generic_mapper_mapping.yaml",
        )

        result = runner.invoke(
            cli,
            [
                "psm-map",
                "generic_mapper_results.tsv",
                "--mapping",
                "generic_mapper_mapping.yaml",
                "--normalized-tsv-out",
                "mapped.tsv",
                "--rejected-tsv-out",
                "rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["column_mapping"]["score_orientation"] == "higher_better"
        assert payload["normalization"]["adapter"]["score_orientation"] == "higher_better"
        assert payload["summary"]["accepted_rows"] == 2
        assert payload["summary"]["mapped_run_count"] == 2
        assert payload["summary"]["unmapped_source_columns"] == [
            "analyst_note",
            "instrument",
        ]
        assert payload["mapped_rows"][0]["run_id"] == "run_A"
        assert payload["mapped_rows"][0]["peptide_sequence"] == "PESTIDE"
        assert payload["mapped_rows"][0]["modified_peptide"] == "PES[Phospho]TIDE"
        assert payload["mapped_rows"][1]["target_decoy_label"] == "decoy"
        assert payload["mapped_rows"][1]["target_decoy_contaminant_class"] == "mixed"
        assert payload["mapped_rows"][1]["contaminant_flag"] is True
        assert payload["rejected_evidence_rows"] == []
        assert Path("mapped.tsv").exists()
        assert Path("rejected.tsv").exists()
        assert Path("rejected.tsv").read_text(encoding="utf-8").startswith(
            "source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n"
        )


def test_psm_map_command_blocks_missing_required_mapping() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_adapters"
        shutil.copy(
            fixture_dir / "generic_mapper_results.tsv",
            "generic_mapper_results.tsv",
        )
        Path("generic_mapper_mapping.yaml").write_text(
            "\n".join(
                (
                    "run_id: run_name",
                    "spectrum_id: scan_ref",
                    "peptide: sequence_text",
                    "charge: z",
                    "score: state_score",
                    "protein_refs: accessions",
                    "decoy_label: decoy_state",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "psm-map",
                "generic_mapper_results.tsv",
                "--mapping",
                "generic_mapper_mapping.yaml",
            ],
        )

        assert result.exit_code != 0
        assert "score_orientation" in result.output


def test_openms_import_command_reports_idxml_and_feature_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "search_result_bundles" / "openms"
        shutil.copy(fixture_dir / "openms.idxml", "openms.idxml")
        shutil.copy(fixture_dir / "openms_features.tsv", "openms_features.tsv")

        result = runner.invoke(
            cli,
            [
                "openms-import",
                "openms.idxml",
                "--feature-table",
                "openms_features.tsv",
                "--summary-tsv-out",
                "openms.summary.tsv",
                "--psm-tsv-out",
                "openms.psm.tsv",
                "--protein-tsv-out",
                "openms.protein.tsv",
                "--feature-tsv-out",
                "openms.feature.tsv",
                "--rejected-feature-tsv-out",
                "openms.rejected_features.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["accepted_feature_count"] == 4
        assert payload["summary"]["rejected_feature_count"] == 1
        assert payload["summary"]["feature_sample_count"] == 2
        assert payload["feature_parse_summary"]["rejected_rows"] == 1
        assert payload["psm_rows"][0]["spectrum_id"].endswith("scan=1002")
        assert payload["protein_rows"][0]["target_decoy_label"] == "decoy"
        assert payload["feature_rows"][2]["peptide_sequence"] == "M[Oxidation]PEPTIDE"
        assert payload["rejected_feature_rows"][0]["row_number"] == 6
        assert payload["rejected_feature_rows"][0]["issues"][0]["code"] == "invalid_intensity"
        assert payload["rejected_evidence_rows"][0]["reason_code"] == "invalid_intensity"
        assert Path("openms.summary.tsv").exists()
        assert Path("openms.psm.tsv").exists()
        assert Path("openms.protein.tsv").exists()
        assert Path("openms.feature.tsv").exists()
        assert Path("openms.rejected_features.tsv").exists()
        assert Path("openms.rejected_features.tsv").read_text(
            encoding="utf-8"
        ).startswith("source_file\trow_number\tentity_type\tentity_id\treason_code\tdetail\n")


def test_fdr_command_writes_audit_and_calibration_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "psm"
        shutil.copy(fixture_dir / "fdr_results.tsv", "fdr_results.tsv")

        result = runner.invoke(
            cli,
            [
                "fdr",
                "fdr_results.tsv",
                "--threshold",
                "0.5",
                "--score-orientation",
                "higher_better",
                "--audit-out",
                "audit.json",
                "--calibration-out",
                "calibration.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_psms"] == 3
        assert payload["audit_trail"]["reproducibility_hash"]
        assert Path("audit.json").exists()
        assert Path("calibration.json").exists()


def test_infer_proteins_command_emits_grouping_and_coverage_artifacts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        psm_fixture_dir = FIXTURE_ROOT / "psm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            psm_fixture_dir / "protein_inference_results.tsv",
            "protein_inference_results.tsv",
        )
        shutil.copy(
            fasta_fixture_dir / "protein_inference.fasta", "protein_inference.fasta"
        )

        result = runner.invoke(
            cli,
            [
                "infer-proteins",
                "protein_inference_results.tsv",
                "--threshold",
                "0.05",
                "--fasta",
                "protein_inference.fasta",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_psms"] == 4
        assert len(payload["protein_groups"]) >= 3
        assert {entry["protein_ref"] for entry in payload["parsimony_proteins"]} == {
            "P11111",
            "P22222",
            "P33333",
        }
        assert any(
            entry["canonical_peptide"] == "SHAREDK"
            for entry in payload["razor_assignments"]
        )
        assert any(
            entry["protein_ref"] == "P11111" for entry in payload["protein_coverage"]
        )


def test_quantify_command_emits_quant_matrix_and_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--normalization",
                "median",
                "--imputation",
                "low_intensity",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--differential-tsv-out",
                "quantify.differential.tsv",
                "--batch-effect-summary-tsv-out",
                "quantify.batch_effect_summary.tsv",
                "--batch-effect-batches-tsv-out",
                "quantify.batch_effect_batches.tsv",
                "--batch-effect-components-tsv-out",
                "quantify.batch_effect_components.tsv",
                "--design-matrix-tsv-out",
                "quantify.design.tsv",
                "--design-coefficients-tsv-out",
                "quantify.design_coefficients.tsv",
                "--design-contrasts-tsv-out",
                "quantify.design_contrasts.tsv",
                "--limma-assay-tsv-out",
                "quantify.limma_assay.tsv",
                "--limma-samples-tsv-out",
                "quantify.limma_samples.tsv",
                "--limma-design-tsv-out",
                "quantify.limma_design.tsv",
                "--limma-contrasts-tsv-out",
                "quantify.limma_contrasts.tsv",
                "--msstats-input-tsv-out",
                "quantify.msstats.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["table"]["entity_level"] == "protein"
        assert payload["table"]["normalization_method"] == "median"
        assert payload["missing_summary"]["entries"][0]["zero_count"] == 1
        assert payload["missingness_entity_summary"]["entries"]
        assert payload["missingness_condition_summary"]["entries"]
        assert payload["missingness_intensity_dependence"]["plot_points"]
        assert payload["missingness_mechanism_report"]["entries"]
        assert (
            payload["missingness_mechanism_report"]["summary_counts"][
                "missing_completely_at_random"
            ]
            >= 1
        )
        assert payload["normalization_comparison"]["method"] == "median"
        assert payload["normalization_comparison"]["after"]
        assert payload["normalization_strategy"]["recommended_method"] is not None
        assert payload["imputation_report"]["method"] == "low_intensity"
        assert payload["imputation_report"]["imputed_value_count"] > 0
        assert payload["imputation_sensitivity"]["entries"]
        assert tuple(
            entry["method"] for entry in payload["imputation_sensitivity"]["entries"]
        ) == ("none", "low_intensity", "knn")
        assert payload["imputation_sensitivity"]["overlap_entries"]
        assert payload["imputation_sensitivity"]["changed_significance_entries"]
        assert payload["imputation_sensitivity"]["imputation_dependent_hits"]
        assert payload["batch_effect"]["disposition"] == "ADVISORY"
        assert payload["batch_effect"]["batch_variance_proxy"] >= 0.0
        assert payload["batch_effect"]["principal_components"]
        assert payload["batch_effect"]["batch_correction_blocked"] is False
        assert payload["replicate_correlations"]["entries"]
        assert payload["replicate_qc"]["replicate_cv_report"]["entries"]
        assert payload["replicate_qc"]["sample_pca_report"]["entries"]
        assert payload["replicate_qc"]["condition_clustering_report"] is not None
        assert payload["replicate_cv"]["entries"]
        assert payload["sample_pca"]["entries"]
        assert payload["condition_clustering"]["condition_count"] == 2
        assert payload["design_matrix"]["columns"]
        assert payload["design_model_fit"]["coefficient_entries"]
        assert payload["limma_compatible_package"]["sample_annotations"]
        assert payload["msstats_compatible_input_report"]["rows"]
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert (
            payload["differential_abundance"]["assumption_report"]["test_type"]
            == "linear_model_contrast"
        )
        assert (
            payload["differential_abundance"]["assumption_report"][
                "multiple_testing_scope"
            ]
            == "benjamini_hochberg_report_wide_entities"
        )
        assert payload["differential_abundance"]["contrast_name"] == "control_vs_treatment"
        assert payload["outputs"]["differential_tsv"] == "quantify.differential.tsv"
        assert (
            payload["outputs"]["batch_effect_summary_tsv"]
            == "quantify.batch_effect_summary.tsv"
        )
        assert (
            payload["outputs"]["batch_effect_batches_tsv"]
            == "quantify.batch_effect_batches.tsv"
        )
        assert (
            payload["outputs"]["batch_effect_components_tsv"]
            == "quantify.batch_effect_components.tsv"
        )
        assert payload["outputs"]["design_matrix_tsv"] == "quantify.design.tsv"
        assert (
            payload["outputs"]["design_coefficients_tsv"]
            == "quantify.design_coefficients.tsv"
        )
        assert (
            payload["outputs"]["design_contrasts_tsv"]
            == "quantify.design_contrasts.tsv"
        )
        assert payload["outputs"]["limma_assay_tsv"] == "quantify.limma_assay.tsv"
        assert payload["outputs"]["limma_samples_tsv"] == "quantify.limma_samples.tsv"
        assert payload["outputs"]["limma_design_tsv"] == "quantify.limma_design.tsv"
        assert (
            payload["outputs"]["limma_contrasts_tsv"]
            == "quantify.limma_contrasts.tsv"
        )
        assert payload["outputs"]["msstats_input_tsv"] == "quantify.msstats.tsv"
        assert Path("quantify.differential.tsv").exists()
        assert Path("quantify.batch_effect_summary.tsv").exists()
        assert Path("quantify.batch_effect_batches.tsv").exists()
        assert Path("quantify.batch_effect_components.tsv").exists()
        assert Path("quantify.design.tsv").exists()
        assert Path("quantify.design_coefficients.tsv").exists()
        assert Path("quantify.design_contrasts.tsv").exists()
        assert Path("quantify.limma_assay.tsv").exists()
        assert Path("quantify.limma_samples.tsv").exists()
        assert Path("quantify.limma_design.tsv").exists()
        assert Path("quantify.limma_contrasts.tsv").exists()


def test_quantify_command_reports_confounded_batch_correction_block() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "features.tsv")
        Path("design.tsv").write_text(
            "\n".join(
                [
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-a\torbitrap-b\tsage",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-b\torbitrap-a\tsage",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "features.tsv",
                "--design",
                "design.tsv",
                "--design-batch-field",
                "",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["batch_effect"]["fully_confounded_with_condition"] is True
        assert payload["batch_effect"]["batch_correction_blocked"] is True
        assert payload["batch_effect"]["disposition"] == "ENFORCED"
        assert "batch is fully confounded with condition" in (
            payload["batch_effect"]["batch_warning"] or ""
        )


def test_quantify_command_reports_paired_differential_broken_pairs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("paired_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds\tmissing_reason",
                    "pf001\tC1\tPEPA\tP001\t1000\t2\t500.2\t1200\t",
                    "pf002\tT1\tPEPA\tP001\t1900\t2\t500.2\t1201\t",
                    "pf003\tC2\tPEPA\tP001\t1100\t2\t500.2\t1202\t",
                    "pf004\tT2\tPEPA\tP001\t2200\t2\t500.2\t1203\t",
                    "pf005\tC3\tPEPA\tP001\t900\t2\t500.2\t1204\t",
                    "pf101\tC1\tPEPB\tP002\t500\t2\t600.2\t1300\t",
                    "pf102\tT1\tPEPB\tP002\t850\t2\t600.2\t1301\t",
                    "pf103\tC2\tPEPB\tP002\t520\t2\t600.2\t1302\t",
                    "pf104\tT2\tPEPB\tP002\t900\t2\t600.2\t1303\t",
                    "pf105\tC3\tPEPB\tP002\t510\t2\t600.2\t1304\t",
                )
            ),
            encoding="utf-8",
        )
        Path("paired.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\tpair_id",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage\tpair-1",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-a\torbitrap-a\tsage\tpair-1",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-b\torbitrap-b\tsage\tpair-2",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage\tpair-2",
                    "C3\tcontrol\t3\t1\tc3.mzml\tc3.tsv\tbatch-c\torbitrap-c\tsage\tpair-3",
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "paired_features.tsv",
                "--design",
                "paired.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--design-batch-field",
                "",
                "--differential-tsv-out",
                "paired.differential.tsv",
                "--broken-pairs-tsv-out",
                "paired.broken.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert (
            payload["differential_abundance"]["assumption_report"]["test_type"]
            == "paired_t_test"
        )
        assert payload["differential_abundance"]["broken_pairs"][0]["pair_id"] == "pair-3"
        assert payload["outputs"]["differential_tsv"] == "paired.differential.tsv"
        assert "complete_pair_count" in Path("paired.differential.tsv").read_text(
            encoding="utf-8"
        )
        assert "pair-3" in Path("paired.broken.tsv").read_text(encoding="utf-8")
        assert "P001\tcontrol\ttreatment" in Path(
            "paired.differential.tsv"
        ).read_text(encoding="utf-8")
        assert "contrast_name" in Path("paired.differential.tsv").read_text(
            encoding="utf-8"
        )
        assert payload["outputs"]["broken_pairs_tsv"] == "paired.broken.tsv"
        assert any(
            entry["entity_id"] == "P001" and entry["log2_fold_change"] > 0
            for entry in payload["differential_abundance"]["entries"]
        )


def test_quantify_command_reports_log2_normalization_preparation_explicitly() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "log2_median_centering",
                "--imputation",
                "none",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["table"]["normalization_method"] == "log2_median_centering"
        assert payload["normalization_comparison"]["method"] == "log2_median_centering"
        assert payload["normalization_comparison"]["before_distributions"]
        assert payload["normalization_comparison"]["after_distributions"]
        assert payload["normalization_comparison"]["log_transform_preparation"]
        assert {
            entry["handling_strategy"]
            for entry in payload["normalization_comparison"]["log_transform_preparation"]
        } == {"exclude_nonpositive_values_before_log2_centering"}
        assert all(
            entry["zero_count"] == 1
            for entry in payload["normalization_comparison"]["log_transform_preparation"]
        )
        assert any(
            entry["method"] == "log2_median_centering"
            for entry in payload["normalization_strategy"]["entries"]
        )


def test_quantify_command_reports_group_aware_imputation_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
                "--imputation",
                "group_aware_low_intensity",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["table"]["imputation_method"] == "group_aware_low_intensity"
        assert payload["imputation_report"]["method"] == "group_aware_low_intensity"
        assert payload["imputation_report"]["entries"]
        assert tuple(
            entry["method"] for entry in payload["imputation_sensitivity"]["entries"]
        ) == (
            "none",
            "low_intensity",
            "knn",
            "group_aware_low_intensity",
        )
        first_entry = payload["imputation_report"]["entries"][0]
        assert first_entry["strategy"] == "condition_low_intensity_floor"
        assert first_entry["reference_group"] in {"control", "treatment"}
        imputed_row = next(
            value
            for value in payload["table"]["values"]
            if value["entity_id"] == "P004"
            and value["sample_id"] == "C1"
        )
        assert imputed_row["imputation_provenance"]["method"] == (
            "group_aware_low_intensity"
        )


def test_quantify_command_blocks_confounded_design_matrices() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        Path("confounded.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\tpair_id\ttimepoint\tage_years",
                    "C1\tcontrol\t1\t1\tc1.mzml\tc1.tsv\tbatch-a\torbitrap-a\tsage\tpair-a\tt0\t40",
                    "C2\tcontrol\t2\t1\tc2.mzml\tc2.tsv\tbatch-a\torbitrap-a\tsage\tpair-a\tt0\t40",
                    "T1\ttreatment\t1\t1\tt1.mzml\tt1.tsv\tbatch-b\torbitrap-b\tsage\tpair-b\tt1\t60",
                    "T2\ttreatment\t2\t1\tt2.mzml\tt2.tsv\tbatch-b\torbitrap-b\tsage\tpair-b\tt1\t60",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "confounded.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--design-pairing-field",
                "pair_id",
                "--design-covariate",
                "timepoint",
                "--design-covariate",
                "age_years",
            ],
        )

        assert result.exit_code != 0
        assert "design matrix is confounded or rank-deficient" in result.output


def test_quantify_command_requires_explicit_timepoint_order_for_unordered_labels() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("time_course_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds",
                    "tc001\tc_base_1\tPEPA\tP001\t100\t2\t500.2\t1200",
                    "tc002\tc_base_2\tPEPA\tP001\t110\t2\t500.2\t1201",
                    "tc003\tc_end_1\tPEPA\tP001\t130\t2\t500.2\t1202",
                    "tc004\tc_end_2\tPEPA\tP001\t140\t2\t500.2\t1203",
                    "tc005\tt_base_1\tPEPA\tP001\t100\t2\t500.2\t1204",
                    "tc006\tt_base_2\tPEPA\tP001\t110\t2\t500.2\t1205",
                    "tc007\tt_end_1\tPEPA\tP001\t410\t2\t500.2\t1206",
                    "tc008\tt_end_2\tPEPA\tP001\t430\t2\t500.2\t1207",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("time_course.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\ttimepoint",
                    "c_base_1\tcontrol\t1\t1\tc_base_1.mzml\tc_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_base_2\tcontrol\t2\t1\tc_base_2.mzml\tc_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_end_1\tcontrol\t3\t1\tc_end_1.mzml\tc_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "c_end_2\tcontrol\t4\t1\tc_end_2.mzml\tc_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_base_1\ttreatment\t1\t1\tt_base_1.mzml\tt_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_base_2\ttreatment\t2\t1\tt_base_2.mzml\tt_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_end_1\ttreatment\t3\t1\tt_end_1.mzml\tt_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_end_2\ttreatment\t4\t1\tt_end_2.mzml\tt_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "time_course_features.tsv",
                "--design",
                "time_course.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--design-batch-field",
                "",
                "--time-course-tsv-out",
                "time_course.tsv",
            ],
        )

        assert result.exit_code != 0
        assert "unordered timepoint labels require an explicit order file" in result.output


def test_quantify_command_emits_time_course_differential_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("time_course_features.tsv").write_text(
            "\n".join(
                (
                    "feature_id\tsample_id\tpeptide\tproteins\tintensity\tcharge\tmz\tretention_time_seconds",
                    "tc001\tc_base_1\tPEPA\tP001\t100\t2\t500.2\t1200",
                    "tc002\tc_base_2\tPEPA\tP001\t110\t2\t500.2\t1201",
                    "tc003\tc_end_1\tPEPA\tP001\t130\t2\t500.2\t1202",
                    "tc004\tc_end_2\tPEPA\tP001\t140\t2\t500.2\t1203",
                    "tc005\tt_base_1\tPEPA\tP001\t100\t2\t500.2\t1204",
                    "tc006\tt_base_2\tPEPA\tP001\t110\t2\t500.2\t1205",
                    "tc007\tt_end_1\tPEPA\tP001\t410\t2\t500.2\t1206",
                    "tc008\tt_end_2\tPEPA\tP001\t430\t2\t500.2\t1207",
                    "tc101\tc_base_1\tPEPB\tP002\t200\t2\t600.2\t1300",
                    "tc102\tc_base_2\tPEPB\tP002\t210\t2\t600.2\t1301",
                    "tc103\tc_end_1\tPEPB\tP002\t240\t2\t600.2\t1302",
                    "tc104\tc_end_2\tPEPB\tP002\t250\t2\t600.2\t1303",
                    "tc105\tt_base_1\tPEPB\tP002\t205\t2\t600.2\t1304",
                    "tc106\tt_base_2\tPEPB\tP002\t215\t2\t600.2\t1305",
                    "tc107\tt_end_1\tPEPB\tP002\t245\t2\t600.2\t1306",
                    "tc108\tt_end_2\tPEPB\tP002\t255\t2\t600.2\t1307",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("time_course.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file\tbatch\tinstrument\tsearch_engine\ttimepoint",
                    "c_base_1\tcontrol\t1\t1\tc_base_1.mzml\tc_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_base_2\tcontrol\t2\t1\tc_base_2.mzml\tc_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "c_end_1\tcontrol\t3\t1\tc_end_1.mzml\tc_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "c_end_2\tcontrol\t4\t1\tc_end_2.mzml\tc_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_base_1\ttreatment\t1\t1\tt_base_1.mzml\tt_base_1.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_base_2\ttreatment\t2\t1\tt_base_2.mzml\tt_base_2.tsv\tbatch-a\torbitrap-a\tsage\tbaseline",
                    "t_end_1\ttreatment\t3\t1\tt_end_1.mzml\tt_end_1.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                    "t_end_2\ttreatment\t4\t1\tt_end_2.mzml\tt_end_2.tsv\tbatch-b\torbitrap-b\tsage\tendpoint",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        Path("timepoint.order.txt").write_text(
            "baseline\nendpoint\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "time_course_features.tsv",
                "--design",
                "time_course.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "none",
                "--imputation",
                "none",
                "--design-batch-field",
                "",
                "--design-timepoint-order-file",
                "timepoint.order.txt",
                "--time-course-tsv-out",
                "time_course.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["time_course_differential"] is not None
        assert payload["time_course_differential"]["ordered_timepoints"] == [
            "baseline",
            "endpoint",
        ]
        assert payload["outputs"]["time_course_tsv"] == "time_course.tsv"
        assert Path("time_course.tsv").read_text(encoding="utf-8").startswith(
            "entity_id\tcondition\treference_condition"
        )
        assert "interaction_p_value" in Path("time_course.tsv").read_text(
            encoding="utf-8"
        )


def test_heatmap_matrix_command_emits_normalized_matrix_payload() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "heatmap-matrix",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "heatmap.summary.tsv",
                "--matrix-tsv-out",
                "heatmap.matrix.tsv",
                "--row-metadata-tsv-out",
                "heatmap.rows.tsv",
                "--column-metadata-tsv-out",
                "heatmap.columns.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["heatmap_report"]["summary"]["entity_level"] == "protein"
        assert payload["heatmap_report"]["summary"]["z_scored"] is True
        assert payload["outputs"]["summary_tsv"] == "heatmap.summary.tsv"
        assert payload["outputs"]["matrix_tsv"] == "heatmap.matrix.tsv"
        assert payload["outputs"]["row_metadata_tsv"] == "heatmap.rows.tsv"
        assert payload["outputs"]["column_metadata_tsv"] == "heatmap.columns.tsv"
        assert Path("heatmap.summary.tsv").exists()
        assert Path("heatmap.matrix.tsv").exists()
        assert Path("heatmap.rows.tsv").exists()
        assert Path("heatmap.columns.tsv").exists()
        assert "entity_level\tmeasure_kind\taggregation_method" in Path(
            "heatmap.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "entity_id\tC1\tC2\tT1\tT2" in Path("heatmap.matrix.tsv").read_text(
            encoding="utf-8"
        )
        assert "protein_refs\tmember_peptides" in Path("heatmap.rows.tsv").read_text(
            encoding="utf-8"
        )
        assert "column_index\tsample_id\tcondition" in Path(
            "heatmap.columns.tsv"
        ).read_text(encoding="utf-8")


def test_heatmap_matrix_command_applies_filter_and_missing_value_policy() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "heatmap-matrix",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--protein-ref",
                "P001",
                "--min-observed-fraction",
                "1.0",
                "--no-z-score",
                "--missing-value-policy",
                "drop_rows",
                "--matrix-tsv-out",
                "heatmap.filtered.tsv",
                "--row-metadata-tsv-out",
                "heatmap.rows.tsv",
                "--column-metadata-tsv-out",
                "heatmap.columns.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["heatmap_report"]["summary"]["output_entity_count"] == 1
        assert payload["heatmap_report"]["summary"]["filtered_protein_ref_count"] >= 1
        assert payload["heatmap_report"]["summary"]["z_scored"] is False
        assert (
            payload["heatmap_report"]["summary"]["missing_value_policy"] == "drop_rows"
        )
        assert (
            payload["heatmap_report"]["column_metadata"][0]["missing_value_policy"]
            == "drop_rows"
        )
        assert "P001" in Path("heatmap.filtered.tsv").read_text(encoding="utf-8")
        assert "P002" not in Path("heatmap.filtered.tsv").read_text(encoding="utf-8")
        assert "missing_value_policy" in Path("heatmap.rows.tsv").read_text(
            encoding="utf-8"
        )
        assert "missing_value_policy" in Path("heatmap.columns.tsv").read_text(
            encoding="utf-8"
        )


def test_sample_exploration_command_emits_scores_distances_and_clusters() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "sample-exploration",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "sample_exploration.summary.tsv",
                "--scores-tsv-out",
                "sample_exploration.scores.tsv",
                "--explained-variance-tsv-out",
                "sample_exploration.variance.tsv",
                "--correlations-tsv-out",
                "sample_exploration.correlations.tsv",
                "--distances-tsv-out",
                "sample_exploration.distances.tsv",
                "--clusters-tsv-out",
                "sample_exploration.clusters.tsv",
                "--outliers-tsv-out",
                "sample_exploration.outliers.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert (
            payload["sample_exploration_report"]["summary"]["entity_level"]
            == "protein"
        )
        assert (
            payload["sample_exploration_report"]["summary"][
                "pairwise_correlation_count"
            ]
            == 6
        )
        assert (
            payload["sample_exploration_report"]["summary"][
                "pairwise_distance_count"
            ]
            == 6
        )
        assert payload["sample_exploration_report"]["sample_correlation_report"]["entries"]
        assert "outlier_reasons" in payload["sample_exploration_report"]["sample_pca_report"]["entries"][0]
        assert payload["outputs"]["summary_tsv"] == "sample_exploration.summary.tsv"
        assert payload["outputs"]["scores_tsv"] == "sample_exploration.scores.tsv"
        assert (
            payload["outputs"]["explained_variance_tsv"]
            == "sample_exploration.variance.tsv"
        )
        assert (
            payload["outputs"]["correlations_tsv"]
            == "sample_exploration.correlations.tsv"
        )
        assert (
            payload["outputs"]["distances_tsv"]
            == "sample_exploration.distances.tsv"
        )
        assert payload["outputs"]["clusters_tsv"] == "sample_exploration.clusters.tsv"
        assert payload["outputs"]["outliers_tsv"] == "sample_exploration.outliers.tsv"
        assert Path("sample_exploration.summary.tsv").exists()
        assert Path("sample_exploration.scores.tsv").exists()
        assert Path("sample_exploration.variance.tsv").exists()
        assert Path("sample_exploration.correlations.tsv").exists()
        assert Path("sample_exploration.distances.tsv").exists()
        assert Path("sample_exploration.clusters.tsv").exists()
        assert Path("sample_exploration.outliers.tsv").exists()
        assert "entity_level\tmeasure_kind\taggregation_method" in Path(
            "sample_exploration.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\tpc1\tpc2" in Path(
            "sample_exploration.scores.tsv"
        ).read_text(encoding="utf-8")
        assert "component_index\tcomponent_label\texplained_variance_ratio" in Path(
            "sample_exploration.variance.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id_a\tsample_id_b\tcondition_a\tcondition_b" in Path(
            "sample_exploration.correlations.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id_a\tsample_id_b\tcondition_a\tcondition_b" in Path(
            "sample_exploration.distances.tsv"
        ).read_text(encoding="utf-8")
        assert "merge_order\tmember_sample_ids\tleft_sample_ids\tright_sample_ids" in Path(
            "sample_exploration.clusters.tsv"
        ).read_text(encoding="utf-8")
        assert "sample_id\tcondition\tbatch\toutlier_reasons" in Path(
            "sample_exploration.outliers.tsv"
        ).read_text(encoding="utf-8")


def test_power_estimate_command_emits_variance_and_effect_size_grid() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        result = runner.invoke(
            cli,
            [
                "power-estimate",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--replicates-per-condition",
                "2",
                "--replicates-per-condition",
                "4",
                "--replicates-per-condition",
                "6",
                "--summary-tsv-out",
                "power.summary.tsv",
                "--variance-tsv-out",
                "power.variance.tsv",
                "--effect-size-grid-tsv-out",
                "power.grid.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["power_estimation_report"]["summary"]["entity_level"] == "protein"
        assert payload["power_estimation_report"]["variance_entries"]
        assert payload["power_estimation_report"]["effect_size_grid"]
        assert (
            payload["power_estimation_report"]["summary"][
                "weaker_power_with_fewer_replicates"
            ]
            is True
        )
        assert payload["outputs"]["summary_tsv"] == "power.summary.tsv"
        assert payload["outputs"]["variance_tsv"] == "power.variance.tsv"
        assert payload["outputs"]["effect_size_grid_tsv"] == "power.grid.tsv"
        assert Path("power.summary.tsv").exists()
        assert Path("power.variance.tsv").exists()
        assert Path("power.grid.tsv").exists()
        assert "fdr_target\ttarget_power" in Path("power.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "entity_id\tprotein_refs\tobserved_sample_count" in Path(
            "power.variance.tsv"
        ).read_text(encoding="utf-8")
        assert "replicates_per_condition\tevaluable_entity_count" in Path(
            "power.grid.tsv"
        ).read_text(encoding="utf-8")


def test_quantify_command_emits_multi_condition_differential_collection() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "multi_condition_ms1_features.tsv",
            "multi_condition_ms1_features.tsv",
        )
        shutil.copy(
            fixture_dir / "multi_condition.design.tsv",
            "multi_condition.design.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "quantify",
                "multi_condition_ms1_features.tsv",
                "--design",
                "multi_condition.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "sum",
                "--normalization",
                "median",
                "--differential-tsv-out",
                "quantify.multi_condition.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["design_matrix"] is not None
        assert payload["design_model_fit"] is not None
        assert payload["differential_abundance"] is None
        assert payload["differential_abundance_multi_condition"] is not None
        assert payload["outputs"]["differential_tsv"] == "quantify.multi_condition.tsv"
        assert Path("quantify.multi_condition.tsv").exists()
        tsv = Path("quantify.multi_condition.tsv").read_text(encoding="utf-8")
        assert "P001\tcontrol\trescue" in tsv
        assert "P001\tcontrol\ttreatment" in tsv
        assert (
            payload["differential_abundance_multi_condition"]["condition_count"] == 3
        )
        assert len(payload["differential_abundance_multi_condition"]["reports"]) == 3
        assert all(
            entry["adjusted_p_value"] is not None
            for report in payload["differential_abundance_multi_condition"]["reports"]
            for entry in report["entries"]
        )


def test_quantify_command_validates_imported_statistical_backend_results() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")
        shutil.copy(fixture_dir / "limma_results.tsv", "limma_results.tsv")
        shutil.copy(fixture_dir / "msstats_results.tsv", "msstats_results.tsv")

        result = runner.invoke(
            cli,
            [
                "quantify",
                "ms1_features.tsv",
                "--design",
                "quant.design.tsv",
                "--entity-level",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--normalization",
                "median",
                "--imputation",
                "low_intensity",
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
                "--limma-results",
                "limma_results.tsv",
                "--msstats-results",
                "msstats_results.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["limma_result_import"]["row_count"] == 2
        assert payload["msstats_result_import"]["row_count"] == 2
        assert payload["limma_validation"]["matched_row_count"] == 2
        assert payload["limma_validation"]["directionally_concordant_count"] == 2
        assert payload["msstats_validation"]["matched_row_count"] == 2
        assert payload["msstats_validation"]["directionally_concordant_count"] == 2
        assert (
            payload["limma_validation"]["mean_absolute_log2_fold_change_delta"]
            is not None
        )
        assert (
            payload["msstats_validation"]["mean_absolute_log2_fold_change_delta"]
            is not None
        )


def test_peptide_matrix_command_emits_feature_backed_matrix_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_features.tsv",
            "peptide_matrix_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_features.tsv",
                "--input-kind",
                "feature",
                "--grouping-mode",
                "modified_peptide",
                "--separate-charge-states",
                "--summary-tsv-out",
                "peptide_matrix.summary.tsv",
                "--matrix-tsv-out",
                "peptide_matrix.matrix.tsv",
                "--missingness-tsv-out",
                "peptide_matrix.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["peptide_row_count"] == 4
        assert Path("peptide_matrix.summary.tsv").exists()
        assert Path("peptide_matrix.matrix.tsv").exists()
        assert Path("peptide_matrix.missingness.tsv").exists()
        assert "feature\tmodified_peptide\ttrue\tsum" in Path(
            "peptide_matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "PEM[Oxidation]TIDE/z2" in Path("peptide_matrix.matrix.tsv").read_text(
            encoding="utf-8"
        )


def test_peptide_matrix_command_emits_psm_backed_matrix_and_skipped_counts() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_psms.tsv",
            "peptide_matrix_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_psms.tsv",
                "--input-kind",
                "psm",
                "--grouping-mode",
                "modified_peptide",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "peptide_matrix_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["accepted_source_record_count"] == 5
        assert payload["report"]["summary"]["skipped_source_record_count"] == 2
        assert payload["report"]["rows"][0]["values"]
        summary_tsv = Path("peptide_matrix_psm.summary.tsv").read_text(encoding="utf-8")
        assert "skipped_source_record_count" in summary_tsv
        assert (
            "psm\tmodified_peptide\tfalse\tsum\t5\t2\t2\t2\t3\t0\t1\t0\t" in summary_tsv
        )


def test_peptide_matrix_command_emits_precursor_mask_and_aggregation_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_precursors.tsv",
            "peptide_matrix_precursors.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "peptide-matrix",
                "peptide_matrix_precursors.tsv",
                "--input-kind",
                "precursor",
                "--grouping-mode",
                "modified_peptide",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--summary-tsv-out",
                "peptide_matrix_precursor.summary.tsv",
                "--missingness-mask-tsv-out",
                "peptide_matrix_precursor.mask.tsv",
                "--aggregation-table-tsv-out",
                "peptide_matrix_precursor.aggregation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "precursor"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["filtered_cell_count"] == 1
        assert payload["report"]["summary"]["missing_cell_count"] == 1
        assert payload["report"]["aggregation_entries"][0]["aggregation_method"] == "top_n"
        assert Path("peptide_matrix_precursor.summary.tsv").exists()
        assert Path("peptide_matrix_precursor.mask.tsv").exists()
        assert Path("peptide_matrix_precursor.aggregation.tsv").exists()
        assert "precursor\tmodified_peptide\tfalse\ttop_n\t7\t0\t3\t2\t4\t0\t1\t1\t" in Path(
            "peptide_matrix_precursor.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "missing_not_observed" in Path(
            "peptide_matrix_precursor.mask.tsv"
        ).read_text(encoding="utf-8")
        assert "ppq001;ppq002" in Path(
            "peptide_matrix_precursor.aggregation.tsv"
        ).read_text(encoding="utf-8")


def test_protein_matrix_command_emits_feature_backed_rollup_and_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_matrix_features.tsv",
            "protein_matrix_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-matrix",
                "protein_matrix_features.tsv",
                "--input-kind",
                "feature",
                "--target-kind",
                "protein",
                "--aggregation",
                "top_n",
                "--top-n",
                "2",
                "--unique-peptide-only",
                "--summary-tsv-out",
                "protein_matrix.summary.tsv",
                "--matrix-tsv-out",
                "protein_matrix.matrix.tsv",
                "--missingness-tsv-out",
                "protein_matrix.missingness.tsv",
                "--contributions-tsv-out",
                "protein_matrix.contributions.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 8
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["report"]["summary"]["unique_only"] is True
        assert Path("protein_matrix.summary.tsv").exists()
        assert Path("protein_matrix.matrix.tsv").exists()
        assert Path("protein_matrix.missingness.tsv").exists()
        assert Path("protein_matrix.contributions.tsv").exists()
        assert (
            payload["report"]["rows"][0]["values"][0]["shared_peptide_policy"]
            == "unique_only"
        )
        assert "feature\tmodified_peptide\tprotein\tfalse\ttop_n\ttrue" in Path(
            "protein_matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P1\tprotein\tP1\t2\t2\t0\tPEPAAK;PEPMTK\t1600\t2100" in Path(
            "protein_matrix.matrix.tsv"
        ).read_text(encoding="utf-8")
        assert "included_by_policy" in Path(
            "protein_matrix.contributions.tsv"
        ).read_text(encoding="utf-8")


def test_protein_matrix_command_emits_psm_backed_group_rollup() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "peptide_matrix_psms.tsv",
            "peptide_matrix_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-matrix",
                "peptide_matrix_psms.tsv",
                "--input-kind",
                "psm",
                "--target-kind",
                "protein_group",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "protein_matrix_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 7
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 1
        assert payload["report"]["rows"][0]["target_kind"] == "protein_group"
        summary_tsv = Path("protein_matrix_psm.summary.tsv").read_text(encoding="utf-8")
        assert "target_kind" in summary_tsv
        assert "psm\tmodified_peptide\tprotein_group\tfalse\tsum\tfalse" in summary_tsv


def test_protein_lfq_command_emits_feature_backed_matrix_and_pairwise_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_lfq_features.tsv",
            "protein_lfq_features.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-lfq",
                "protein_lfq_features.tsv",
                "--input-kind",
                "feature",
                "--target-kind",
                "protein",
                "--minimum-shared-peptides",
                "2",
                "--summary-tsv-out",
                "protein_lfq.summary.tsv",
                "--matrix-tsv-out",
                "protein_lfq.matrix.tsv",
                "--pairwise-tsv-out",
                "protein_lfq.pairwise.tsv",
                "--missingness-tsv-out",
                "protein_lfq.missingness.tsv",
                "--disconnected-components-tsv-out",
                "protein_lfq.disconnected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "feature"
        assert payload["accepted_source_records"] == 10
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["aggregation_method"] == "sum"
        assert payload["report"]["summary"]["protein_row_count"] == 2
        assert payload["report"]["summary"]["total_pairwise_ratio_count"] == 2
        assert Path("protein_lfq.summary.tsv").exists()
        assert Path("protein_lfq.matrix.tsv").exists()
        assert Path("protein_lfq.pairwise.tsv").exists()
        assert Path("protein_lfq.missingness.tsv").exists()
        assert Path("protein_lfq.disconnected.tsv").exists()
        assert "feature\tmodified_peptide\tprotein\tfalse\tsum\tfalse\t2" in Path(
            "protein_lfq.summary.tsv"
        ).read_text(encoding="utf-8")
        assert (
            "P1\tprotein\tP1\t3\t3\t0\t2\t1\tPEPAAK;PEPCCK;PEPVVK\t447.214\t894.427\t223.607"
            in Path("protein_lfq.matrix.tsv").read_text(encoding="utf-8")
        )
        assert "P1\tprotein\tS1\tS2\t2\t1\t2\tPEPAAK;PEPVVK" in Path(
            "protein_lfq.pairwise.tsv"
        ).read_text(encoding="utf-8")
        disconnected_tsv = Path("protein_lfq.disconnected.tsv").read_text(
            encoding="utf-8"
        )
        assert (
            "P2\tprotein\tP2\t1\tS1\tS2;S3\t1\t0\tDISCAAK" in disconnected_tsv
        )
        assert (
            "P2\tprotein\tP2\t2\tS2\tS1;S3\t1\t0\tDISCAAK" in disconnected_tsv
        )
        assert (
            "P2\tprotein\tP2\t3\tS3\tS1;S2\t1\t0\tDISCVVK" in disconnected_tsv
        )
        assert (
            payload["outputs"]["disconnected_components_tsv"]
            == "protein_lfq.disconnected.tsv"
        )


def test_protein_lfq_command_emits_psm_backed_group_rollup_and_skipped_rows() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(
            fixture_dir / "protein_lfq_psms.tsv",
            "protein_lfq_psms.tsv",
        )

        result = runner.invoke(
            cli,
            [
                "protein-lfq",
                "protein_lfq_psms.tsv",
                "--input-kind",
                "psm",
                "--target-kind",
                "protein",
                "--run-column",
                "run_id",
                "--spectrum-id-column",
                "spectrum_id",
                "--modified-peptide-column",
                "modified_peptide",
                "--score-column",
                "score",
                "--summary-tsv-out",
                "protein_lfq_psm.summary.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["input_kind"] == "psm"
        assert payload["accepted_source_records"] == 9
        assert payload["rejected_source_records"] == 0
        assert payload["report"]["summary"]["protein_row_count"] == 1
        assert payload["report"]["summary"]["total_pairwise_ratio_count"] == 3
        summary_tsv = Path("protein_lfq_psm.summary.tsv").read_text(encoding="utf-8")
        assert "aggregation_method" in summary_tsv
        assert "psm\tmodified_peptide\tprotein\tfalse\tsum\tfalse\t1" in summary_tsv


def test_ptm_summarize_command_emits_site_reports_and_occupancy() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv", "localization_results.tsv"
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "summarize",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--features",
                "ptm_features.tsv",
                "--threshold",
                "0.1",
                "--flank-size",
                "3",
                "--occupancy-summary-tsv-out",
                "ptm.occupancy.summary.tsv",
                "--occupancy-tsv-out",
                "ptm.occupancy.tsv",
                "--occupancy-counterpart-tsv-out",
                "ptm.occupancy.counterpart.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert any(
            entry["site_key"] == "P11111:S5:Phospho" for entry in payload["site_table"]
        )
        assert payload["ambiguity_review"]["summary"]["localized_site_count"] == 3
        assert payload["ambiguity_review"]["summary"]["unlocalized_group_count"] == 2
        assert payload["fdr_report"]["entries"][-1]["accepted"] is False
        assert any(
            entry["sample_id"] == "T2" and entry["occupancy_fraction"] == 0.79
            for entry in payload["occupancy"]
        )
        assert payload["occupancy_report"]["summary"]["entry_count"] >= 1
        assert payload["occupancy_counterpart_report"]["entries"]
        assert payload["site_quantification"]["ambiguity_policy"] == "preserve"
        assert payload["site_group_quantification"]["summary"]["group_row_count"] == 2
        assert any(
            row["site_key"] == "P11111:S5:Phospho"
            for row in payload["site_quantification"]["rows"]
        )
        assert any(
            row["group_key"] == "P11111:Phospho:17|18|19"
            for row in payload["site_group_quantification"]["rows"]
        )
        assert "entry_count" in Path("ptm.occupancy.summary.tsv").read_text()
        assert "S[Phospho]PEPTIDEK" in Path("ptm.occupancy.tsv").read_text()
        assert "counterpart_status" in Path(
            "ptm.occupancy.counterpart.tsv"
        ).read_text()


def test_ptm_parse_peptide_command_emits_explicit_site_records() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ptm",
            "parse-peptide",
            "[Acetyl]-M[Oxidation]STY[Phospho]K",
            "--protein-ref",
            "P22222",
            "--peptide-start-position",
            "15",
            "--sample-id",
            "T1",
            "--spectrum-id",
            "scan=ptm-peptide-002",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["canonical_peptide"] == "[Acetyl]-M[Oxidation]STY[Phospho]K"
    assert payload["modification_names"] == ["Acetyl", "Oxidation", "Phospho"]
    assert [site["residue"] for site in payload["sites"]] == ["M", "M", "Y"]
    assert [site["peptide_position"] for site in payload["sites"]] == [1, 1, 4]
    assert [site["protein_position"] for site in payload["sites"]] == [15, 15, 18]


def test_ptm_parse_peptides_command_emits_review_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        shutil.copy(ptm_fixture_dir / "ptm_peptides.tsv", "ptm_peptides.tsv")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "parse-peptides",
                "ptm_peptides.tsv",
                "--summary-tsv-out",
                "ptm_peptides.summary.tsv",
                "--record-tsv-out",
                "ptm_peptides.records.tsv",
                "--site-tsv-out",
                "ptm_peptides.sites.tsv",
                "--rejected-tsv-out",
                "ptm_peptides.rejected.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"] == {
            "accepted_record_count": 3,
            "rejected_row_count": 2,
            "parsed_site_count": 5,
            "protein_mapped_site_count": 4,
            "multi_modified_record_count": 1,
        }
        assert Path("ptm_peptides.summary.tsv").read_text().splitlines()[1] == "3\t2\t5\t4\t1"
        assert "AAS[Phospho]PEP" in Path("ptm_peptides.records.tsv").read_text()
        assert "UNIMOD:21\tS\t3\t6\tanywhere" in Path(
            "ptm_peptides.sites.tsv"
        ).read_text()
        assert "invalid_peptide_start_position" in Path(
            "ptm_peptides.rejected.tsv"
        ).read_text()


def test_ptm_map_sites_command_emits_site_mapping_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--mapping-tsv-out",
                "ptm.mapping.tsv",
                "--exact-mapping-tsv-out",
                "ptm.exact.tsv",
                "--ambiguous-mapping-tsv-out",
                "ptm.ambiguous.tsv",
                "--unmapped-tsv-out",
                "ptm.unmapped.tsv",
                "--site-table-tsv-out",
                "ptm.site_table.tsv",
                "--ambiguity-tsv-out",
                "ptm.ambiguity.tsv",
                "--coverage-tsv-out",
                "ptm.coverage.tsv",
                "--validation-tsv-out",
                "ptm.validation.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["mapping_count"] == 10
        assert payload["exact_mapping_count"] == 6
        assert payload["ambiguous_mapping_count"] == 4
        assert payload["unmapped_peptide_count"] == 0
        assert payload["site_count"] == 5
        assert payload["ambiguity_count"] == 2
        assert payload["ambiguity_review"]["summary"]["possible_residue_count"] == 6
        assert payload["coordinate_validation"]["valid"] is True
        assert "shared_peptide" in Path("ptm.mapping.tsv").read_text()
        assert "scan=ptm-001" in Path("ptm.exact.tsv").read_text()
        assert "scan=ptm-005" in Path("ptm.ambiguous.tsv").read_text()
        assert Path("ptm.unmapped.tsv").read_text().splitlines()[0].startswith(
            "spectrum_id\tsample_id\tlocalized_peptide"
        )
        assert "P11111:S5:Phospho" in Path("ptm.site_table.tsv").read_text()
        assert (
            "P11111:Phospho:17|18|19"
            in Path("ptm.ambiguity.tsv").read_text()
        )
        assert "S;T;Y" in Path("ptm.ambiguity.tsv").read_text()
        assert "scan=ptm-001" in Path("ptm.coverage.tsv").read_text()
        assert (
            Path("ptm.validation.tsv").read_text().splitlines()[0]
            == "spectrum_id\tprotein_ref\tsite_key\tcode\tmessage"
        )


def test_ptm_map_sites_command_exports_separate_multi_modified_candidates() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "multi_localization_results.tsv",
            "multi_localization_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "multi_localization_results.tsv",
                "ptm_sites.fasta",
                "--candidate-tsv-out",
                "ptm.candidates.tsv",
                "--mapping-tsv-out",
                "ptm.mapping.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 1
        assert payload["site_candidate_count"] == 2
        assert payload["mapping_count"] == 4
        assert "Phospho\tUNIMOD:21\tS\t2" in Path("ptm.candidates.tsv").read_text()
        assert "Phospho\tUNIMOD:21\tY\t4" in Path("ptm.candidates.tsv").read_text()
        assert "\t2\t17\t" in Path("ptm.mapping.tsv").read_text()
        assert "\t4\t19\t" in Path("ptm.mapping.tsv").read_text()


def test_ptm_map_sites_command_preserves_exact_shared_and_unmapped_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("mapping_input.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tspectrum_id\tpeptide\tcharge\tscore\tq_value\tproteins\tlocalization_score\tcandidate_sites\tdecoy_label",
                    "C1\tscan=shared-unique\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP11111;P40404\t0.990\t1\ttarget",
                    "C1\tscan=unmapped\tS[Phospho]PEPTIDEK\t2\t110.0\t0.005\tP40404\t0.990\t1\ttarget",
                )
            )
            + "\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "mapping_input.tsv",
                "ptm_sites.fasta",
                "--exact-mapping-tsv-out",
                "ptm.exact.tsv",
                "--ambiguous-mapping-tsv-out",
                "ptm.ambiguous.tsv",
                "--unmapped-tsv-out",
                "ptm.unmapped.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mapping_count"] == 1
        assert payload["exact_mapping_count"] == 1
        assert payload["ambiguous_mapping_count"] == 0
        assert payload["unmapped_peptide_count"] == 1
        assert "scan=shared-unique" in Path("ptm.exact.tsv").read_text()
        assert Path("ptm.ambiguous.tsv").read_text().splitlines() == [
            "spectrum_id\tsample_id\tprotein_ref\tlocalized_peptide\tcanonical_peptide\tmodification_name\tresidue\tpeptide_site_index\tprotein_position\tlocalization_score\tq_value\tcandidate_protein_positions\tambiguous\tshared_peptide\ttarget_decoy_label"
        ]
        assert "scan=unmapped" in Path("ptm.unmapped.tsv").read_text()
        assert "missing_protein_sequence" in Path("ptm.unmapped.tsv").read_text()


def test_ptm_ambiguity_review_command_emits_localized_and_group_quant_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-001": ["b5", "y7"],
                    "scan=ptm-005": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "ambiguity-review",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "--features",
                "ptm_features.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--summary-tsv-out",
                "ptm.ambiguity.summary.tsv",
                "--localized-tsv-out",
                "ptm.localized.tsv",
                "--unlocalized-tsv-out",
                "ptm.unlocalized.tsv",
                "--group-quant-summary-tsv-out",
                "ptm.group_quant.summary.tsv",
                "--group-quant-matrix-tsv-out",
                "ptm.group_quant.matrix.tsv",
                "--group-quant-missingness-tsv-out",
                "ptm.group_quant.missingness.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ambiguity_review"]["summary"]["localized_site_count"] == 3
        assert payload["ambiguity_review"]["summary"]["unlocalized_group_count"] == 2
        assert payload["site_group_quantification"]["summary"]["group_row_count"] == 2
        assert Path("ptm.ambiguity.summary.tsv").read_text().splitlines()[0].startswith(
            "localized_site_count\tunlocalized_group_count"
        )
        assert "P11111:S5:Phospho" in Path("ptm.localized.tsv").read_text()
        assert "P11111:Phospho:17|18|19" in Path("ptm.unlocalized.tsv").read_text()
        assert "group_key\tprotein_ref" in Path("ptm.group_quant.matrix.tsv").read_text()
        assert "sample_id\tobserved_count" in Path(
            "ptm.group_quant.missingness.tsv"
        ).read_text()


def test_ptm_score_localization_command_emits_probability_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        shutil.copy(
            ptm_fixture_dir / "localization_probability_results.tsv",
            "localization_probability_results.tsv",
        )
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-prob-001": ["b5", "y7"],
                    "scan=ptm-prob-002": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "score-localization",
                "localization_probability_results.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--summary-tsv-out",
                "ptm.localization.summary.tsv",
                "--entry-tsv-out",
                "ptm.localization.entries.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 2
        assert (
            payload["localization_scoring"]["entries"][0]["probability_source"]
            == "reported_probability"
        )
        assert (
            payload["localization_scoring"]["entries"][0]["localization_tier"]
            == "high_confidence"
        )
        assert "reported_probability" in Path(
            "ptm.localization.entries.tsv"
        ).read_text()
        assert "localization_tier" in Path(
            "ptm.localization.entries.tsv"
        ).read_text().splitlines()[0]
        assert Path("ptm.localization.summary.tsv").read_text().splitlines()[0] == (
            "entry_count\tambiguous_entry_count\tconfident_entry_count\t"
            "high_confidence_entry_count\tsupported_entry_count\trefused_entry_count\t"
            "multi_phosphorylated_entry_count\tfragment_supported_entry_count"
        )


def test_ptm_summary_and_mapping_commands_accept_localization_probability_column() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_probability_results.tsv",
            "localization_probability_results.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        summarize_result = runner.invoke(
            cli,
            [
                "ptm",
                "summarize",
                "localization_probability_results.tsv",
                "ptm_sites.fasta",
                "--localization-probability-column",
                "localization_probability",
            ],
        )
        map_sites_result = runner.invoke(
            cli,
            [
                "ptm",
                "map-sites",
                "localization_probability_results.tsv",
                "ptm_sites.fasta",
                "--localization-probability-column",
                "localization_probability",
            ],
        )

        assert summarize_result.exit_code == 0
        assert map_sites_result.exit_code == 0
        assert json.loads(summarize_result.output)["accepted_rows"] == 2
        assert json.loads(map_sites_result.output)["accepted_rows"] == 2


def test_ptm_quantify_sites_command_emits_site_matrix_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "quantify-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--ambiguity-policy",
                "exclude",
                "--summary-tsv-out",
                "ptm.site_quant.summary.tsv",
                "--matrix-tsv-out",
                "ptm.site_quant.matrix.tsv",
                "--missingness-tsv-out",
                "ptm.site_quant.missingness.tsv",
                "--excluded-tsv-out",
                "ptm.site_quant.excluded.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["site_quantification"]["ambiguity_policy"] == "exclude"
        assert "P11111:S5:Phospho" in Path("ptm.site_quant.matrix.tsv").read_text()
        assert "P11111:S17:Phospho" in Path("ptm.site_quant.excluded.tsv").read_text()


def test_ptm_estimate_occupancy_command_emits_occupancy_ledgers() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "estimate-occupancy",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "--summary-tsv-out",
                "ptm.occupancy.summary.tsv",
                "--occupancy-tsv-out",
                "ptm.occupancy.tsv",
                "--counterpart-tsv-out",
                "ptm.occupancy.counterpart.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["occupancy_report"]["summary"]["entry_count"] >= 1
        assert "S[Phospho]PEPTIDEK" in Path("ptm.occupancy.tsv").read_text()
        assert "counterpart_status" in Path(
            "ptm.occupancy.counterpart.tsv"
        ).read_text()


def test_ptm_differential_command_emits_site_results_and_volcano() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "differential",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--protein-correction-mode",
                "subtract_unmodified_protein",
                "--design-batch-field",
                "",
                "--results-tsv-out",
                "ptm.differential.tsv",
                "--volcano-tsv-out",
                "ptm.volcano.tsv",
                "--volcano-json-out",
                "ptm.volcano.json",
                "--volcano-svg-out",
                "ptm.volcano.svg",
                "--volcano-html-out",
                "ptm.volcano.html",
                "--volcano-top-label-count",
                "1",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["protein_correction_mode"] == "subtract_unmodified_protein"
        assert payload["volcano_review"]["labeled_point_count"] == 1
        assert "P11111:S5:Phospho" in Path("ptm.differential.tsv").read_text()
        assert "plotted_log2_fold_change" in Path("ptm.volcano.tsv").read_text()
        assert Path("ptm.volcano.json").exists()
        assert Path("ptm.volcano.svg").exists()
        assert Path("ptm.volcano.html").exists()
        assert '"source_kind": "ptm"' in Path("ptm.volcano.json").read_text(
            encoding="utf-8"
        )
        assert "<svg" in Path("ptm.volcano.svg").read_text(encoding="utf-8")
        assert "Volcano plot:" in Path("ptm.volcano.html").read_text(
            encoding="utf-8"
        )


def test_ptm_differential_command_exports_paired_broken_pair_ledger() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("ptm_paired.design.tsv").write_text(
            "\n".join(
                (
                    "sample_id\tcondition\treplicate\tfraction\tspectra_file\tbatch\tpair_id",
                    "C1\tcontrol\t1\t1\tC1.raw\tbatch-a\tpair-1",
                    "C2\tcontrol\t2\t1\tC2.raw\tbatch-a\tpair-2",
                    "T1\ttreated\t1\t1\tT1.raw\tbatch-b\tpair-1",
                    "T2\ttreated\t2\t1\tT2.raw\tbatch-b\tpair-2",
                )
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "differential",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm_paired.design.tsv",
                "--design-pairing-field",
                "pair_id",
                "--design-batch-field",
                "",
                "--broken-pairs-tsv-out",
                "ptm.broken.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["differential_report"]["broken_pairs"] == []
        assert any(
            entry["complete_pair_count"] == 2
            for entry in payload["differential_report"]["entries"]
        )
        assert Path("ptm.broken.tsv").read_text(encoding="utf-8").startswith(
            "condition_a\tcondition_b\tpair_id"
        )


def test_ptm_motif_enrichment_command_emits_windows_terms_and_logo() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "motif-enrichment",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--flank-size",
                "3",
                "--max-adjusted-p-value",
                "1.0",
                "--min-absolute-log2-fold-change",
                "0.5",
                "--direction",
                "upregulated",
                "--window-tsv-out",
                "ptm.motif.windows.tsv",
                "--frequency-tsv-out",
                "ptm.motif.frequency.tsv",
                "--enriched-term-tsv-out",
                "ptm.motif.terms.tsv",
                "--logo-tsv-out",
                "ptm.motif.logo.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["motif_enrichment_report"]["regulated_site_count"] == 1
        assert any(
            term["residue"] == "P" and term["exclusive_to_regulated"]
            for term in payload["motif_enrichment_report"]["enriched_terms"]
        )
        assert "centered_window" in Path("ptm.motif.windows.tsv").read_text()
        assert "regulated_frequency" in Path("ptm.motif.frequency.tsv").read_text()
        assert "exclusive_to_regulated" in Path("ptm.motif.terms.tsv").read_text()
        assert "window_role" in Path("ptm.motif.logo.tsv").read_text()


def test_ptm_annotate_sites_command_emits_mapped_unmapped_and_biology_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(
            ptm_fixture_dir / "ptm_site_annotations.tsv",
            "ptm_site_annotations.tsv",
        )
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")

        result = runner.invoke(
            cli,
            [
                "ptm",
                "annotate-sites",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_site_annotations.tsv",
                "--summary-tsv-out",
                "ptm.annotation.summary.tsv",
                "--mapped-tsv-out",
                "ptm.annotation.mapped.tsv",
                "--unmapped-tsv-out",
                "ptm.annotation.unmapped.tsv",
                "--function-tsv-out",
                "ptm.annotation.function.tsv",
                "--kinase-tsv-out",
                "ptm.annotation.kinase.tsv",
                "--pathway-tsv-out",
                "ptm.annotation.pathway.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["annotation_rows"] == 5
        assert payload["rejected_annotation_rows"] == 1
        assert payload["target_species"] == "Homo sapiens"
        assert payload["mapping_report"]["summary"]["matched_annotation_count"] == 3
        assert "species_mismatch_count" in Path("ptm.annotation.summary.tsv").read_text()
        assert "P11111:S5:Phospho" in Path("ptm.annotation.mapped.tsv").read_text()
        assert "Mus musculus" in Path("ptm.annotation.unmapped.tsv").read_text()
        assert "activation-linked phosphosite" in Path(
            "ptm.annotation.function.tsv"
        ).read_text()
        assert "AKT1" in Path("ptm.annotation.kinase.tsv").read_text()
        assert "MAPK signaling" in Path("ptm.annotation.pathway.tsv").read_text()


def test_ptm_report_command_emits_full_report_bundle() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        ptm_fixture_dir = FIXTURE_ROOT / "ptm"
        fasta_fixture_dir = FIXTURE_ROOT / "fasta"
        shutil.copy(
            ptm_fixture_dir / "localization_results.tsv",
            "localization_results.tsv",
        )
        shutil.copy(ptm_fixture_dir / "ptm_features.tsv", "ptm_features.tsv")
        shutil.copy(ptm_fixture_dir / "ptm.design.tsv", "ptm.design.tsv")
        shutil.copy(fasta_fixture_dir / "ptm_sites.fasta", "ptm_sites.fasta")
        Path("fragment_support.json").write_text(
            json.dumps(
                {
                    "scan=ptm-001": ["b5", "y7"],
                    "scan=ptm-005": ["b2"],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            cli,
            [
                "ptm",
                "report",
                "localization_results.tsv",
                "ptm_sites.fasta",
                "ptm_features.tsv",
                "ptm.design.tsv",
                "--fragment-support-json",
                "fragment_support.json",
                "--protein-correction-mode",
                "subtract_unmodified_protein",
                "--output-dir",
                "ptm_report",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert payload["feature_rows"] == 12
        assert payload["design_rows"] == 4
        assert payload["report"]["summary"]["quantified_site_row_count"] == 5
        assert payload["report"]["summary"]["differential_site_count"] == 5
        assert payload["export_manifest"]["motif_summary_included"] is True
        report_dir = Path("ptm_report")
        assert (report_dir / "ptm_site_workflow_manifest.json").exists()
        assert (report_dir / "ptm_report_manifest.json").exists()
        assert (report_dir / "ptm_site_workflow_summary.tsv").exists()
        assert (report_dir / "ptm_site_workflow_accepted_evidence.tsv").exists()
        assert (report_dir / "ptm_site_workflow_rejected_evidence.tsv").exists()
        assert (report_dir / "ptm_peptides.tsv").exists()
        assert (report_dir / "ptm_sites.tsv").exists()
        assert (report_dir / "ptm_localization.tsv").exists()
        assert (report_dir / "ptm_site_quant_matrix.tsv").exists()
        assert (report_dir / "ptm_differential.tsv").exists()
        assert (report_dir / "ptm_motif_terms.tsv").exists()
        assert "accepted_evidence_count" in (
            report_dir / "ptm_site_workflow_summary.tsv"
        ).read_text()
        assert "S[Phospho]PEPTIDEK" in (report_dir / "ptm_peptides.tsv").read_text()
        assert "P11111:S5:Phospho" in (report_dir / "ptm_sites.tsv").read_text()
        assert "probability_source" in (
            report_dir / "ptm_localization.tsv"
        ).read_text()
        assert "corrected_log2_fold_change" in (
            report_dir / "ptm_differential.tsv"
        ).read_text()
        assert "exclusive_to_regulated" in (
            report_dir / "ptm_motif_terms.tsv"
        ).read_text()


def test_qc_report_command_emits_json_tsv_html_manifest_and_benchmark() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "qc_policy.json",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--design",
                "design.tsv",
                "--policy",
                "qc_policy.json",
                "--tsv-out",
                "qc.tsv",
                "--html-out",
                "qc.html",
                "--manifest-out",
                "qc.manifest.json",
                "--benchmark-out",
                "qc.benchmark.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["run_report"]["run_id"] == "spectra"
        assert payload["run_assessment"]["policy_name"] == "production-demo-qc"
        assert Path("qc.tsv").read_text().startswith("scope\tentity_id\tmetric_key")
        assert "Bijux Proteomics QC Report" in Path("qc.html").read_text()
        manifest = json.loads(Path("qc.manifest.json").read_text())
        benchmark = json.loads(Path("qc.benchmark.json").read_text())
        assert manifest["document_schema"]["document_kind"] == "qc_evidence_manifest"
        assert (
            benchmark["document_schema"]["document_kind"]
            == "proteomics_performance_snapshot"
        )


def test_qc_report_command_reports_structured_policy_errors() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in ("spectra.mgf", "results.tsv", "proteins.fasta"):
            shutil.copy(fixture_dir / name, name)
        Path("bad-policy.json").write_text("{not valid json}\n")

        result = runner.invoke(
            cli,
            [
                "qc",
                "report",
                "spectra.mgf",
                "results.tsv",
                "proteins.fasta",
                "--policy",
                "bad-policy.json",
            ],
        )

        assert result.exit_code != 0
        assert "QC_POLICY_INVALID" in result.output


def test_workflow_plan_command_emits_runtime_bundle_and_sidecar_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "ms1_features.tsv",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "workflow-plan",
                "--proteins",
                "proteins.fasta",
                "--spectra",
                "spectra.mgf",
                "--identifications",
                "results.tsv",
                "--features",
                "ms1_features.tsv",
                "--design",
                "design.tsv",
                "--sample-id",
                "sample-A",
                "--search-adapter",
                "generic",
                "--dag-out",
                "workflow.dag.json",
                "--job-out",
                "workflow.slurm",
                "--checkpoint-out",
                "workflow.checkpoint.json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["manifest"]["workflow_id"].startswith(
            "sample-a-generic-workflow"
        )
        assert payload["dag_plan"]["nodes"][0]["step_kind"] == "validate-inputs"
        assert payload["search_contract"]["adapter_kind"] == "generic"
        assert Path("workflow.dag.json").exists()
        assert "#SBATCH --job-name=" in Path("workflow.slurm").read_text()
        checkpoint = json.loads(Path("workflow.checkpoint.json").read_text())
        assert checkpoint["document_schema"]["document_kind"] == "workflow_checkpoint"


def test_workflow_validate_command_checks_runtime_integrity() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "production_run"
        for name in (
            "spectra.mgf",
            "results.tsv",
            "proteins.fasta",
            "design.tsv",
            "ms1_features.tsv",
        ):
            shutil.copy(fixture_dir / name, name)

        result = runner.invoke(
            cli,
            [
                "workflow-validate",
                "--proteins",
                "proteins.fasta",
                "--spectra",
                "spectra.mgf",
                "--identifications",
                "results.tsv",
                "--features",
                "ms1_features.tsv",
                "--design",
                "design.tsv",
                "--sample-id",
                "sample-A",
                "--search-adapter",
                "generic",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["valid"] is True
        assert "cache-manifest" in payload["checked_surfaces"]
