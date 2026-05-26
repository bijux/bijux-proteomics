# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated lab handoff surfaces for explanation, risk, and export owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "AlternativeAssayPlanComparison",
    "AlternativeAssayPlanOption",
    "AssayRiskAssessment",
    "AssayRiskCode",
    "AssayRiskFinding",
    "AssayRiskSeverity",
    "HandoffAuthorityBoundary",
    "HandoffAuthorityOwner",
    "HandoffExplanation",
    "HandoffSupportLevel",
    "HandoffSupportStatement",
    "LabArtifactCompatibilityReport",
    "LabArtifactContractIssue",
    "LabArtifactContractRegistry",
    "LabArtifactProfile",
    "LabArtifactSchemaContract",
    "LabArtifactUpgradeAdvisory",
    "LabRunQcFeedbackEntry",
    "LabRunQcFeedbackReasonCode",
    "LabRunQcFeedbackReport",
    "LabRunQcFeedbackStatus",
    "LabRunQcObservation",
    "LabExecutionRefusal",
    "LimsExportBundle",
    "LimsExportRecord",
    "LimsFieldMapping",
    "PtmLabAssayRisk",
    "PtmLabValidationPacket",
    "PtmLabValidationTargetEntry",
    "TargetedTransitionCandidate",
    "TargetedTransitionReview",
    "TargetedTransitionReviewEntry",
    "TransitionReviewDisposition",
    "artifacts",
    "assess_assay_risk",
    "build_canonical_artifact_envelope",
    "build_handoff_explanation",
    "build_lab_artifact_upgrade_advisory",
    "build_lab_run_qc_feedback_report",
    "build_lims_export_bundle",
    "build_ptm_lab_validation_packet",
    "compare_alternative_assay_plans",
    "default_lab_artifact_contract_registry",
    "default_lab_artifact_profile",
    "diff_model_payloads",
    "evaluate_lab_artifact_compatibility",
    "evaluate_lab_artifact_schema_contract",
    "evaluate_lab_artifact_with_registry",
    "explanations",
    "exports",
    "lint_lab_artifact_contract_registry",
    "ptm",
    "qc_feedback",
    "refuse_irresponsible_assay_handoff",
    "review_targeted_transition_candidates",
    "risk",
    "serialization",
    "transitions",
    "verify_canonical_artifact_envelope",
]

_HANDOFF_PUBLIC_EXPORTS = {
    "AlternativeAssayPlanComparison": (
        "bijux_proteomics_lab.handoffs.exports",
        "AlternativeAssayPlanComparison",
    ),
    "AlternativeAssayPlanOption": (
        "bijux_proteomics_lab.handoffs.exports",
        "AlternativeAssayPlanOption",
    ),
    "AssayRiskAssessment": (
        "bijux_proteomics_lab.handoffs.risk",
        "AssayRiskAssessment",
    ),
    "AssayRiskCode": ("bijux_proteomics_lab.handoffs.risk", "AssayRiskCode"),
    "AssayRiskFinding": ("bijux_proteomics_lab.handoffs.risk", "AssayRiskFinding"),
    "AssayRiskSeverity": ("bijux_proteomics_lab.handoffs.risk", "AssayRiskSeverity"),
    "HandoffAuthorityBoundary": (
        "bijux_proteomics_lab.handoffs.explanations",
        "HandoffAuthorityBoundary",
    ),
    "HandoffAuthorityOwner": (
        "bijux_proteomics_lab.handoffs.explanations",
        "HandoffAuthorityOwner",
    ),
    "HandoffExplanation": (
        "bijux_proteomics_lab.handoffs.explanations",
        "HandoffExplanation",
    ),
    "HandoffSupportLevel": (
        "bijux_proteomics_lab.handoffs.explanations",
        "HandoffSupportLevel",
    ),
    "HandoffSupportStatement": (
        "bijux_proteomics_lab.handoffs.explanations",
        "HandoffSupportStatement",
    ),
    "LabArtifactCompatibilityReport": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactCompatibilityReport",
    ),
    "LabArtifactContractIssue": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactContractIssue",
    ),
    "LabArtifactContractRegistry": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactContractRegistry",
    ),
    "LabArtifactProfile": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactProfile",
    ),
    "LabArtifactSchemaContract": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactSchemaContract",
    ),
    "LabArtifactUpgradeAdvisory": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "LabArtifactUpgradeAdvisory",
    ),
    "LabRunQcFeedbackEntry": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "LabRunQcFeedbackEntry",
    ),
    "LabRunQcFeedbackReasonCode": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "LabRunQcFeedbackReasonCode",
    ),
    "LabRunQcFeedbackReport": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "LabRunQcFeedbackReport",
    ),
    "LabRunQcFeedbackStatus": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "LabRunQcFeedbackStatus",
    ),
    "LabRunQcObservation": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "LabRunQcObservation",
    ),
    "LabExecutionRefusal": (
        "bijux_proteomics_lab.handoffs.explanations",
        "LabExecutionRefusal",
    ),
    "LimsExportBundle": ("bijux_proteomics_lab.handoffs.exports", "LimsExportBundle"),
    "LimsExportRecord": ("bijux_proteomics_lab.handoffs.exports", "LimsExportRecord"),
    "LimsFieldMapping": ("bijux_proteomics_lab.handoffs.exports", "LimsFieldMapping"),
    "PtmLabAssayRisk": ("bijux_proteomics_lab.handoffs.ptm", "PtmLabAssayRisk"),
    "PtmLabValidationPacket": (
        "bijux_proteomics_lab.handoffs.ptm",
        "PtmLabValidationPacket",
    ),
    "PtmLabValidationTargetEntry": (
        "bijux_proteomics_lab.handoffs.ptm",
        "PtmLabValidationTargetEntry",
    ),
    "TargetedTransitionCandidate": (
        "bijux_proteomics_lab.handoffs.transitions",
        "TargetedTransitionCandidate",
    ),
    "TargetedTransitionReview": (
        "bijux_proteomics_lab.handoffs.transitions",
        "TargetedTransitionReview",
    ),
    "TargetedTransitionReviewEntry": (
        "bijux_proteomics_lab.handoffs.transitions",
        "TargetedTransitionReviewEntry",
    ),
    "TransitionReviewDisposition": (
        "bijux_proteomics_lab.handoffs.transitions",
        "TransitionReviewDisposition",
    ),
    "artifacts": ("bijux_proteomics_lab.handoffs", "artifacts"),
    "assess_assay_risk": ("bijux_proteomics_lab.handoffs.risk", "assess_assay_risk"),
    "build_canonical_artifact_envelope": (
        "bijux_proteomics_lab.handoffs.serialization",
        "build_canonical_artifact_envelope",
    ),
    "build_handoff_explanation": (
        "bijux_proteomics_lab.handoffs.explanations",
        "build_handoff_explanation",
    ),
    "build_lab_artifact_upgrade_advisory": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "build_lab_artifact_upgrade_advisory",
    ),
    "build_lab_run_qc_feedback_report": (
        "bijux_proteomics_lab.handoffs.qc_feedback",
        "build_lab_run_qc_feedback_report",
    ),
    "build_lims_export_bundle": (
        "bijux_proteomics_lab.handoffs.exports",
        "build_lims_export_bundle",
    ),
    "build_ptm_lab_validation_packet": (
        "bijux_proteomics_lab.handoffs.ptm",
        "build_ptm_lab_validation_packet",
    ),
    "compare_alternative_assay_plans": (
        "bijux_proteomics_lab.handoffs.exports",
        "compare_alternative_assay_plans",
    ),
    "default_lab_artifact_contract_registry": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "default_lab_artifact_contract_registry",
    ),
    "default_lab_artifact_profile": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "default_lab_artifact_profile",
    ),
    "diff_model_payloads": (
        "bijux_proteomics_lab.handoffs.serialization",
        "diff_model_payloads",
    ),
    "evaluate_lab_artifact_compatibility": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "evaluate_lab_artifact_compatibility",
    ),
    "evaluate_lab_artifact_schema_contract": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "evaluate_lab_artifact_schema_contract",
    ),
    "evaluate_lab_artifact_with_registry": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "evaluate_lab_artifact_with_registry",
    ),
    "explanations": ("bijux_proteomics_lab.handoffs", "explanations"),
    "exports": ("bijux_proteomics_lab.handoffs", "exports"),
    "lint_lab_artifact_contract_registry": (
        "bijux_proteomics_lab.handoffs.artifacts",
        "lint_lab_artifact_contract_registry",
    ),
    "ptm": ("bijux_proteomics_lab.handoffs", "ptm"),
    "qc_feedback": ("bijux_proteomics_lab.handoffs", "qc_feedback"),
    "refuse_irresponsible_assay_handoff": (
        "bijux_proteomics_lab.handoffs.explanations",
        "refuse_irresponsible_assay_handoff",
    ),
    "review_targeted_transition_candidates": (
        "bijux_proteomics_lab.handoffs.transitions",
        "review_targeted_transition_candidates",
    ),
    "risk": ("bijux_proteomics_lab.handoffs", "risk"),
    "serialization": ("bijux_proteomics_lab.handoffs", "serialization"),
    "transitions": ("bijux_proteomics_lab.handoffs", "transitions"),
    "verify_canonical_artifact_envelope": (
        "bijux_proteomics_lab.handoffs.serialization",
        "verify_canonical_artifact_envelope",
    ),
}
_HANDOFF_SUBMODULES = {
    name: f"{__name__}.{name}"
    for name in (
        "artifacts",
        "explanations",
        "exports",
        "ptm",
        "qc_feedback",
        "risk",
        "serialization",
        "transitions",
    )
}


def __getattr__(name: str) -> Any:
    """Load curated handoff owners lazily and block infrastructure leakage."""

    submodule_name = _HANDOFF_SUBMODULES.get(name)
    if submodule_name is not None:
        return import_module(submodule_name)

    target = _HANDOFF_PUBLIC_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = target
    module = import_module(module_name)
    return getattr(module, attribute_name)
