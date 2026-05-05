# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated citation registry for scientific reference surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.json_models import JsonModel


class CitationSourceKind(StrEnum):
    """Supported source categories for curated scientific references."""

    DATABASE = "database"
    ONTOLOGY = "ontology"
    METHOD = "method"
    REVIEW = "review"
    DATASET = "dataset"


class CitationRecord(JsonModel):
    """Stable scientific citation with version and license notes."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    source_kind: CitationSourceKind
    authors: tuple[str, ...] = Field(default_factory=tuple)
    publication_year: int = Field(..., ge=1900, le=2100)
    venue: str = Field(..., min_length=1)
    source_version: str | None = Field(default=None, min_length=1)
    doi: str | None = Field(default=None, min_length=1)
    url: str | None = Field(default=None, min_length=1)
    license_note: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)


DEFAULT_CITATION_REGISTRY: tuple[CitationRecord, ...] = (
    CitationRecord(
        citation_id="citation:uniprot_2025",
        title="UniProt: the Universal Protein Knowledgebase in 2025",
        source_kind=CitationSourceKind.DATABASE,
        authors=("The UniProt Consortium",),
        publication_year=2025,
        venue="Nucleic Acids Research",
        source_version="2025",
        doi="10.1093/nar/gkae1010",
        url="https://www.uniprot.org",
        license_note="Open-access article distributed under CC BY 4.0.",
        summary="Canonical protein sequence and annotation reference for reviewed and unreviewed protein records.",
    ),
    CitationRecord(
        citation_id="citation:psi_mod_2008",
        title="The PSI-MOD community standard for representation of protein modification data",
        source_kind=CitationSourceKind.ONTOLOGY,
        authors=(
            "Luisa Montecchi-Palazzi",
            "Ron Beavis",
            "Pierre-Alain Binz",
            "Robert J. Chalkley",
            "John Cottrell",
            "David Creasy",
            "Jim Shofstahl",
            "Sean L. Seymour",
            "John S. Garavelli",
        ),
        publication_year=2008,
        venue="Nature Biotechnology",
        source_version="2008",
        doi="10.1038/nbt0808-864",
        url="https://pubmed.ncbi.nlm.nih.gov/18688235/",
        license_note="Publisher-hosted article; reuse is subject to publisher terms.",
        summary="Community-standard representation for protein modification concepts and identifiers.",
    ),
    CitationRecord(
        citation_id="citation:psi_ms_cv_2012",
        title="The HUPO proteomics standards initiative-mass spectrometry controlled vocabulary",
        source_kind=CitationSourceKind.ONTOLOGY,
        authors=(
            "Gisbert Mayer",
            "Luisa Montecchi-Palazzi",
            "Daniel Ovelleiro",
            "Andrew R. Jones",
            "Pierre-Alain Binz",
        ),
        publication_year=2013,
        venue="Database",
        source_version="bat009",
        doi="10.1093/database/bat009",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3594986/",
        license_note="PMC-hosted article; reuse follows the article terms listed by the publisher.",
        summary="Controlled vocabulary backbone for instrument, acquisition, and mass-spectrometry process terms.",
    ),
    CitationRecord(
        citation_id="citation:target_decoy_2007",
        title="Target-decoy search strategy for increased confidence in large-scale protein identifications by mass spectrometry",
        source_kind=CitationSourceKind.METHOD,
        authors=("Joshua E. Elias", "Steven P. Gygi"),
        publication_year=2007,
        venue="Nature Methods",
        source_version="2007",
        doi="10.1038/nmeth1019",
        url="https://www.nature.com/articles/nmeth1019",
        license_note="Publisher-hosted article; reuse is subject to publisher terms.",
        summary="Foundational target-decoy framing for peptide-spectrum-match error estimation and FDR caution.",
    ),
    CitationRecord(
        citation_id="citation:ascore_2006",
        title="A probability-based approach for high-throughput protein phosphorylation analysis and site localization",
        source_kind=CitationSourceKind.METHOD,
        authors=(
            "Sean A. Beausoleil",
            "J. Villen",
            "Scott A. Gerber",
            "James Rush",
            "Steven P. Gygi",
        ),
        publication_year=2006,
        venue="Nature Biotechnology",
        source_version="2006",
        doi="10.1038/nbt1240",
        url="https://www.nature.com/articles/nbt1240",
        license_note="Publisher-hosted article; reuse is subject to publisher terms.",
        summary="Widely cited site-localization approach for phosphorylation confidence and ambiguity handling.",
    ),
    CitationRecord(
        citation_id="citation:tmtpro_2020",
        title="TMTpro reagents: a set of isobaric labeling mass tags enables simultaneous proteome-wide measurements across 16 samples",
        source_kind=CitationSourceKind.METHOD,
        authors=(
            "Jiaming Li",
            "Jonathan G. Van Vranken",
            "Laura Pontano Vaites",
            "Devin K. Schweppe",
            "Edward L. Huttlin",
            "Steven P. Gygi",
        ),
        publication_year=2020,
        venue="Nature Methods",
        source_version="TMTpro16",
        doi="10.1038/s41592-020-0781-4",
        url="https://www.nature.com/articles/s41592-020-0781-4",
        license_note="Publisher-hosted article; reuse is subject to publisher terms.",
        summary="Reference chemistry for multiplex isobaric labeling assumptions and caveats.",
    ),
    CitationRecord(
        citation_id="citation:protein_inference_2012",
        title="Inference and validation of protein identifications",
        source_kind=CitationSourceKind.REVIEW,
        authors=("Manfred Claassen",),
        publication_year=2012,
        venue="Molecular & Cellular Proteomics",
        source_version="2012",
        doi="10.1074/mcp.R111.014795",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/",
        license_note="PMC-hosted article; reuse follows the article terms listed by the publisher.",
        summary="Protein inference review covering parsimony, ambiguity, and validation tradeoffs.",
    ),
    CitationRecord(
        citation_id="citation:swath_2012",
        title="Targeted data extraction of the MS/MS spectra generated by data-independent acquisition: a new concept for consistent and accurate proteome analysis",
        source_kind=CitationSourceKind.METHOD,
        authors=(
            "Ludovic C. Gillet",
            "Pedro Navarro",
            "Simon Tate",
            "Hannes L. Rost",
            "Nikolai Selevsek",
            "Reto Aebersold",
        ),
        publication_year=2012,
        venue="Molecular & Cellular Proteomics",
        source_version="SWATH-MS",
        doi="10.1074/mcp.O111.016717",
        url="https://pubmed.ncbi.nlm.nih.gov/22261725/",
        license_note="PubMed metadata is open to read, but reuse of the primary method article remains subject to publisher terms.",
        summary="Foundational DIA/SWATH method reference for peptide-centric extraction and consistent quantitative analysis.",
    ),
)


__all__ = ["CitationRecord", "CitationSourceKind", "DEFAULT_CITATION_REGISTRY"]
