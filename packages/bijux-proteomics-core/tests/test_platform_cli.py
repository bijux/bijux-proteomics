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


def test_spectrum_stats_command_reports_collection_summary_and_provenance() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = Path(__file__).parent / "fixtures" / "spectra" / "multi.mgf"
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
        assert provenance["document_schema"]["document_kind"] == "spectrum_provenance_manifest"


def test_spectrum_annotate_command_writes_annotation_and_plot_payload() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        source = Path(__file__).parent / "fixtures" / "spectra" / "simple.mgf"
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
        assert payload["annotation"]["document_schema"]["document_kind"] == "spectrum_annotation"
        assert payload["annotation"]["matches"]
        assert Path("annotation.tsv").exists()
        assert Path("plot.json").exists()


def test_validate_command_supports_fasta_psm_mgf_and_mod_registry(fasta_fixture_dir: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(Path(__file__).parent / "fixtures" / "psm" / "minimal_results.tsv", "results.tsv")
        shutil.copy(Path(__file__).parent / "fixtures" / "spectra" / "simple.mgf", "simple.mgf")
        shutil.copy(
            Path(__file__).parent / "fixtures" / "modifications" / "valid_registry.json",
            "registry.json",
        )

        fasta_result = runner.invoke(cli, ["validate", "valid.fasta", "--kind", "fasta"])
        psm_result = runner.invoke(cli, ["validate", "results.tsv", "--kind", "psm"])
        mgf_result = runner.invoke(cli, ["validate", "simple.mgf", "--kind", "mgf"])
        registry_result = runner.invoke(cli, ["validate", "registry.json", "--kind", "mod-registry"])

        assert fasta_result.exit_code == 0
        assert json.loads(fasta_result.output)["valid"] is True
        assert psm_result.exit_code == 0
        assert json.loads(psm_result.output)["valid"] is True
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["valid"] is True
        assert registry_result.exit_code == 0
        assert json.loads(registry_result.output)["summary"]["variable_modifications"] >= 1


def test_summarize_command_supports_fasta_psm_and_mgf(fasta_fixture_dir: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(fasta_fixture_dir / "valid_records.fasta", "valid.fasta")
        shutil.copy(Path(__file__).parent / "fixtures" / "psm" / "minimal_results.tsv", "results.tsv")
        shutil.copy(Path(__file__).parent / "fixtures" / "spectra" / "multi.mgf", "multi.mgf")

        fasta_result = runner.invoke(cli, ["summarize", "valid.fasta", "--kind", "fasta"])
        psm_result = runner.invoke(cli, ["summarize", "results.tsv", "--kind", "psm"])
        mgf_result = runner.invoke(cli, ["summarize", "multi.mgf", "--kind", "mgf"])

        assert fasta_result.exit_code == 0
        assert json.loads(fasta_result.output)["summary"]["total_records"] == 3
        assert psm_result.exit_code == 0
        assert json.loads(psm_result.output)["psm_summary"]["total_psms"] == 3
        assert mgf_result.exit_code == 0
        assert json.loads(mgf_result.output)["summary"]["spectrum_count"] == 2


def test_validate_and_summarize_commands_support_mzml_and_design_tables() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(Path(__file__).parent / "fixtures" / "formats" / "simple.mzml", "simple.mzml")
        shutil.copy(Path(__file__).parent / "fixtures" / "formats" / "valid.design.tsv", "design.tsv")

        validate_mzml = runner.invoke(cli, ["validate", "simple.mzml", "--kind", "mzml"])
        summarize_mzml = runner.invoke(cli, ["summarize", "simple.mzml", "--kind", "mzml"])
        validate_design = runner.invoke(cli, ["validate", "design.tsv", "--kind", "design-table"])
        summarize_design = runner.invoke(cli, ["summarize", "design.tsv", "--kind", "design-table"])

        assert validate_mzml.exit_code == 0
        assert json.loads(validate_mzml.output)["detected_format"] == "mzml"
        assert summarize_mzml.exit_code == 0
        assert json.loads(summarize_mzml.output)["metadata"]["run_id"] == "RUN_001"
        assert validate_design.exit_code == 0
        assert json.loads(validate_design.output)["detected_format"] == "design-table"
        assert summarize_design.exit_code == 0
        assert json.loads(summarize_design.output)["accepted_entries"] == 1


def test_format_convert_and_bundle_run_commands_materialize_normalized_outputs() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(Path(__file__).parent / "fixtures" / "formats" / "simple.mzml", "simple.mzml")
        shutil.copy(Path(__file__).parent / "fixtures" / "formats" / "valid.design.tsv", "design.tsv")
        shutil.copy(
            Path(__file__).parent / "fixtures" / "first_useful_run" / "results.tsv",
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
        fixture_dir = Path(__file__).parent / "fixtures" / "search_adapters"
        shutil.copy(fixture_dir / "sage_results.tsv", "sage_results.tsv")
        shutil.copy(fixture_dir / "sage_config.json", "sage_config.json")
        shutil.copy(fixture_dir / "generic_results.tsv", "generic_results.tsv")
        shutil.copy(fixture_dir / "generic_mapping.json", "generic_mapping.json")

        inspect_result = runner.invoke(cli, ["search-adapter", "inspect", "--adapter", "sage"])
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
        fixture_dir = Path(__file__).parent / "fixtures" / "search_adapters"
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
        assert any(issue["code"] == "missing_decoy_strategy" for issue in validate_payload["issues"])
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
        fixture_dir = Path(__file__).parent / "fixtures" / "psm"
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
