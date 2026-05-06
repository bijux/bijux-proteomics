# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Corpus manifests for bundled fixtures and external scientific references."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class KnowledgeCorpusSourceKind(StrEnum):
    """Supported corpus source kinds for curated reference knowledge."""

    BUNDLED_FIXTURE = "bundled_fixture"
    EXTERNAL_REFERENCE = "external_reference"


class CorpusManifest(JsonModel):
    """One curated corpus entry used by benchmark manifests or rule mappings."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    source_kind: KnowledgeCorpusSourceKind
    format_family: str = Field(..., min_length=1)
    scientific_scope: str = Field(..., min_length=1)
    source_version: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    license_and_reuse_note: str = Field(..., min_length=1)
    repo_relative_path: str | None = Field(default=None, min_length=1)
    reference_locator: str | None = Field(default=None, min_length=1)
    reference_accession: str | None = Field(default=None, min_length=1)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("version_trace", "retrieval_trace", "citation_ids", "benchmark_ids")
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned

    @model_validator(mode="after")
    def _validate_source_fields(self) -> CorpusManifest:
        if self.source_kind is KnowledgeCorpusSourceKind.BUNDLED_FIXTURE:
            if self.repo_relative_path is None:
                raise ValueError("bundled fixtures require repo_relative_path")
            if (
                self.reference_locator is not None
                or self.reference_accession is not None
            ):
                raise ValueError(
                    "bundled fixtures must not declare external reference fields"
                )
        if self.source_kind is KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE:
            if self.reference_locator is None:
                raise ValueError("external references require reference_locator")
            if self.repo_relative_path is not None:
                raise ValueError(
                    "external references must not declare repo_relative_path"
                )
            if not self.citation_ids:
                raise ValueError("external references require at least one citation id")
        return self


DEFAULT_CORPUS_MANIFESTS: tuple[CorpusManifest, ...] = (
    CorpusManifest(
        corpus_id="corpus:search_adapter_fixture_suite",
        display_name="Search adapter fixture suite",
        source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE,
        format_family="tsv_and_params",
        scientific_scope="Cross-engine DDA and DIA adapter normalization fixtures.",
        source_version="Checked-in repository fixture snapshot reviewed on 2026-05-05.",
        version_trace=(
            "The corpus points to the checked-in adapter fixture tree under packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora.",
        ),
        retrieval_trace=(
            "Repo fixture paths were verified on 2026-05-05 against the current core fixture tree.",
        ),
        license_and_reuse_note="Bundled repository fixtures are reused only inside this package as reviewable normalization evidence, not as a claim of vendor-tool redistribution rights.",
        repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora",
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:dia_library_extraction_consistency",
        ),
    ),
    CorpusManifest(
        corpus_id="corpus:quant_fixture_suite",
        display_name="Quantification fixture suite",
        source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE,
        format_family="tsv_and_design",
        scientific_scope="Bundled LFQ and multiplex quantification fixture inputs.",
        source_version="Checked-in repository fixture snapshot reviewed on 2026-05-05.",
        version_trace=(
            "The corpus points to the checked-in quantification fixture tree under packages/bijux-proteomics-core/tests/fixtures/quant.",
        ),
        retrieval_trace=(
            "Repo fixture paths were verified on 2026-05-05 against the current quantification fixture tree.",
        ),
        license_and_reuse_note="Bundled repository fixtures are reused as internal benchmark inputs and do not imply redistribution rights for any external quantification software outputs beyond the checked-in test data.",
        repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant",
        benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
        ),
    ),
    CorpusManifest(
        corpus_id="corpus:ptm_fixture_suite",
        display_name="PTM localization fixture suite",
        source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE,
        format_family="tsv",
        scientific_scope="Bundled PTM localization features and expected score patterns.",
        source_version="Checked-in repository fixture snapshot reviewed on 2026-05-05.",
        version_trace=(
            "The corpus points to the checked-in PTM fixture tree under packages/bijux-proteomics-core/tests/fixtures/ptm.",
        ),
        retrieval_trace=(
            "Repo fixture paths were verified on 2026-05-05 against the current PTM fixture tree.",
        ),
        license_and_reuse_note="Bundled PTM fixtures are reused as internal localization evidence and do not broaden reuse rights beyond the repository’s checked-in test data.",
        repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/ptm",
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
    ),
    CorpusManifest(
        corpus_id="corpus:chromatogram_qc_fixture",
        display_name="Chromatogram QC fixture",
        source_kind=KnowledgeCorpusSourceKind.BUNDLED_FIXTURE,
        format_family="tsv",
        scientific_scope="Transition-level chromatogram quality-control fixture.",
        source_version="Checked-in repository fixture snapshot reviewed on 2026-05-05.",
        version_trace=(
            "The corpus points to the checked-in chromatogram QC fixture under packages/bijux-proteomics-core/tests/fixtures/formats.",
        ),
        retrieval_trace=(
            "Repo fixture paths were verified on 2026-05-05 against the current chromatogram fixture tree.",
        ),
        license_and_reuse_note="Bundled chromatogram fixtures are reused as internal QC evidence and do not imply redistribution rights for any vendor chromatogram exports beyond the checked-in test data.",
        repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/formats/chromatogram_qc.tsv",
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
    ),
    CorpusManifest(
        corpus_id="corpus:uniprot_reference_proteome",
        display_name="UniProt reviewed reference proteome",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="database",
        scientific_scope="Reviewed protein sequence and annotation reference used for identifier grounding.",
        source_version="UniProt 2025 knowledgebase release.",
        version_trace=(
            "This corpus is pinned to the 2025 UniProt release cited in citation:uniprot_2025.",
        ),
        retrieval_trace=(
            "The reference homepage and cited release metadata were reviewed on 2026-05-05.",
        ),
        license_and_reuse_note="Used as an external scientific reference with citation-backed attribution; reuse remains governed by the cited UniProt terms and the article’s CC BY 4.0 notice.",
        reference_locator="https://www.uniprot.org",
        reference_accession="doi:10.1093/nar/gkae1010",
        citation_ids=("citation:uniprot_2025",),
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
        ),
    ),
    CorpusManifest(
        corpus_id="corpus:target_decoy_method_reference",
        display_name="Target-decoy method reference",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="journal_article",
        scientific_scope="Foundational identification-confidence framing for target-decoy validation.",
        source_version="2007 target-decoy method publication.",
        version_trace=(
            "This corpus is pinned to the published target-decoy method record cited in citation:target_decoy_2007.",
        ),
        retrieval_trace=(
            "Publisher DOI metadata were reviewed on 2026-05-05 for the linked method article.",
        ),
        license_and_reuse_note="Used as an external scientific reference with citation-backed attribution; reuse is limited by the publisher-hosted article terms.",
        reference_locator="https://www.nature.com/articles/nmeth1019",
        reference_accession="doi:10.1038/nmeth1019",
        citation_ids=("citation:target_decoy_2007",),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
    ),
    CorpusManifest(
        corpus_id="corpus:swath_method_reference",
        display_name="SWATH method reference",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="journal_article",
        scientific_scope="DIA extraction and SWATH-style peptide-centric analysis reference.",
        source_version="SWATH-MS method publication reviewed on 2026-05-05.",
        version_trace=(
            "This corpus is pinned to the SWATH-MS method record cited in citation:swath_2012.",
        ),
        retrieval_trace=(
            "PubMed metadata and DOI-linked records were reviewed on 2026-05-05 for the linked method article.",
        ),
        license_and_reuse_note="Used as an external scientific reference with citation-backed attribution; reuse remains governed by the linked article terms rather than by repository-local redistribution.",
        reference_locator="https://pubmed.ncbi.nlm.nih.gov/22261725/",
        reference_accession="doi:10.1074/mcp.O111.016717",
        citation_ids=("citation:swath_2012",),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
    ),
    CorpusManifest(
        corpus_id="corpus:ptm_localization_method_reference",
        display_name="PTM localization method reference",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="journal_article",
        scientific_scope="Phosphorylation localization evidence interpretation and PTM concept grounding.",
        source_version="2006-2008 PTM localization and ontology reference set.",
        version_trace=(
            "This corpus is pinned to the Ascore and PSI-MOD publications cited in citation:ascore_2006 and citation:psi_mod_2008.",
        ),
        retrieval_trace=(
            "Publisher DOI metadata and citation links were reviewed on 2026-05-05 for the linked PTM references.",
        ),
        license_and_reuse_note="Used as an external scientific reference set with citation-backed attribution; reuse remains governed by the linked publisher-hosted articles.",
        reference_locator="https://www.nature.com/articles/nbt1240",
        reference_accession="doi:10.1038/nbt1240",
        citation_ids=("citation:ascore_2006", "citation:psi_mod_2008"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
    ),
    CorpusManifest(
        corpus_id="corpus:tmtpro_labeling_reference",
        display_name="TMTpro labeling reference",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="journal_article",
        scientific_scope="Isobaric label chemistry assumptions for multiplex reporter interpretation.",
        source_version="TMTpro16 method publication.",
        version_trace=(
            "This corpus is pinned to the TMTpro method record cited in citation:tmtpro_2020.",
        ),
        retrieval_trace=(
            "Publisher DOI metadata were reviewed on 2026-05-05 for the linked multiplex chemistry article.",
        ),
        license_and_reuse_note="Used as an external scientific reference with citation-backed attribution; reuse remains governed by the linked article terms.",
        reference_locator="https://www.nature.com/articles/s41592-020-0781-4",
        reference_accession="doi:10.1038/s41592-020-0781-4",
        citation_ids=("citation:tmtpro_2020",),
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
    ),
    CorpusManifest(
        corpus_id="corpus:protein_inference_review_reference",
        display_name="Protein inference review reference",
        source_kind=KnowledgeCorpusSourceKind.EXTERNAL_REFERENCE,
        format_family="review_article",
        scientific_scope="Protein-level rollup caution for targeted or summary-oriented evidence outputs.",
        source_version="2012 protein inference review.",
        version_trace=(
            "This corpus is pinned to the review cited in citation:protein_inference_2012.",
        ),
        retrieval_trace=(
            "DOI metadata and PMC mirror links were reviewed on 2026-05-05 for the linked review article.",
        ),
        license_and_reuse_note="Used as an external scientific reference with citation-backed attribution; reuse remains governed by the linked review terms rather than by repository-local redistribution.",
        reference_locator="https://pmc.ncbi.nlm.nih.gov/articles/PMC3494198/",
        reference_accession="doi:10.1074/mcp.R111.014795",
        citation_ids=("citation:protein_inference_2012",),
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
    ),
)


__all__ = [
    "CorpusManifest",
    "DEFAULT_CORPUS_MANIFESTS",
    "KnowledgeCorpusSourceKind",
]
