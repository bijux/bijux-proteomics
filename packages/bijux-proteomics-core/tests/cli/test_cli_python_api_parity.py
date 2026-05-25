# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import shutil

from click.testing import CliRunner

from bijux_proteomics.interfaces.cli.app import cli
from bijux_proteomics.interfaces.python_api import (
    run_compartment_biology_command,
    run_fasta_parse_command,
    run_program_template,
    run_psm_inspect_command,
    run_quantify_command,
)


FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures"
_VOLATILE_KEYS = {"artifact_id", "content_hash", "created_at", "updated_at"}


def _invoke_python_api(function, /, *args, **kwargs) -> dict[str, object]:
    stream = io.StringIO()
    with redirect_stdout(stream):
        function(*args, **kwargs)
    return json.loads(stream.getvalue())


def _normalize_payload(value):
    if isinstance(value, dict):
        return {
            key: _normalize_payload(item)
            for key, item in value.items()
            if key not in _VOLATILE_KEYS and key != "outputs"
        }
    if isinstance(value, list):
        return [_normalize_payload(item) for item in value]
    return value


def test_psm_inspect_cli_matches_python_api_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        shutil.copy(FIXTURE_ROOT / "psm" / "representative_results.tsv", "results.tsv")

        cli_result = runner.invoke(
            cli,
            [
                "psm-inspect",
                "results.tsv",
                "--tsv-out",
                "normalized.cli.tsv",
                "--summary-tsv-out",
                "inspection.cli.tsv",
                "--provenance-out",
                "provenance.cli.json",
            ],
        )

        assert cli_result.exit_code == 0

        api_payload = _invoke_python_api(
            run_psm_inspect_command,
            Path("results.tsv"),
            "spectrum_id",
            "peptide",
            None,
            None,
            "charge",
            "score",
            "q_value",
            None,
            "proteins",
            None,
            None,
            ";",
            "trypsin",
            "DECOY_",
            None,
            None,
            Path("normalized.api.tsv"),
            Path("provenance.api.json"),
            Path("inspection.api.tsv"),
            None,
            None,
            None,
            None,
            None,
            None,
        )

        assert _normalize_payload(json.loads(cli_result.output)) == _normalize_payload(
            api_payload
        )
        assert Path("normalized.cli.tsv").read_text(encoding="utf-8") == Path(
            "normalized.api.tsv"
        ).read_text(encoding="utf-8")
        assert Path("inspection.cli.tsv").read_text(encoding="utf-8") == Path(
            "inspection.api.tsv"
        ).read_text(encoding="utf-8")
        assert _normalize_payload(
            json.loads(Path("provenance.cli.json").read_text(encoding="utf-8"))
        ) == _normalize_payload(
            json.loads(Path("provenance.api.json").read_text(encoding="utf-8"))
        )


def test_program_template_cli_matches_python_api_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        cli_result = runner.invoke(
            cli,
            [
                "program-template",
                "--program-id",
                "prog-001",
                "--name",
                "Stress Response Program",
                "--objective",
                "Explain treatment stress response",
                "--target-id",
                "target-001",
                "--target-name",
                "P11111",
                "--sequence",
                "MPEPTIDERK",
                "--organism",
                "human",
                "--mechanism",
                "stress adaptation",
                "--out",
                "program.cli.json",
            ],
        )

        assert cli_result.exit_code == 0

        api_payload = _invoke_python_api(
            run_program_template,
            "prog-001",
            "Stress Response Program",
            "Explain treatment stress response",
            "target-001",
            "P11111",
            "MPEPTIDERK",
            "human",
            "stress adaptation",
            Path("program.api.json"),
        )

        assert _normalize_payload(json.loads(cli_result.output)) == _normalize_payload(
            api_payload
        )
        assert _normalize_payload(
            json.loads(Path("program.cli.json").read_text(encoding="utf-8"))
        ) == _normalize_payload(
            json.loads(Path("program.api.json").read_text(encoding="utf-8"))
        )


def test_fasta_parse_cli_matches_python_api_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fasta_path = Path("example.fasta")
        fasta_path.write_text(">sp|P11111|ONE_HUMAN\nMPEPTIDE\n", encoding="utf-8")

        cli_result = runner.invoke(
            cli,
            [
                "fasta-parse",
                "example.fasta",
                "--mode",
                "strict",
                "--duplicate-accession-policy",
                "reject",
            ],
        )

        assert cli_result.exit_code == 0

        api_payload = _invoke_python_api(
            run_fasta_parse_command,
            fasta_path,
            "strict",
            "reject",
            None,
        )

        assert _normalize_payload(json.loads(cli_result.output)) == _normalize_payload(
            api_payload
        )


def test_compartment_biology_cli_matches_python_api_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        workflow_fixture_dir = FIXTURE_ROOT / "workflow"
        for name in [
            "biological_report_features.tsv",
            "biological_report.design.tsv",
            "biological_report_compartments.tsv",
        ]:
            shutil.copy(workflow_fixture_dir / name, name)

        cli_result = runner.invoke(
            cli,
            [
                "interpretation",
                "compartment-biology",
                "biological_report_features.tsv",
                "biological_report_compartments.tsv",
                "--design-path",
                "biological_report.design.tsv",
                "--summary-tsv-out",
                "compartment.cli.summary.tsv",
                "--enrichment-tsv-out",
                "compartment.cli.enrichment.tsv",
            ],
        )

        assert cli_result.exit_code == 0

        api_payload = _invoke_python_api(
            run_compartment_biology_command,
            input_table=Path("biological_report_features.tsv"),
            context_annotation_tsv=Path("biological_report_compartments.tsv"),
            design_path=Path("biological_report.design.tsv"),
            condition_a=None,
            condition_b=None,
            sample_column="sample_id",
            feature_id_column="feature_id",
            peptide_column="peptide",
            intensity_column="intensity",
            protein_refs_column="proteins",
            charge_column="charge",
            mz_column="mz",
            retention_time_column="retention_time_seconds",
            missing_reason_column="missing_reason",
            protein_separator=";",
            aggregation="sum",
            top_n=3,
            normalization="median",
            protein_ref_column="protein_ref",
            context_id_column="context_id",
            context_kind_column="context_kind",
            context_name_column="context_name",
            source_name_column="source_name",
            source_accession_column="source_accession",
            evidence_column="evidence",
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
            min_enrichment_ratio=1.0,
            minimum_observed_member_count=2,
            summary_tsv_out=Path("compartment.api.summary.tsv"),
            enrichment_tsv_out=Path("compartment.api.enrichment.tsv"),
            matrix_tsv_out=None,
            sample_score_tsv_out=None,
            condition_score_tsv_out=None,
            condition_comparison_tsv_out=None,
            unresolved_member_tsv_out=None,
            unknown_localization_tsv_out=None,
            rejected_context_tsv_out=None,
            out_path=None,
        )

        assert _normalize_payload(json.loads(cli_result.output)) == _normalize_payload(
            api_payload
        )
        assert Path("compartment.cli.summary.tsv").read_text(encoding="utf-8") == Path(
            "compartment.api.summary.tsv"
        ).read_text(encoding="utf-8")
        assert Path("compartment.cli.enrichment.tsv").read_text(
            encoding="utf-8"
        ) == Path("compartment.api.enrichment.tsv").read_text(encoding="utf-8")


def test_quantify_cli_matches_python_api_output() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        fixture_dir = FIXTURE_ROOT / "quant"
        shutil.copy(fixture_dir / "ms1_features.tsv", "ms1_features.tsv")
        shutil.copy(fixture_dir / "quant.design.tsv", "quant.design.tsv")

        cli_result = runner.invoke(
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
                "--differential-tsv-out",
                "quant.cli.differential.tsv",
            ],
        )

        assert cli_result.exit_code == 0

        api_payload = _invoke_python_api(
            run_quantify_command,
            input_table=Path("ms1_features.tsv"),
            measure="intensity",
            entity_level="protein",
            aggregation="sum",
            top_n=3,
            normalization="log2_median_centering",
            imputation="none",
            sample_column="sample_id",
            feature_id_column="feature_id",
            peptide_column="peptide",
            intensity_column="intensity",
            protein_refs_column="proteins",
            charge_column="charge",
            mz_column="mz",
            retention_time_column="retention_time_seconds",
            missing_reason_column="missing_reason",
            protein_separator=";",
            design_path=Path("quant.design.tsv"),
            condition_a=None,
            condition_b=None,
            differential_tsv_out=Path("quant.api.differential.tsv"),
            broken_pairs_tsv_out=None,
            multi_contrast_consistency_tsv_out=None,
            batch_effect_summary_tsv_out=None,
            batch_effect_batches_tsv_out=None,
            batch_effect_components_tsv_out=None,
            time_course_tsv_out=None,
            design_covariates=(),
            design_batch_field="batch",
            design_pairing_field=None,
            design_timepoint_field=None,
            design_timepoint_order_file=None,
            design_matrix_tsv_out=None,
            design_coefficients_tsv_out=None,
            design_contrasts_tsv_out=None,
            limma_assay_tsv_out=None,
            limma_samples_tsv_out=None,
            limma_design_tsv_out=None,
            limma_contrasts_tsv_out=None,
            msstats_input_tsv_out=None,
            limma_results_path=None,
            msstats_results_path=None,
            report_out=None,
            out_path=None,
        )

        assert _normalize_payload(json.loads(cli_result.output)) == _normalize_payload(
            api_payload
        )
        assert Path("quant.cli.differential.tsv").read_text(encoding="utf-8") == Path(
            "quant.api.differential.tsv"
        ).read_text(encoding="utf-8")
