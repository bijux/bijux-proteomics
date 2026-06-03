# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
from typing import Literal

from bijux_proteomics.study import (
    AcquisitionType,
    DepletionMode,
    DigestionEnzyme,
    EnrichmentType,
    FractionationMode,
    LabelingMethod,
    LabProtocolContextEntry,
    build_lab_protocol_interpretation_profile,
    build_protocol_aware_qc_threshold_policy,
    default_qc_threshold_policy,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.lab.qc import QcThresholdPolicy


def _write_protocol_table(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "protocol.tsv"
    path.write_text(body, encoding="utf-8")
    return path


def _protocol_entry(
    *,
    protocol_id: str,
    acquisition_type: AcquisitionType = AcquisitionType.DDA,
    labeling_method: LabelingMethod = LabelingMethod.LABEL_FREE,
    enrichment_type: EnrichmentType = EnrichmentType.NONE,
    fractionation_mode: FractionationMode = FractionationMode.NONE,
    depletion_mode: DepletionMode = DepletionMode.NONE,
) -> LabProtocolContextEntry:
    return LabProtocolContextEntry(
        protocol_id=protocol_id,
        digestion_enzyme=DigestionEnzyme.TRYPSIN,
        acquisition_type=acquisition_type,
        labeling_method=labeling_method,
        enrichment_type=enrichment_type,
        fractionation_mode=fractionation_mode,
        depletion_mode=depletion_mode,
        instrument_platform="Orbitrap Eclipse",
        metadata={},
    )


def _threshold(
    policy: QcThresholdPolicy,
    metric_key: str,
    field_name: Literal["lower_warn", "lower_fail", "upper_warn", "upper_fail"],
) -> float | None:
    for rule in policy.rules:
        if rule.metric_key == metric_key:
            if field_name == "lower_warn":
                return rule.lower_warn
            if field_name == "lower_fail":
                return rule.lower_fail
            if field_name == "upper_warn":
                return rule.upper_warn
            return rule.upper_fail
    raise AssertionError(f"missing QC rule for {metric_key}")


def test_parse_lab_protocol_context_table_preserves_context_and_metadata(
    tmp_path: Path,
) -> None:
    report = parse_lab_protocol_context_table(
        _write_protocol_table(
            tmp_path,
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform\tnote",
                    "prot-001\ttrypsin_lysc\tdia\tlabel_free\tnone\toffline_high_ph\tnone\tOrbitrap Astral\tdeep fractionated cohort",
                )
            )
            + "\n",
        )
    )

    entry = require_single_lab_protocol_context(report)
    assert report.summary.accepted_entry_count == 1
    assert report.summary.rejected_row_count == 0
    assert entry.digestion_enzyme is DigestionEnzyme.TRYPSIN_LYSC
    assert entry.acquisition_type is AcquisitionType.DIA
    assert entry.fractionation_mode is FractionationMode.OFFLINE_HIGH_PH
    assert entry.metadata == {"note": "deep fractionated cohort"}


def test_parse_lab_protocol_context_table_rejects_invalid_controlled_values(
    tmp_path: Path,
) -> None:
    report = parse_lab_protocol_context_table(
        _write_protocol_table(
            tmp_path,
            "\n".join(
                (
                    "protocol_id\tdigestion_enzyme\tacquisition_type\tlabeling_method\tenrichment_type\tfractionation_mode\tdepletion_mode\tinstrument_platform",
                    "prot-001\ttrypsin\tunknown\tlabel_free\tnone\tnone\tnone\tOrbitrap",
                )
            )
            + "\n",
        )
    )

    assert report.summary.accepted_entry_count == 0
    assert report.summary.rejected_row_count == 1
    assert report.rejected_rows[0].issues[0].code == "invalid_lab_protocol_value"


def test_lab_protocol_profiles_distinguish_targeted_tmt_enriched_and_dia_modes() -> (
    None
):
    targeted = build_lab_protocol_interpretation_profile(
        _protocol_entry(
            protocol_id="targeted-protocol",
            acquisition_type=AcquisitionType.TARGETED,
        )
    )
    tmt = build_lab_protocol_interpretation_profile(
        _protocol_entry(
            protocol_id="tmt-protocol",
            labeling_method=LabelingMethod.TMT,
        )
    )
    phospho = build_lab_protocol_interpretation_profile(
        _protocol_entry(
            protocol_id="phospho-protocol",
            enrichment_type=EnrichmentType.PHOSPHO,
        )
    )
    dia = build_lab_protocol_interpretation_profile(
        _protocol_entry(
            protocol_id="dia-protocol",
            acquisition_type=AcquisitionType.DIA,
        )
    )

    assert targeted.interpretation_focus == "targeted_validation"
    assert targeted.min_absolute_log2_fold_change == 0.25
    assert tmt.interpretation_focus == "multiplex_discovery"
    assert tmt.min_absolute_log2_fold_change == 0.58
    assert phospho.interpretation_focus == "enriched_subproteome"
    assert phospho.heatmap_max_entity_count == 40
    assert dia.interpretation_focus == "dia_discovery"
    assert dia.heatmap_max_entity_count == 75


def test_protocol_aware_qc_policy_distinguishes_targeted_dia_tmt_and_enriched_modes() -> (
    None
):
    base_policy = default_qc_threshold_policy()
    targeted_policy = build_protocol_aware_qc_threshold_policy(
        _protocol_entry(
            protocol_id="targeted-protocol",
            acquisition_type=AcquisitionType.TARGETED,
        ),
        base_policy=base_policy,
    )
    dia_policy = build_protocol_aware_qc_threshold_policy(
        _protocol_entry(
            protocol_id="dia-protocol",
            acquisition_type=AcquisitionType.DIA,
            fractionation_mode=FractionationMode.OFFLINE_HIGH_PH,
        ),
        base_policy=base_policy,
    )
    tmt_policy = build_protocol_aware_qc_threshold_policy(
        _protocol_entry(
            protocol_id="tmt-protocol",
            labeling_method=LabelingMethod.TMT,
        ),
        base_policy=base_policy,
    )
    phospho_policy = build_protocol_aware_qc_threshold_policy(
        _protocol_entry(
            protocol_id="phospho-protocol",
            enrichment_type=EnrichmentType.PHOSPHO,
            depletion_mode=DepletionMode.PLASMA_HIGH_ABUNDANCE,
        ),
        base_policy=base_policy,
    )

    assert targeted_policy.policy_name.endswith(":targeted-protocol")
    assert _threshold(targeted_policy, "spectrum_count", "lower_warn") == 200.0
    assert _threshold(targeted_policy, "identification_rate", "lower_fail") == 0.02
    assert _threshold(dia_policy, "spectrum_count", "lower_warn") == 500.0
    assert _threshold(dia_policy, "identification_rate", "lower_warn") == 0.12
    assert _threshold(tmt_policy, "missed_cleavage_rate", "upper_warn") == 0.25
    assert _threshold(tmt_policy, "non_specific_fraction", "upper_fail") == 0.35
    assert _threshold(phospho_policy, "identification_rate", "lower_warn") == 0.1
    assert _threshold(phospho_policy, "contaminant_psm_fraction", "upper_warn") == 0.12
