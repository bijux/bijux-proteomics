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
        peaks=tuple(SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks),
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
            cli, ["fasta-stats", "dedup.fasta", "--mode", "permissive"]
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
        assert Path("production.summary.tsv").read_text().splitlines()[0].startswith(
            "input_record_count\tprotein_count\trejected_record_count"
        )
        assert "1-99\t1\t99\t6\t116" in Path("production.length.tsv").read_text()
        assert (
            "Homo sapiens\t4\t3\t1\t1"
            in Path("production.organism.tsv").read_text()
        )

        dedup_result = runner.invoke(
            cli,
            [
                "fasta-dedup",
                "dedup.fasta",
                "--mode",
                "permissive",
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
        assert shuffle_payload["generation_report"]["target_sequence_collision_count"] == 1

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
            (
                ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\n"
                "MPEPDADAA\n"
            )
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


def test_peptide_index_command_reports_groups_il_equivalence_and_missed_cleavages() -> (
    None
):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("database.fasta").write_text(
            (
                ">sp|P10001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\n"
                "MPEPTLDEKAK\n"
                ">sp|P20001|BETA_HUMAN Beta OS=Homo sapiens GN=BETA\n"
                "AKSHADEQKQQ\n"
                ">sp|P20002|GAMMA_HUMAN Gamma OS=Homo sapiens GN=GAMMA\n"
                "MKSHADEQKLL\n"
            )
        )
        Path("groups.tsv").write_text(
            "accession\tprotein_group\n"
            "P20001\tGROUP_SHARED\n"
            "P20002\tGROUP_SHARED\n"
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
        assert by_query["MPEPTLDEKAK"]["missed_cleavage_counts"] == [1]
        assert by_query["SHADEQK"]["protein_groups"] == ["GROUP_SHARED"]
        assert (
            by_query["SHADEQK"]["audit_class"] == "protein_group_specific"
        )


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


def test_fragment_ions_command_reports_b_y_ions_with_charge_and_tsv() -> None:
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
                "--include-neutral-losses",
                "--tsv-out",
                "fragments.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["counts_by_series"]["b"] > 0
        assert payload["counts_by_series"]["y"] > 0
        assert payload["counts_by_charge"]["1"] > 0
        assert payload["counts_by_charge"]["2"] > 0
        assert payload["neutral_loss_count"] > 0
        assert Path("fragments.tsv").exists()


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


def test_peptide_properties_command_supports_modifications_and_custom_protease() -> None:
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
        assert Path("normalized.jsonl").exists()
        assert Path("normalized.tsv").exists()
        manifest = json.loads(Path("provenance.json").read_text())
        assert (
            manifest["document_schema"]["document_kind"]
            == "search_result_provenance_manifest"
        )


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
        assert payload["annotation"]["matches"]
        assert payload["annotation"]["matched_peak_count"] > 0
        assert payload["annotation"]["explained_intensity_fraction"] > 0.0
        assert Path("annotation.tsv").exists()
        assert Path("plot.json").exists()


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
        assert payload["library_report"]["matches"][0]["reference_spectrum_id"] == "reference"
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
        assert payload["library_report"]["matches"][0]["reference_spectrum_id"] == "best-match"
        assert payload["library_report"]["matches"][0]["classification"] == "duplicate_like"


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
        assert json.loads(psm_result.output)["psm_summary"]["total_psms"] == 3
        assert contaminant_psm_result.exit_code == 0
        contaminant_payload = json.loads(contaminant_psm_result.output)
        assert contaminant_payload["contaminant_report"]["contaminant_psm_count"] == 2
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
                "--condition-a",
                "control",
                "--condition-b",
                "treatment",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_features"] == 32
        assert payload["rejected_features"] == 0
        assert payload["table"]["entity_level"] == "protein"
        assert payload["table"]["normalization_method"] == "median"
        assert payload["missing_summary"]["entries"][0]["zero_count"] == 1
        assert payload["batch_effect"]["disposition"] == "ADVISORY"
        assert payload["replicate_correlations"]["entries"]
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert any(
            entry["entity_id"] == "P001" and entry["log2_fold_change"] > 0
            for entry in payload["differential_abundance"]["entries"]
        )


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
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["accepted_rows"] == 8
        assert any(
            entry["site_key"] == "P11111:S5:Phospho" for entry in payload["site_table"]
        )
        assert len(payload["ambiguity_report"]) == 2
        assert payload["fdr_report"]["entries"][-1]["accepted"] is False
        assert any(
            entry["sample_id"] == "T2" and entry["occupancy_fraction"] == 0.79
            for entry in payload["occupancy"]
        )


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
