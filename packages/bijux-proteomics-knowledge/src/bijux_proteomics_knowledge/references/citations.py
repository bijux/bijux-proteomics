# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated citation registry for scientific reference surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

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
    publisher: str = Field(..., min_length=1)
    source_locator_kind: str = Field(..., min_length=1)
    access_route: str = Field(..., min_length=1)
    source_version: str | None = Field(default=None, min_length=1)
    doi: str | None = Field(default=None, min_length=1)
    url: str | None = Field(default=None, min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    evidence_role: str = Field(..., min_length=1)
    license_note: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)

    @field_validator("retrieval_trace")
    @classmethod
    def _strip_retrieval_trace(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if not cleaned:
            raise ValueError("retrieval_trace requires at least one non-blank value")
        return cleaned


DEFAULT_CITATION_REGISTRY: tuple[CitationRecord, ...] = (
    CitationRecord(
        citation_id="citation:uniprot_2025",
        title="UniProt: the Universal Protein Knowledgebase in 2025",
        source_kind=CitationSourceKind.DATABASE,
        authors=("The UniProt Consortium",),
        publication_year=2025,
        venue="Nucleic Acids Research",
        publisher="Oxford University Press",
        source_locator_kind="doi_and_database_homepage",
        access_route="journal landing page plus UniProt canonical database homepage",
        source_version="2025",
        doi="10.1093/nar/gkae1010",
        url="https://www.uniprot.org",
        retrieval_trace=(
            "DOI metadata and the UniProt database homepage were reviewed on 2026-05-05.",
            "The cited 2025 knowledgebase release remains the reference version for reviewed-proteome grounding in this package.",
        ),
        evidence_role="Canonical reviewed-proteome and annotation anchor for identifier and protein-meaning claims.",
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
        publisher="Springer Nature",
        source_locator_kind="doi_and_pubmed_record",
        access_route="publisher landing page plus PubMed metadata record",
        source_version="2008",
        doi="10.1038/nbt0808-864",
        url="https://pubmed.ncbi.nlm.nih.gov/18688235/",
        retrieval_trace=(
            "Publisher DOI metadata and the PubMed record were reviewed on 2026-05-05.",
            "The 2008 PSI-MOD publication remains the ontology-grounding anchor for PTM concepts in this package.",
        ),
        evidence_role="Primary ontology provenance for PTM concept labels and normalization.",
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
        publisher="Oxford University Press",
        source_locator_kind="doi_and_pmc_mirror",
        access_route="journal DOI metadata with PMC full-text mirror",
        source_version="bat009",
        doi="10.1093/database/bat009",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3594986/",
        retrieval_trace=(
            "DOI metadata and the PMC-hosted full-text mirror were reviewed on 2026-05-05.",
            "Vocabulary term usage in this package is tied to the bat009 PSI-MS controlled-vocabulary framing.",
        ),
        evidence_role="Controlled-vocabulary backbone for instrument and acquisition terminology.",
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
        publisher="Springer Nature",
        source_locator_kind="doi_and_publisher_record",
        access_route="publisher landing page with DOI metadata",
        source_version="2007",
        doi="10.1038/nmeth1019",
        url="https://www.nature.com/articles/nmeth1019",
        retrieval_trace=(
            "Publisher DOI metadata were reviewed on 2026-05-05.",
            "This 2007 method paper remains the reference anchor for target-decoy framing and FDR scope cautions.",
        ),
        evidence_role="Method anchor for target-decoy confidence framing and identification-scope caveats.",
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
        publisher="Springer Nature",
        source_locator_kind="doi_and_publisher_record",
        access_route="publisher landing page with DOI metadata",
        source_version="2006",
        doi="10.1038/nbt1240",
        url="https://www.nature.com/articles/nbt1240",
        retrieval_trace=(
            "Publisher DOI metadata were reviewed on 2026-05-05.",
            "This 2006 localization method remains the primary evidence anchor for PTM site-confidence interpretation.",
        ),
        evidence_role="Method anchor for phosphorylation localization confidence and ambiguity handling.",
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
        publisher="Springer Nature",
        source_locator_kind="doi_and_publisher_record",
        access_route="publisher landing page with DOI metadata",
        source_version="TMTpro16",
        doi="10.1038/s41592-020-0781-4",
        url="https://www.nature.com/articles/s41592-020-0781-4",
        retrieval_trace=(
            "Publisher DOI metadata were reviewed on 2026-05-05.",
            "The TMTpro16 method framing remains the current label-chemistry anchor for multiplex caveats in this package.",
        ),
        evidence_role="Method anchor for reporter-channel semantics, isobaric chemistry, and multiplex caveats.",
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
        publisher="American Society for Biochemistry and Molecular Biology",
        source_locator_kind="doi_and_pmc_mirror",
        access_route="journal DOI metadata with PMC full-text mirror",
        source_version="2012",
        doi="10.1074/mcp.R111.014795",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/",
        retrieval_trace=(
            "DOI metadata and the PMC-hosted full-text mirror were reviewed on 2026-05-05.",
            "This review remains the primary rollup-caution anchor for protein inference and evidence-level scope.",
        ),
        evidence_role="Review anchor for protein inference ambiguity, rollup caution, and evidence-level qualification.",
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
        publisher="American Society for Biochemistry and Molecular Biology",
        source_locator_kind="doi_and_pubmed_record",
        access_route="PubMed metadata record with DOI-linked journal landing page",
        source_version="SWATH-MS",
        doi="10.1074/mcp.O111.016717",
        url="https://pubmed.ncbi.nlm.nih.gov/22261725/",
        retrieval_trace=(
            "PubMed metadata and DOI-linked journal records were reviewed on 2026-05-05.",
            "This SWATH-MS method paper remains the anchor for library-conditioned DIA extraction framing in this package.",
        ),
        evidence_role="Method anchor for DIA extraction semantics, library scope, and peptide-centric transition evidence.",
        license_note="PubMed metadata is open to read, but reuse of the primary method article remains subject to publisher terms.",
        summary="Foundational DIA/SWATH method reference for peptide-centric extraction and consistent quantitative analysis.",
    ),
)


__all__ = ["CitationRecord", "CitationSourceKind", "DEFAULT_CITATION_REGISTRY"]
