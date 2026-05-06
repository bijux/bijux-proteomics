# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Ontology mappings needed by shared proteomics reference workflows."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.serialization.json_models import JsonModel


class KnowledgeOntologyDomain(StrEnum):
    """Curated ontology families consumed by the knowledge package."""

    UNIPROT = "uniprot"
    PTM = "ptm"
    INSTRUMENT = "instrument"
    ACQUISITION_MODE = "acquisition_mode"


class KnowledgeOntologyMapping(JsonModel):
    """One curated ontology mapping with evidence provenance."""

    model_config = ConfigDict(extra="forbid")

    domain: KnowledgeOntologyDomain
    term_id: str = Field(..., min_length=1)
    preferred_label: str = Field(..., min_length=1)
    normalized_key: str = Field(..., min_length=1)
    aliases: tuple[str, ...] = Field(default_factory=tuple)
    source_name: str = Field(..., min_length=1)
    external_accession: str | None = Field(default=None, min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("normalized_key")
    @classmethod
    def _normalize_key(cls, value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")

    @field_validator("aliases")
    @classmethod
    def _normalize_aliases(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            sorted(
                alias.strip().lower().replace("-", "_").replace(" ", "_")
                for alias in value
                if alias.strip()
            )
        )

    @field_validator("version_trace", "retrieval_trace", "citation_ids")
    @classmethod
    def _strip_trace_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_ONTOLOGY_MAPPINGS: tuple[KnowledgeOntologyMapping, ...] = (
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.UNIPROT,
        term_id="uniprot:reviewed_entry",
        preferred_label="UniProt reviewed entry",
        normalized_key="reviewed_entry",
        aliases=("swissprot", "swiss_prot", "reviewed protein"),
        source_name="UniProtKB",
        external_accession="reviewed",
        version_trace=("Pinned to the UniProt 2025 release framing used by citation:uniprot_2025.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:uniprot_2025",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.UNIPROT,
        term_id="uniprot:isoform_entry",
        preferred_label="UniProt isoform entry",
        normalized_key="isoform_entry",
        aliases=("protein isoform", "splice isoform"),
        source_name="UniProtKB",
        external_accession="isoform",
        version_trace=("Pinned to the UniProt 2025 release framing used by citation:uniprot_2025.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:uniprot_2025",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.PTM,
        term_id="ptm:phosphorylation",
        preferred_label="Phosphorylation",
        normalized_key="phosphorylation",
        aliases=("phospho", "phosphorylated"),
        source_name="PSI-MOD",
        external_accession="MOD:00696",
        version_trace=("Pinned to the PSI-MOD concept framing cited in citation:psi_mod_2008.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.PTM,
        term_id="ptm:oxidation",
        preferred_label="Oxidation",
        normalized_key="oxidation",
        aliases=("oxidized", "methionine oxidation"),
        source_name="PSI-MOD",
        external_accession=None,
        version_trace=("Pinned to the PSI-MOD concept framing cited in citation:psi_mod_2008.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.INSTRUMENT,
        term_id="instrument:orbitrap",
        preferred_label="Orbitrap",
        normalized_key="orbitrap",
        aliases=("thermo orbitrap", "exploris", "fusion lumos"),
        source_name="PSI-MS CV",
        external_accession=None,
        version_trace=("Pinned to the PSI-MS controlled-vocabulary framing cited in citation:psi_ms_cv_2012.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_ms_cv_2012",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.INSTRUMENT,
        term_id="instrument:timstof",
        preferred_label="timsTOF",
        normalized_key="timstof",
        aliases=("bruker timstof", "tims_tof"),
        source_name="PSI-MS CV",
        external_accession=None,
        version_trace=("Pinned to the PSI-MS controlled-vocabulary framing cited in citation:psi_ms_cv_2012.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_ms_cv_2012",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.ACQUISITION_MODE,
        term_id="acquisition_mode:dda",
        preferred_label="Data-dependent acquisition",
        normalized_key="dda",
        aliases=("data dependent acquisition", "ida"),
        source_name="PSI-MS CV",
        external_accession=None,
        version_trace=("Pinned to the PSI-MS controlled-vocabulary framing cited in citation:psi_ms_cv_2012.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_ms_cv_2012",),
    ),
    KnowledgeOntologyMapping(
        domain=KnowledgeOntologyDomain.ACQUISITION_MODE,
        term_id="acquisition_mode:dia",
        preferred_label="Data-independent acquisition",
        normalized_key="dia",
        aliases=("data independent acquisition", "swath", "swath_ms"),
        source_name="PSI-MS CV",
        external_accession=None,
        version_trace=("Pinned to the PSI-MS and SWATH vocabulary framing cited in citation:psi_ms_cv_2012 and citation:swath_2012.",),
        retrieval_trace=("Ontology label and alias review was refreshed against the linked source on 2026-05-05.",),
        citation_ids=("citation:psi_ms_cv_2012", "citation:swath_2012"),
    ),
)


def resolve_ontology_mapping(
    domain: KnowledgeOntologyDomain,
    value: str,
) -> KnowledgeOntologyMapping | None:
    """Resolve one raw value against the curated ontology mappings."""
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    for mapping in DEFAULT_ONTOLOGY_MAPPINGS:
        if mapping.domain is not domain:
            continue
        if normalized == mapping.normalized_key or normalized in mapping.aliases:
            return mapping
    return None


__all__ = [
    "DEFAULT_ONTOLOGY_MAPPINGS",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "resolve_ontology_mapping",
]
