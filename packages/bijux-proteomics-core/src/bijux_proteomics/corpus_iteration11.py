# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Realistic mini-study and corpus surfaces for iteration 11."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class CorpusLicenseStatus(StrEnum):
    """License/caveat states for corpus assets."""

    BUNDLED = "bundled"
    REFERENCED = "referenced"
    USER_SUPPLIED = "user_supplied"


class CorpusAssetEntry(JsonModel):
    """One curated corpus asset with provenance and licensing state."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=8)
    license_status: CorpusLicenseStatus
    caveat: str = Field(..., min_length=1)


class DdaMiniStudyBundle(JsonModel):
    """Complete DDA mini-study fixture package with expected outputs."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    asset_entries: tuple[CorpusAssetEntry, ...] = Field(default_factory=tuple)
    expected_outputs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


def build_complete_dda_mini_study_bundle(
    *,
    study_id: str,
    asset_entries: tuple[CorpusAssetEntry, ...],
    expected_outputs: tuple[str, ...],
    evidence_pointers: tuple[str, ...],
) -> DdaMiniStudyBundle:
    """Curate DDA mini-study inputs, expected outputs, and evidence pointers."""

    required_roles = {
        "spectra",
        "engine_output",
        "fasta",
        "design_metadata",
        "identification",
        "protein_inference",
        "qc",
        "evidence",
    }
    roles = {entry.role for entry in asset_entries}
    missing = sorted(required_roles - roles)
    if missing:
        raise ValueError(f"DDA mini-study is missing required asset roles: {', '.join(missing)}")
    return DdaMiniStudyBundle(
        study_id=study_id,
        asset_entries=tuple(sorted(asset_entries, key=lambda entry: (entry.role, entry.path))),
        expected_outputs=tuple(sorted(expected_outputs)),
        evidence_pointers=tuple(sorted(evidence_pointers)),
    )


class DiaMiniStudyBundle(JsonModel):
    """Complete DIA mini-study fixture package with quant/evidence outputs."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    asset_entries: tuple[CorpusAssetEntry, ...] = Field(default_factory=tuple)
    precursor_quantity_rows: int = Field(..., ge=0)
    protein_quantity_rows: int = Field(..., ge=0)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)


def build_complete_dia_mini_study_bundle(
    *,
    study_id: str,
    asset_entries: tuple[CorpusAssetEntry, ...],
    precursor_quantity_rows: int,
    protein_quantity_rows: int,
    evidence_pointers: tuple[str, ...],
) -> DiaMiniStudyBundle:
    """Curate DIA mini-study inputs, quant outputs, and evidence pointers."""

    required_roles = {
        "library",
        "result_matrix",
        "design_metadata",
        "qc",
        "evidence",
    }
    roles = {entry.role for entry in asset_entries}
    missing = sorted(required_roles - roles)
    if missing:
        raise ValueError(f"DIA mini-study is missing required asset roles: {', '.join(missing)}")
    return DiaMiniStudyBundle(
        study_id=study_id,
        asset_entries=tuple(sorted(asset_entries, key=lambda entry: (entry.role, entry.path))),
        precursor_quantity_rows=precursor_quantity_rows,
        protein_quantity_rows=protein_quantity_rows,
        evidence_pointers=tuple(sorted(evidence_pointers)),
    )


class LfqMiniStudyBundle(JsonModel):
    """Complete LFQ mini-study package with normalization and DA context."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    feature_matrix_path: str = Field(..., min_length=1)
    peptide_matrix_path: str = Field(..., min_length=1)
    protein_matrix_path: str = Field(..., min_length=1)
    normalization_method: str = Field(..., min_length=1)
    missingness_summary_path: str = Field(..., min_length=1)
    differential_abundance_report_path: str = Field(..., min_length=1)
    review_packet_path: str = Field(..., min_length=1)


def build_complete_lfq_mini_study_bundle(
    *,
    study_id: str,
    feature_matrix_path: str,
    peptide_matrix_path: str,
    protein_matrix_path: str,
    normalization_method: str,
    missingness_summary_path: str,
    differential_abundance_report_path: str,
    review_packet_path: str,
) -> LfqMiniStudyBundle:
    """Curate LFQ matrices and downstream review outputs for a complete mini-study."""

    if normalization_method.lower() not in {"median", "vsn", "quantile", "none"}:
        raise ValueError("LFQ mini-study normalization method is not recognized")
    return LfqMiniStudyBundle(
        study_id=study_id,
        feature_matrix_path=feature_matrix_path,
        peptide_matrix_path=peptide_matrix_path,
        protein_matrix_path=protein_matrix_path,
        normalization_method=normalization_method,
        missingness_summary_path=missingness_summary_path,
        differential_abundance_report_path=differential_abundance_report_path,
        review_packet_path=review_packet_path,
    )


class TmtMiniStudyBundle(JsonModel):
    """Complete TMT mini-study bundle with channel and normalization diagnostics."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    channel_ids: tuple[str, ...] = Field(default_factory=tuple)
    carrier_channel_id: str | None = None
    reference_channel_id: str | None = None
    balance_diagnostics_path: str = Field(..., min_length=1)
    normalization_report_path: str = Field(..., min_length=1)
    differential_abundance_report_path: str = Field(..., min_length=1)


def build_complete_tmt_mini_study_bundle(
    *,
    study_id: str,
    channel_ids: tuple[str, ...],
    carrier_channel_id: str | None,
    reference_channel_id: str | None,
    balance_diagnostics_path: str,
    normalization_report_path: str,
    differential_abundance_report_path: str,
) -> TmtMiniStudyBundle:
    """Curate TMT channel/normalization outputs for complete mini-study fixtures."""

    if len(set(channel_ids)) != len(channel_ids):
        raise ValueError("TMT mini-study channel ids must be unique")
    if carrier_channel_id and carrier_channel_id not in channel_ids:
        raise ValueError("carrier channel id must be part of channel ids")
    if reference_channel_id and reference_channel_id not in channel_ids:
        raise ValueError("reference channel id must be part of channel ids")
    return TmtMiniStudyBundle(
        study_id=study_id,
        channel_ids=channel_ids,
        carrier_channel_id=carrier_channel_id,
        reference_channel_id=reference_channel_id,
        balance_diagnostics_path=balance_diagnostics_path,
        normalization_report_path=normalization_report_path,
        differential_abundance_report_path=differential_abundance_report_path,
    )


class PtmMiniStudyBundle(JsonModel):
    """Complete PTM mini-study fixture package with downstream lab suggestions."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    localization_report_path: str = Field(..., min_length=1)
    motif_report_path: str = Field(..., min_length=1)
    occupancy_report_path: str = Field(..., min_length=1)
    quant_report_path: str = Field(..., min_length=1)
    caveats: tuple[str, ...] = Field(default_factory=tuple)
    lab_target_suggestions: tuple[str, ...] = Field(default_factory=tuple)


def build_complete_ptm_mini_study_bundle(
    *,
    study_id: str,
    localization_report_path: str,
    motif_report_path: str,
    occupancy_report_path: str,
    quant_report_path: str,
    caveats: tuple[str, ...],
    lab_target_suggestions: tuple[str, ...],
) -> PtmMiniStudyBundle:
    """Curate PTM localization/motif/occupancy/quant outputs and lab suggestions."""

    if not lab_target_suggestions:
        raise ValueError("PTM mini-study should include at least one lab target suggestion")
    return PtmMiniStudyBundle(
        study_id=study_id,
        localization_report_path=localization_report_path,
        motif_report_path=motif_report_path,
        occupancy_report_path=occupancy_report_path,
        quant_report_path=quant_report_path,
        caveats=tuple(sorted(caveats)),
        lab_target_suggestions=tuple(sorted(lab_target_suggestions)),
    )


class KnownMixtureTruthBoundary(JsonModel):
    """Bounded truth-like reference statement for known-mixture studies."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(..., min_length=1)
    supported: bool
    caveat: str = Field(..., min_length=1)


class KnownMixtureMiniStudyBundle(JsonModel):
    """Known-mixture mini-study with bounded truth-like claims."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    mixture_asset_path: str = Field(..., min_length=1)
    truth_reference_path: str = Field(..., min_length=1)
    boundaries: tuple[KnownMixtureTruthBoundary, ...] = Field(default_factory=tuple)


def build_known_mixture_mini_study_bundle(
    *,
    study_id: str,
    mixture_asset_path: str,
    truth_reference_path: str,
    boundaries: tuple[KnownMixtureTruthBoundary, ...],
) -> KnownMixtureMiniStudyBundle:
    """Build known-mixture bundle with explicit accuracy-claim boundaries."""

    if not boundaries:
        raise ValueError("known-mixture mini-study must include at least one truth boundary")
    return KnownMixtureMiniStudyBundle(
        study_id=study_id,
        mixture_asset_path=mixture_asset_path,
        truth_reference_path=truth_reference_path,
        boundaries=tuple(boundaries),
    )


class ContradictionMiniStudyEntry(JsonModel):
    """One preserved contradiction across workflow surfaces."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    engine_disagreement: str = Field(..., min_length=1)
    quant_disagreement: str = Field(..., min_length=1)
    ptm_disagreement: str = Field(..., min_length=1)
    qc_disagreement: str = Field(..., min_length=1)
    lab_disagreement: str = Field(..., min_length=1)


class ContradictionMiniStudyBundle(JsonModel):
    """Mini-study bundle preserving contradictory proteomics evidence."""

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1)
    entries: tuple[ContradictionMiniStudyEntry, ...] = Field(default_factory=tuple)


def build_contradiction_mini_study_bundle(
    *,
    study_id: str,
    entries: tuple[ContradictionMiniStudyEntry, ...],
) -> ContradictionMiniStudyBundle:
    """Build contradiction mini-study fixture without flattening disagreements."""

    if not entries:
        raise ValueError("contradiction mini-study must include at least one contradiction entry")
    return ContradictionMiniStudyBundle(study_id=study_id, entries=entries)


class NegativeScienceCaseOutcome(StrEnum):
    """Outcome classes for scientifically incoherent corpus inputs."""

    REFUSED = "refused"
    CAVEATED = "caveated"


class NegativeScienceCase(JsonModel):
    """One incoherent scientific input with expected refusal/caveat behavior."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    incoherence_reason: str = Field(..., min_length=1)
    expected_outcome: NegativeScienceCaseOutcome
    evidence_pointer: str = Field(..., min_length=1)


class NegativeScienceCorpusReport(JsonModel):
    """Negative corpus report with refusal/caveat expectations."""

    model_config = ConfigDict(extra="forbid")

    cases: tuple[NegativeScienceCase, ...] = Field(default_factory=tuple)
    refusal_case_count: int = Field(..., ge=0)
    caveated_case_count: int = Field(..., ge=0)


def build_negative_science_corpus_report(
    cases: tuple[NegativeScienceCase, ...],
) -> NegativeScienceCorpusReport:
    """Build negative-science corpus expectations for refusal/caveated outputs."""

    return NegativeScienceCorpusReport(
        cases=cases,
        refusal_case_count=sum(
            1 for case in cases if case.expected_outcome is NegativeScienceCaseOutcome.REFUSED
        ),
        caveated_case_count=sum(
            1 for case in cases if case.expected_outcome is NegativeScienceCaseOutcome.CAVEATED
        ),
    )


class ExternalEngineCorpusPolicy(StrEnum):
    """Allowed distribution mode for external-engine corpus artifacts."""

    BUNDLE = "bundle"
    GENERATE = "generate"
    REFERENCE = "reference"
    USER_SUPPLIED = "user_supplied"


class ExternalEngineCorpusLicensingEntry(JsonModel):
    """One licensing-plan decision for an external-engine artifact class."""

    model_config = ConfigDict(extra="forbid")

    artifact_class: str = Field(..., min_length=1)
    policy: ExternalEngineCorpusPolicy
    rationale: str = Field(..., min_length=1)
    follow_up_action: str = Field(..., min_length=1)


class ExternalEngineCorpusLicensingPlan(JsonModel):
    """Licensing and distribution plan for external-engine corpus assets."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ExternalEngineCorpusLicensingEntry, ...] = Field(default_factory=tuple)


def build_external_engine_corpus_licensing_plan(
    entries: tuple[ExternalEngineCorpusLicensingEntry, ...],
) -> ExternalEngineCorpusLicensingPlan:
    """Build licensing plan for real-engine outputs and corpus distribution strategy."""

    classes = [entry.artifact_class for entry in entries]
    if len(classes) != len(set(classes)):
        raise ValueError("external-engine corpus licensing plan requires unique artifact classes")
    return ExternalEngineCorpusLicensingPlan(
        entries=tuple(sorted(entries, key=lambda entry: entry.artifact_class))
    )


class ScientificQuestionExampleIndexEntry(JsonModel):
    """Index entry mapping one scientific question to example corpus artifacts."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1)
    input_type: str = Field(..., min_length=1)
    workflow: str = Field(..., min_length=1)
    output_artifact: str = Field(..., min_length=1)
    evidence_grade: str = Field(..., min_length=1)
    caveats: tuple[str, ...] = Field(default_factory=tuple)


class ScientificQuestionExampleIndex(JsonModel):
    """Example index grouped by scientific question and output behavior."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ScientificQuestionExampleIndexEntry, ...] = Field(default_factory=tuple)


def build_example_index_by_scientific_question(
    entries: tuple[ScientificQuestionExampleIndexEntry, ...],
) -> ScientificQuestionExampleIndex:
    """Index examples by input type, workflow, output, evidence grade, and caveats."""

    return ScientificQuestionExampleIndex(
        entries=tuple(sorted(entries, key=lambda entry: (entry.question, entry.workflow)))
    )
