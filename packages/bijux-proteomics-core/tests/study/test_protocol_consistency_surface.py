# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.study import (
    AcquisitionType,
    DigestionEnzyme,
    EnrichmentType,
    FractionationMode,
    LabelingMethod,
    LabProtocolContextEntry,
    ProtocolConsistencySeverity,
    ProtocolConsistencyStatus,
    build_lcms_run_qc_report,
    build_protocol_consistency_report,
    render_protocol_consistency_tsv,
    require_protocol_consistency_without_blockers,
)
from bijux_proteomics.study.lab_protocol_context import DepletionMode


def _protocol(
    *,
    protocol_id: str,
    digestion_enzyme: DigestionEnzyme = DigestionEnzyme.TRYPSIN,
    acquisition_type: AcquisitionType = AcquisitionType.DDA,
    labeling_method: LabelingMethod = LabelingMethod.LABEL_FREE,
    enrichment_type: EnrichmentType = EnrichmentType.NONE,
) -> LabProtocolContextEntry:
    return LabProtocolContextEntry(
        protocol_id=protocol_id,
        digestion_enzyme=digestion_enzyme,
        acquisition_type=acquisition_type,
        labeling_method=labeling_method,
        enrichment_type=enrichment_type,
        fractionation_mode=FractionationMode.NONE,
        depletion_mode=DepletionMode.NONE,
        instrument_platform="Orbitrap Eclipse",
        metadata={},
    )


def test_protocol_consistency_report_blocks_non_tryptic_digestion_drift() -> None:
    run_report = build_lcms_run_qc_report(
        spectra=(
            SpectrumModel(
                spectrum_id="scan-001",
                precursor_mz=500.2,
                precursor_charge=2,
                peaks=(SpectrumPeak(mz=500.2, intensity=1200.0),),
            ),
            SpectrumModel(
                spectrum_id="scan-002",
                precursor_mz=600.2,
                precursor_charge=2,
                peaks=(SpectrumPeak(mz=600.2, intensity=1400.0),),
            ),
        ),
        psm_records=(
            PsmRecord(
                spectrum_id="scan-001",
                peptide="ACDEFGK",
                canonical_peptide="ACDEFGK",
                charge=2,
                score=120.0,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
            PsmRecord(
                spectrum_id="scan-002",
                peptide="CDEFG",
                canonical_peptide="CDEFG",
                charge=2,
                score=95.0,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        protein_sequences={"P11111": "KACDEFGKRAA"},
        run_id="run-001",
    )

    report = build_protocol_consistency_report(
        _protocol(protocol_id="trypsin-protocol"),
        run_qc_report=run_report,
    )

    assert report.summary.status is ProtocolConsistencyStatus.BLOCKING
    assert report.summary.blocking_diagnostic_count == 1
    assert report.diagnostics[0].code == "digestion_specificity_mismatch"
    assert report.diagnostics[0].severity is ProtocolConsistencySeverity.BLOCKING


def test_protocol_consistency_report_blocks_tmt_protocol_without_reporter_signal(
    tmp_path: Path,
) -> None:
    reporter_path = tmp_path / "reporters.tsv"
    reporter_path.write_text(
        "\n".join(
            (
                "source_row_id\tpeptide\tmultiplex_group\t126\t127N",
                "row-1\tPEPTIDE\tplex-a\t0\t0",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    reporter_report = SimpleNamespace(
        accepted_rows=(
            SimpleNamespace(
                channel_intensities=(
                    SimpleNamespace(multiplex_channel="126", intensity=0.0),
                    SimpleNamespace(multiplex_channel="127N", intensity=0.0),
                )
            ),
        ),
    )

    report = build_protocol_consistency_report(
        _protocol(
            protocol_id="tmt-protocol",
            digestion_enzyme=DigestionEnzyme.OTHER,
            labeling_method=LabelingMethod.TMT,
        ),
        reporter_import_report=reporter_report,
    )

    assert report.summary.status is ProtocolConsistencyStatus.BLOCKING
    assert report.diagnostics[0].code == "missing_reporter_channel_signal"
    assert report.diagnostics[0].observed == "0_positive_reporter_signals"


def test_protocol_consistency_report_blocks_phospho_protocol_without_phosphosites(
    tmp_path: Path,
) -> None:
    ptm_path = tmp_path / "ptm.tsv"
    ptm_path.write_text(
        "\n".join(
            (
                "spectrum_id\tpeptide\tcharge\tscore\tproteins\tlocalization_score\tlocalization_probability\tq_value\tsample_id\tcandidate_sites\tdecoy_label",
                "scan=1\tPEK[Acetyl]TIDE\t2\t100\tP11111\t15\t0.98\t0.01\tS1\t3\ttarget",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    ptm_report = SimpleNamespace(
        accepted_records=(SimpleNamespace(modification_names=("Acetyl",)),),
    )

    report = build_protocol_consistency_report(
        _protocol(
            protocol_id="phospho-protocol",
            digestion_enzyme=DigestionEnzyme.OTHER,
            enrichment_type=EnrichmentType.PHOSPHO,
        ),
        ptm_evidence_report=ptm_report,
    )

    assert report.summary.status is ProtocolConsistencyStatus.BLOCKING
    assert report.diagnostics[0].code == "missing_expected_enrichment_sites"
    assert "matching_ptm_rows=0" in report.diagnostics[0].observed


def test_protocol_consistency_report_renders_and_requires_non_blocking_consistency(
    tmp_path: Path,
) -> None:
    reporter_path = tmp_path / "reporters.tsv"
    reporter_path.write_text(
        "\n".join(
            (
                "source_row_id\tpeptide\tmultiplex_group\t126\t127N",
                "row-1\tPEPTIDE\tplex-a\t1000\t900",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    report = build_protocol_consistency_report(
        _protocol(
            protocol_id="tmt-ok",
            digestion_enzyme=DigestionEnzyme.OTHER,
            labeling_method=LabelingMethod.TMT,
        ),
        reporter_import_report=SimpleNamespace(
            accepted_rows=(
                SimpleNamespace(
                    channel_intensities=(
                        SimpleNamespace(multiplex_channel="126", intensity=1000.0),
                        SimpleNamespace(multiplex_channel="127N", intensity=900.0),
                    )
                ),
            ),
        ),
    )

    assert report.summary.status is ProtocolConsistencyStatus.PASSED
    assert require_protocol_consistency_without_blockers(report) is report
    assert (
        render_protocol_consistency_tsv(report)
        .splitlines()[0]
        .startswith("protocol_id\taxis\tcode\tseverity")
    )
