# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical semantic identifier formats for cross-output scientific linking."""

from __future__ import annotations

from enum import StrEnum
import re


_SEMANTIC_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class SemanticIdNamespace(StrEnum):
    """Stable identifier namespaces for scientific outputs and review artifacts."""

    PROTEIN = "protein"
    PEPTIDE = "peptide"
    PSM = "psm"
    PTM_SITE = "ptm_site"
    PROTEIN_CLAIM = "protein-claim"
    PATHWAY_CLAIM = "pathway-claim"
    REGULATOR_CLAIM = "regulator-claim"
    PTM_CLAIM = "ptm-claim"
    PROTEIN_CARD = "protein-card"
    PROTEIN_MECHANISM_CARD = "protein-mechanism-card"
    PTM_CARD = "ptm-card"
    PATHWAY_SHIFT_CARD = "pathway-shift-card"
    KINASE_CANDIDATE_CARD = "kinase-candidate-card"
    COMPLEX_CHANGE_CARD = "complex-change-card"
    COMPARTMENT_SIGNAL_CARD = "compartment-signal-card"
    BIOMARKER_CANDIDATE_CARD = "biomarker-candidate-card"
    CROSS_STUDY_PROTEIN_CARD = "cross-study-protein-card"
    CROSS_STUDY_PATHWAY_CARD = "cross-study-pathway-card"
    RAW_SIGNAL_CARD = "raw-signal-card"
    MATRIX = "matrix"
    ARTIFACT = "artifact"


def classify_semantic_id(identifier: str) -> SemanticIdNamespace | None:
    """Return the semantic namespace used by one identifier, if recognized."""

    for namespace in SemanticIdNamespace:
        if identifier.startswith(f"{namespace.value}:"):
            return namespace
    return None


def ensure_semantic_id_namespace(
    identifier: str,
    namespace: SemanticIdNamespace,
) -> None:
    """Raise when an identifier does not use the expected semantic namespace."""

    actual = classify_semantic_id(identifier)
    if actual is not namespace:
        raise ValueError(
            f"identifier {identifier!r} should use {namespace.value!r} namespace"
        )


def build_protein_id(protein_ref: str) -> str:
    """Build the canonical protein identifier used across linked outputs."""

    return _compose_id(SemanticIdNamespace.PROTEIN, protein_ref)


def build_peptide_id(canonical_peptide: str) -> str:
    """Build the canonical peptide identifier used across linked outputs."""

    return _compose_id(SemanticIdNamespace.PEPTIDE, canonical_peptide)


def build_psm_id(
    spectrum_id: str,
    canonical_peptide: str,
    charge_state: int,
) -> str:
    """Build the canonical peptide-spectrum match identifier."""

    if charge_state < 1:
        raise ValueError("charge_state must be positive")
    return _compose_id(
        SemanticIdNamespace.PSM,
        spectrum_id,
        canonical_peptide,
        f"z{charge_state}",
    )


def build_site_id(
    protein_ref: str,
    residue: str,
    position: int,
    modification_name: str,
) -> str:
    """Build the canonical PTM-site identifier."""

    if position < 1:
        raise ValueError("position must be positive")
    residue_text = _normalize_component(residue, lowercase=False)
    if len(residue_text) != 1:
        raise ValueError("residue must resolve to exactly one character")
    return _compose_id(
        SemanticIdNamespace.PTM_SITE,
        protein_ref,
        f"{residue_text}{position}",
        modification_name,
    )


def build_protein_claim_id(protein_group_id: str) -> str:
    """Build the canonical protein-abundance claim identifier."""

    return _compose_id(SemanticIdNamespace.PROTEIN_CLAIM, protein_group_id)


def build_pathway_claim_id(
    pathway_id: str,
    condition_a: str,
    condition_b: str,
) -> str:
    """Build the canonical pathway-activity claim identifier."""

    return _compose_id(
        SemanticIdNamespace.PATHWAY_CLAIM,
        pathway_id,
        condition_a,
        condition_b,
    )


def build_regulator_claim_id(
    regulator: str,
    evidence_type: str,
    signal_surface: str,
) -> str:
    """Build the canonical regulator-activity claim identifier."""

    return _compose_id(
        SemanticIdNamespace.REGULATOR_CLAIM,
        regulator,
        evidence_type,
        signal_surface,
    )


def build_ptm_claim_id(
    site_id: str,
    condition_a: str,
    condition_b: str,
) -> str:
    """Build the canonical PTM narrative-claim identifier."""

    return _compose_id(
        SemanticIdNamespace.PTM_CLAIM,
        site_id,
        condition_a,
        condition_b,
    )


def build_protein_card_id(protein_group_id: str) -> str:
    """Build the canonical protein evidence-card identifier."""

    return _compose_id(SemanticIdNamespace.PROTEIN_CARD, protein_group_id)


def build_protein_mechanism_card_id(protein_group_id: str) -> str:
    """Build the canonical protein mechanism-card identifier."""

    return _compose_id(SemanticIdNamespace.PROTEIN_MECHANISM_CARD, protein_group_id)


def build_ptm_card_id(
    site_id: str,
    condition_a: str,
    condition_b: str,
) -> str:
    """Build the canonical PTM evidence-card identifier."""

    return _compose_id(
        SemanticIdNamespace.PTM_CARD,
        site_id,
        condition_a,
        condition_b,
    )


def build_mechanism_card_id(
    mechanism_kind: str,
    subject_id: str,
) -> str:
    """Build the canonical mechanism-card identifier for workflow cards."""

    namespace = {
        "pathway_shift": SemanticIdNamespace.PATHWAY_SHIFT_CARD,
        "kinase_candidate": SemanticIdNamespace.KINASE_CANDIDATE_CARD,
        "complex_change": SemanticIdNamespace.COMPLEX_CHANGE_CARD,
        "compartment_signal": SemanticIdNamespace.COMPARTMENT_SIGNAL_CARD,
        "biomarker_candidate": SemanticIdNamespace.BIOMARKER_CANDIDATE_CARD,
    }.get(str(getattr(mechanism_kind, "value", mechanism_kind)).strip())
    if namespace is None:
        raise ValueError(f"unsupported mechanism card kind {mechanism_kind!r}")
    return _compose_id(namespace, subject_id)


def build_cross_study_card_id(
    subject_kind: str,
    subject_id: str,
) -> str:
    """Build the canonical cross-study evidence-card identifier."""

    namespace = {
        "protein": SemanticIdNamespace.CROSS_STUDY_PROTEIN_CARD,
        "pathway": SemanticIdNamespace.CROSS_STUDY_PATHWAY_CARD,
    }.get(str(getattr(subject_kind, "value", subject_kind)).strip())
    if namespace is None:
        raise ValueError(f"unsupported cross-study subject kind {subject_kind!r}")
    return _compose_id(namespace, subject_id)


def build_raw_signal_card_id(precursor_id: str) -> str:
    """Build the canonical raw-signal evidence-card identifier."""

    return _compose_id(SemanticIdNamespace.RAW_SIGNAL_CARD, precursor_id)


def build_matrix_id(
    entity_kind: str,
    measure_kind: str,
    *,
    aggregation_method: str | None = None,
    normalization_method: str | None = None,
    imputation_method: str | None = None,
    qualifier: str | None = None,
) -> str:
    """Build the canonical quant-matrix identifier for durable matrix outputs."""

    parts = [entity_kind, measure_kind]
    if aggregation_method is not None:
        parts.append(aggregation_method)
    if normalization_method is not None:
        parts.append(normalization_method)
    if imputation_method is not None:
        parts.append(imputation_method)
    if qualifier is not None:
        parts.append(qualifier)
    return _compose_id(SemanticIdNamespace.MATRIX, *parts)


def build_artifact_id(
    relative_path: str,
    *,
    folder: str,
    artifact_kind: str,
) -> str:
    """Build the canonical workflow artifact identifier."""

    path_parts = tuple(
        _normalize_component(part, lowercase=False)
        for part in relative_path.replace("\\", "/").split("/")
        if part.strip()
    )
    if not path_parts:
        raise ValueError("relative_path must contain at least one path segment")
    return _compose_id(
        SemanticIdNamespace.ARTIFACT,
        folder,
        artifact_kind,
        *path_parts,
    )


def _compose_id(namespace: SemanticIdNamespace, *parts: object) -> str:
    normalized_parts = [
        _normalize_component(part, lowercase=False)
        for part in parts
    ]
    identifier = f"{namespace.value}:{':'.join(normalized_parts)}"
    if not _SEMANTIC_ID_PATTERN.fullmatch(identifier):
        raise ValueError(f"identifier {identifier!r} violates semantic id policy")
    return identifier


def _normalize_component(value: object, *, lowercase: bool) -> str:
    raw_value = getattr(value, "value", value)
    text = str(raw_value).strip()
    if not text:
        raise ValueError("semantic id components must not be blank")
    text = text.replace("\\", ":").replace("/", ":")
    text = text.replace("|", ".").replace(" ", "_")
    text = re.sub(r"[^A-Za-z0-9._:-]+", "-", text)
    text = re.sub(r"[:]{2,}", ":", text)
    text = re.sub(r"[-]{2,}", "-", text)
    text = text.strip(":-_.")
    if lowercase:
        text = text.lower()
    if not text:
        raise ValueError("semantic id components must contain durable characters")
    if not _SEMANTIC_ID_PATTERN.fullmatch(text):
        raise ValueError(f"semantic id component {text!r} violates policy")
    return text


__all__ = [
    "SemanticIdNamespace",
    "build_artifact_id",
    "build_cross_study_card_id",
    "build_mechanism_card_id",
    "build_matrix_id",
    "build_pathway_claim_id",
    "build_peptide_id",
    "build_protein_card_id",
    "build_protein_claim_id",
    "build_protein_id",
    "build_protein_mechanism_card_id",
    "build_psm_id",
    "build_ptm_card_id",
    "build_ptm_claim_id",
    "build_raw_signal_card_id",
    "build_regulator_claim_id",
    "build_site_id",
    "classify_semantic_id",
    "ensure_semantic_id_namespace",
]
