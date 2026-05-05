# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Knowledge-owned controlled vocabulary normalization for proteomics terms."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.json_models import JsonModel


class ControlledVocabularyDomain(StrEnum):
    """Supported curated vocabulary domains."""

    MODIFICATION = "modification"
    ENZYME = "enzyme"
    INSTRUMENT = "instrument"
    ASSAY_TYPE = "assay_type"


class ControlledVocabularyTerm(JsonModel):
    """Canonical curated term with normalized lookup aliases."""

    model_config = ConfigDict(extra="forbid")

    domain: ControlledVocabularyDomain = Field(..., description="Vocabulary domain.")
    term_id: str = Field(..., min_length=1, description="Stable term identifier.")
    preferred_label: str = Field(
        ..., min_length=1, description="Preferred display label."
    )
    normalized_key: str = Field(
        ..., min_length=1, description="Canonical machine-normalized lookup key."
    )
    aliases: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Accepted aliases that normalize to the preferred term.",
    )


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _default_terms() -> tuple[ControlledVocabularyTerm, ...]:
    return (
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.MODIFICATION,
            term_id="mod:phospho",
            preferred_label="Phosphorylation",
            normalized_key="phospho",
            aliases=("phosphorylation", "phosphorylated"),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.MODIFICATION,
            term_id="mod:oxidation",
            preferred_label="Oxidation",
            normalized_key="oxidation",
            aliases=("oxidized",),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.ENZYME,
            term_id="enzyme:trypsin",
            preferred_label="Trypsin",
            normalized_key="trypsin",
            aliases=("tryptic",),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.ENZYME,
            term_id="enzyme:lysc",
            preferred_label="LysC",
            normalized_key="lysc",
            aliases=("lys_c", "lys-c"),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.INSTRUMENT,
            term_id="instrument:orbitrap",
            preferred_label="Orbitrap",
            normalized_key="orbitrap",
            aliases=("thermo_orbitrap",),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.INSTRUMENT,
            term_id="instrument:timstof",
            preferred_label="timsTOF",
            normalized_key="timstof",
            aliases=("tims_tof", "bruker_timstof"),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.ASSAY_TYPE,
            term_id="assay:binding",
            preferred_label="Binding assay",
            normalized_key="binding",
            aliases=("biophysical_binding",),
        ),
        ControlledVocabularyTerm(
            domain=ControlledVocabularyDomain.ASSAY_TYPE,
            term_id="assay:target_engagement",
            preferred_label="Target engagement assay",
            normalized_key="target_engagement",
            aliases=("engagement",),
        ),
    )


DEFAULT_CONTROLLED_VOCABULARY = _default_terms()


def normalize_controlled_term(
    domain: ControlledVocabularyDomain,
    value: str,
) -> ControlledVocabularyTerm | None:
    """Resolve one raw proteomics term against the curated registry."""
    normalized = _normalize_key(value)
    for term in DEFAULT_CONTROLLED_VOCABULARY:
        if term.domain is not domain:
            continue
        aliases = {_normalize_key(alias) for alias in term.aliases}
        if normalized == term.normalized_key or normalized in aliases:
            return term
    return None


__all__ = [
    "DEFAULT_CONTROLLED_VOCABULARY",
    "ControlledVocabularyDomain",
    "ControlledVocabularyTerm",
    "normalize_controlled_term",
]
