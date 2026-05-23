# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import study
from bijux_proteomics.chemistry import calculate_peptide_mz
from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def test_study_package_exports_lab_qc_status_surface() -> None:
    observed_mz = calculate_peptide_mz("ACDEFGK", charge=2)
    run_report = study.build_lcms_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="study-package:scan-001",
                precursor_mz=observed_mz,
                precursor_charge=2,
                retention_time_seconds=120.0,
                peaks=(
                    SpectrumPeak(mz=observed_mz - 10.0, intensity=800.0),
                    SpectrumPeak(mz=observed_mz, intensity=3200.0),
                ),
            ),
        ),
        (
            PsmRecord(
                spectrum_id="study-package:scan-001",
                peptide="ACDEFGK",
                canonical_peptide="ACDEFGK",
                charge=2,
                score=120.0,
                q_value=0.01,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        design_entry=ExperimentalDesignEntry(
            sample_id="STUDY1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="study-package.mgf",
            identifications_file="study-package.tsv",
            metadata={"enrichment_marker_refs": "P11111"},
        ),
        protein_sequences={"P11111": "KACDEFGKRAA"},
        run_id="study-package-run",
    )

    assessment = study.build_run_qc_assessment(
        run_report,
        policy=study.default_qc_threshold_policy().model_copy(update={"rules": ()}),
    )

    assert study.QcStatus.PASS.value == "pass"
    assert assessment.qc_status is study.QcStatus.PASS
    assert assessment.status_reasons == ()
    assert "qc_status" in study.render_qc_assessment_tsv(assessment).splitlines()[0]
