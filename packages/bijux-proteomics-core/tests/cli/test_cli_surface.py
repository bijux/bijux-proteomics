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
        assert (
            Path("production.summary.tsv")
            .read_text()
            .splitlines()[0]
            .startswith("input_record_count\tprotein_count\trejected_record_count")
        )
        assert "1-99\t1\t99\t6\t116" in Path("production.length.tsv").read_text()
        assert "Homo sapiens\t4\t3\t1\t1" in Path("production.organism.tsv").read_text()

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
        assert by_query["MPEPTLDEKAK"]["missed_cleavage_counts"] == [1]
        assert by_query["SHADEQK"]["protein_groups"] == ["GROUP_SHARED"]
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
        assert picked_p22222["partner_ref"] == "DECOY_P22222"
        assert picked_p22222["protein_group_ids"]
        assert Path("picked.summary.tsv").exists()
        assert Path("picked.entries.tsv").exists()
        assert "0.1\t5\t4\t1\t0\t2\t4\t4\t0\t0\t2" in Path(
            "picked.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P22222\tDECOY_P22222\tpg-" in Path("picked.entries.tsv").read_text(
            encoding="utf-8"
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
        assert payload["scenario_count"] == 6
        assert payload["homolog_family_scenario_count"] == 1
        assert payload["contaminant_scenario_count"] == 1
        assert payload["decoy_scenario_count"] == 1
        assert payload["reports"][0]["method_assessments"]
        assert Path("protein_inference_benchmarks.summary.tsv").exists()
        assert Path("protein_inference_benchmarks.scenarios.tsv").exists()
        assert Path("protein_inference_benchmarks.assessments.tsv").exists()
        assert "homolog_family_scenario_count\t1" in Path(
            "protein_inference_benchmarks.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "homolog-family-pressure" in Path(
            "protein_inference_benchmarks.scenarios.tsv"
        ).read_text(encoding="utf-8")
        assert "false_positive_proteins" in Path(
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
        assert p11111["unique_peptides"] == ["PEPTIDEK"]
        assert p11111["shared_peptides"] == ["SHAREDK"]
        assert payload["regions"][0]["protein_ref"] == "P11111"
        assert Path("protein_coverage.summary.tsv").exists()
        assert Path("protein_coverage.tsv").exists()
        assert Path("protein_coverage.regions.tsv").exists()
        assert "proteins_with_shared_peptides\t3" in Path(
            "protein_coverage.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t21\t15\t0.7142857142857143\t2-9;13-19" in Path(
            "protein_coverage.tsv"
        ).read_text(encoding="utf-8")
        assert "P11111\t2\t13\t19\t7" in Path("protein_coverage.regions.tsv").read_text(
            encoding="utf-8"
        )


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
        assert payload["summary"]["total_peptides"] == 6
        assert payload["summary"]["strong_count"] == 2
        assert payload["summary"]["weak_count"] == 2
        assert payload["summary"]["modified_count"] == 1
        assert payload["summary"]["contaminant_count"] == 1
        assert payload["summary"]["decoy_count"] == 1
        by_peptide = {entry["canonical_peptide"]: entry for entry in payload["entries"]}
        assert by_peptide["STRONGK"]["primary_class"] == "strong"
        assert by_peptide["SHAREDK"]["primary_class"] == "weak"
        assert "shared" in by_peptide["SHAREDK"]["tags"]
        assert "modified" in by_peptide["ACDM[Oxidation]K"]["tags"]
        assert by_peptide["CONTAMK"]["primary_class"] == "contaminant"
        assert by_peptide["DECOYSEQ"]["primary_class"] == "decoy"
        assert Path("peptide_evidence.summary.tsv").exists()
        assert Path("peptide_evidence.entries.tsv").exists()
        assert "strong_count\t2" in Path("peptide_evidence.summary.tsv").read_text(
            encoding="utf-8"
        )
        assert "CONTAMK\tCONTAMK\tcontaminant\tunique;contaminant" in Path(
            "peptide_evidence.entries.tsv"
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
        assert Path("plot.json").exists()


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

        result = runner.invoke(
            cli,
            [
                "fragpipe-import",
                "psm.tsv",
                "--peptide-tsv",
                "combined_peptide.tsv",
                "--protein-tsv",
                "combined_protein.tsv",
                "--summary-tsv-out",
                "fragpipe.summary.tsv",
                "--psm-tsv-out",
                "fragpipe.psm.tsv",
                "--peptide-review-tsv-out",
                "fragpipe.peptide.tsv",
                "--protein-review-tsv-out",
                "fragpipe.protein.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["open_search_psm_count"] == 1
        assert payload["summary"]["peptide_row_count"] == 2
        assert payload["summary"]["protein_row_count"] == 3
        assert (
            payload["psm_normalization"]["adapter"]["display_name"]
            == "FragPipe psm export"
        )
        assert payload["psm_rows"][1]["open_search_candidate"] is True
        assert Path("fragpipe.summary.tsv").exists()
        assert Path("fragpipe.psm.tsv").exists()
        assert Path("fragpipe.peptide.tsv").exists()
        assert Path("fragpipe.protein.tsv").exists()


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
                "--psm-tsv-out",
                "sage.psm.tsv",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["dialect_id"] == "sage-psm"
        assert payload["summary"]["accepted_psm_count"] == 3
        assert payload["summary"]["modified_psm_count"] == 2
        assert payload["summary"]["hyperscore_psm_count"] == 3
        assert payload["summary"]["multi_protein_psm_count"] == 1
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert payload["psm_rows"][0]["hyperscore"] == 41.2
        assert Path("sage.summary.tsv").exists()
        assert Path("sage.psm.tsv").exists()


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
                "--psm-tsv-out",
                "comet.psm.tsv",
            ],
        )
        pepxml_result = runner.invoke(cli, ["comet-import", "comet_results.pepxml"])

        assert tabular_result.exit_code == 0
        tabular_payload = json.loads(tabular_result.output)
        assert tabular_payload["import_kind"] == "tabular"
        assert tabular_payload["summary"]["accepted_psm_count"] == 3
        assert tabular_payload["summary"]["modified_psm_count"] == 2
        assert tabular_payload["summary"]["xcorr_psm_count"] == 3
        assert tabular_payload["parameter_report"]["enzyme"] == "trypsin"
        assert Path("comet.summary.tsv").exists()
        assert Path("comet.psm.tsv").exists()

        assert pepxml_result.exit_code == 0
        pepxml_payload = json.loads(pepxml_result.output)
        assert pepxml_payload["import_kind"] == "pepxml"
        assert pepxml_payload["summary"]["accepted_psm_count"] == 3
        assert pepxml_payload["psm_rows"][0]["xcorr"] == 3.52


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
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"]["accepted_evidence_count"] == 4
        assert payload["summary"]["peptide_row_count"] == 4
        assert payload["summary"]["protein_group_row_count"] == 4
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
        assert Path("maxquant.summary.tsv").exists()
        assert Path("maxquant.evidence.tsv").exists()
        assert Path("maxquant.peptides.tsv").exists()
        assert Path("maxquant.proteins.tsv").exists()


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
        assert payload["dia_native_report"]["imported_count"] == 4
        assert Path("diann.summary.tsv").exists()
        assert Path("diann.precursors.tsv").exists()
        assert Path("diann.protein_groups.tsv").exists()


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
                "--protein-group-tsv-out",
                "spectronaut.protein_groups.tsv",
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
        assert payload["parameter_report"]["enzyme"] == "trypsin"
        assert (
            payload["normalization"]["adapter"]["display_name"]
            == "Spectronaut review report"
        )
        assert payload["precursor_rows"][0]["modified_peptide"] == "PES[Phospho]TIDE"
        assert Path("spectronaut.summary.tsv").exists()
        assert Path("spectronaut.precursors.tsv").exists()
        assert Path("spectronaut.protein_groups.tsv").exists()


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
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
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
        assert payload["mapped_rows"][1]["contaminant_flag"] is True
        assert Path("mapped.tsv").exists()


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
        assert Path("openms.summary.tsv").exists()
        assert Path("openms.psm.tsv").exists()
        assert Path("openms.protein.tsv").exists()
        assert Path("openms.feature.tsv").exists()


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
        assert payload["normalization_comparison"]["method"] == "median"
        assert payload["normalization_comparison"]["after"]
        assert payload["normalization_strategy"]["recommended_method"] is not None
        assert payload["batch_effect"]["disposition"] == "ADVISORY"
        assert payload["replicate_correlations"]["entries"]
        assert payload["differential_abundance"]["condition_a"] == "control"
        assert any(
            entry["entity_id"] == "P001" and entry["log2_fold_change"] > 0
            for entry in payload["differential_abundance"]["entries"]
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
        assert "feature\tmodified_peptide\tprotein\tfalse\ttop_n\ttrue" in Path(
            "protein_matrix.summary.tsv"
        ).read_text(encoding="utf-8")
        assert "P1\tprotein\tP1\t2\t2\t0\tPEPAAK;PEPMTK\t1600\t2100" in Path(
            "protein_matrix.matrix.tsv"
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
