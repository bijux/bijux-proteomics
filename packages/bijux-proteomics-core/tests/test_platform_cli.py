# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
import shutil

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli import cli


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

        parse_result = runner.invoke(cli, ["fasta-parse", "valid.fasta", "--mode", "strict"])
        assert parse_result.exit_code == 0
        parse_payload = json.loads(parse_result.output)
        assert parse_payload["total_records"] == 3

        stats_result = runner.invoke(cli, ["fasta-stats", "dedup.fasta", "--mode", "permissive"])
        assert stats_result.exit_code == 0
        stats_payload = json.loads(stats_result.output)
        assert stats_payload["duplicate_sequence_count"] == 2

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
        assert provenance_payload["document_schema"]["document_kind"] == "fasta_provenance_manifest"

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
            ],
        )
        assert decoy_result.exit_code == 0
        decoy_payload = json.loads(decoy_result.output)
        assert decoy_payload["valid"] is True
        assert Path("target_decoy.fasta").read_text().count(">") == 6


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

        shutil.copy(fasta_fixture_dir / "target_decoy_valid.fasta", "target_decoy_valid.fasta")
        validation_result = runner.invoke(
            cli,
            ["target-decoy-validate", "target_decoy_valid.fasta"],
        )
        assert validation_result.exit_code == 0
        validation_payload = json.loads(validation_result.output)
        assert validation_payload["valid"] is True


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
        assert Path("peptides.jsonl").exists()
        manifest = json.loads(Path("digest.manifest.json").read_text())
        assert manifest["document_schema"]["document_kind"] == "peptide_digest_manifest"


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


def test_psm_inspect_command_reports_summaries_and_writes_exports() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = Path(__file__).parent / "fixtures" / "psm" / "minimal_results.tsv"
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
        assert manifest["document_schema"]["document_kind"] == "search_result_provenance_manifest"


def test_fdr_command_filters_by_threshold_and_writes_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = Path(__file__).parent / "fixtures" / "psm" / "fdr_results.tsv"
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
