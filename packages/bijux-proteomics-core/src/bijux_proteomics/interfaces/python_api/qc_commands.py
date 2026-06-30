# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""QC reporting Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    ProteomicsOperatorError,
    ProteomicsOperatorErrorCode,
    click,
    time,
)
from bijux_proteomics.interfaces.support.identification import (
    SearchResultColumnMapping,
    parse_psm_tsv,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_mgf
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    QcEvidenceInputFile,
    build_batch_qc_assessment,
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
    build_performance_snapshot,
    build_protocol_aware_qc_threshold_policy,
    build_qc_evidence_manifest,
    build_run_qc_assessment,
    default_qc_threshold_policy,
    load_qc_threshold_policy,
    parse_fasta_document,
    render_qc_assessment_html,
    render_qc_assessment_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.output_protocol.protocol_policy import (
    _build_protocol_consistency_report_from_inputs,
    _load_protocol_context,
)
from bijux_proteomics.interfaces.support.sequence_support import (
    _file_sha256,
    _select_design_entry,
)


def run_qc_report_command(
    spectra_path: Path,
    psm_path: Path,
    proteins_fasta: Path,
    design_path: Path | None,
    sample_id: str | None,
    run_id: str | None,
    policy_path: Path | None,
    protocol_context_tsv: Path | None,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    out_path: Path | None,
    tsv_out: Path | None,
    html_out: Path | None,
    manifest_out: Path | None,
    benchmark_out: Path | None,
) -> None:
    timings: dict[str, tuple[float, int | None]] = {}
    try:
        policy = default_qc_threshold_policy()
        if policy_path is not None:
            try:
                policy = load_qc_threshold_policy(policy_path)
            except Exception as exc:  # noqa: BLE001
                raise ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_POLICY_INVALID,
                    str(exc),
                ) from exc
        elif protocol_context_tsv is not None:
            try:
                protocol_context = _load_protocol_context(protocol_context_tsv)
                if protocol_context is None:
                    raise ProteomicsOperatorError(
                        ProteomicsOperatorErrorCode.QC_POLICY_INVALID,
                        "protocol context could not be resolved",
                    )
                policy = build_protocol_aware_qc_threshold_policy(protocol_context)
            except Exception as exc:  # noqa: BLE001
                raise ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_POLICY_INVALID,
                    str(exc),
                ) from exc

        started = time.perf_counter()
        design_entry = _select_design_entry(
            design_path, sample_id=sample_id, spectra_path=spectra_path
        )
        timings["parse_design"] = (
            time.perf_counter() - started,
            0 if design_entry is None else 1,
        )

        started = time.perf_counter()
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise ProteomicsOperatorError(
                ProteomicsOperatorErrorCode.INPUT_FASTA_REJECTED,
                f"FASTA input contains rejected records under strict mode: {rejected}",
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        timings["parse_fasta"] = (
            time.perf_counter() - started,
            len(fasta_report.accepted_records),
        )

        started = time.perf_counter()
        spectrum_report = parse_mgf(spectra_path)
        timings["parse_spectra"] = (
            time.perf_counter() - started,
            len(spectrum_report.accepted_spectra),
        )

        started = time.perf_counter()
        psm_report = parse_psm_tsv(
            psm_path,
            mapping=SearchResultColumnMapping(
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
            ),
        )
        timings["parse_psms"] = (
            time.perf_counter() - started,
            len(psm_report.accepted_records),
        )

        started = time.perf_counter()
        run_report = build_lcms_run_qc_report(
            spectrum_report.accepted_spectra,
            psm_report.accepted_records,
            design_entry=design_entry,
            protein_sequences=protein_sequences,
            run_id=run_id,
        )
        run_assessment = build_run_qc_assessment(run_report, policy=policy)
        protocol_consistency_report = (
            None
            if protocol_context_tsv is None
            else _build_protocol_consistency_report_from_inputs(
                protocol_context_tsv_path=protocol_context_tsv,
                run_qc_report=run_report,
            )
        )
        timings["build_run_qc"] = (
            time.perf_counter() - started,
            len(run_assessment.metric_assessments),
        )

        started = time.perf_counter()
        batch_report = None
        batch_assessment = None
        if design_entry and design_entry.batch:
            batch_report = build_instrument_batch_qc_report((run_report,))
            batch_assessment = build_batch_qc_assessment(batch_report, policy=policy)
        timings["build_batch_qc"] = (
            time.perf_counter() - started,
            0 if batch_assessment is None else len(batch_assessment.metric_assessments),
        )

        benchmark = build_performance_snapshot(run_report.run_id, operations=timings)
        input_files = [
            QcEvidenceInputFile(
                path=str(spectra_path),
                sha256=_file_sha256(spectra_path),
                role="spectra",
            ),
            QcEvidenceInputFile(
                path=str(psm_path),
                sha256=_file_sha256(psm_path),
                role="identifications",
            ),
            QcEvidenceInputFile(
                path=str(proteins_fasta),
                sha256=_file_sha256(proteins_fasta),
                role="proteins",
            ),
        ]
        if design_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(design_path),
                    sha256=_file_sha256(design_path),
                    role="design",
                )
            )
        if policy_path is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(policy_path),
                    sha256=_file_sha256(policy_path),
                    role="qc_policy",
                )
            )
        if protocol_context_tsv is not None:
            input_files.append(
                QcEvidenceInputFile(
                    path=str(protocol_context_tsv),
                    sha256=_file_sha256(protocol_context_tsv),
                    role="lab_protocol_context",
                )
            )
        manifest = build_qc_evidence_manifest(
            run_report=run_report,
            run_assessment=run_assessment,
            policy=policy,
            input_files=tuple(input_files),
            batch_report=batch_report,
            batch_assessment=batch_assessment,
            benchmark=benchmark,
        )
    except ProteomicsOperatorError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_BUILD_FAILED, str(exc)
                )
            )
        ) from exc

    try:
        if tsv_out is not None:
            _write_text_output(
                tsv_out,
                render_qc_assessment_tsv(
                    run_assessment, batch_assessment=batch_assessment
                ),
            )
        if html_out is not None:
            _write_text_output(
                html_out,
                render_qc_assessment_html(
                    run_report,
                    run_assessment,
                    batch_report=batch_report,
                    batch_assessment=batch_assessment,
                ),
            )
        if manifest_out is not None:
            manifest_out.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
        if benchmark_out is not None:
            benchmark_out.write_text(
                benchmark.to_stable_json() + "\n", encoding="utf-8"
            )
    except OSError as exc:
        raise click.ClickException(
            str(
                ProteomicsOperatorError(
                    ProteomicsOperatorErrorCode.QC_OUTPUT_WRITE_FAILED, str(exc)
                )
            )
        ) from exc

    payload = {
        "run_report": run_report.to_dict(),
        "run_assessment": run_assessment.to_dict(),
        "protocol_consistency_report": None
        if protocol_consistency_report is None
        else protocol_consistency_report.to_dict(),
        "batch_report": None if batch_report is None else batch_report.to_dict(),
        "batch_assessment": None
        if batch_assessment is None
        else batch_assessment.to_dict(),
        "evidence_manifest": manifest.to_dict(),
        "performance_snapshot": benchmark.to_dict(),
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_qc_report_command"]
