# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated literature groups for recurring workflow interpretation themes."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel


class LiteratureFocusArea(StrEnum):
    """Literature-group themes curated by the knowledge package."""

    ENZYME = "enzyme"
    QC = "qc"
    FDR = "fdr"
    QUANTIFICATION = "quantification"
    PTM = "ptm"
    DIA = "dia"
    TARGETED = "targeted"


class LiteratureGroup(JsonModel):
    """One curated literature cluster with explicit workflow links."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    focus_area: LiteratureFocusArea
    title: str = Field(..., min_length=1)
    curation_note: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    context_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator(
        "citation_ids",
        "benchmark_ids",
        "context_ids",
        "version_trace",
        "retrieval_trace",
    )
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_LITERATURE_GROUPS: tuple[LiteratureGroup, ...] = (
    LiteratureGroup(
        group_id="literature:enzyme_panel_comparability",
        focus_area=LiteratureFocusArea.ENZYME,
        title="Protease specificity and panel comparability",
        curation_note="Enzyme-sensitive benchmarking needs literature support for cleavage expectations, peptide detectability, and the limits of cross-protease comparison.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:uniprot_2025", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        context_ids=(
            "context:digestion_tryptic_specificity",
            "context:digestion_panel_scope",
        ),
    ),
    LiteratureGroup(
        group_id="literature:qc_signal_quality",
        focus_area=LiteratureFocusArea.QC,
        title="Signal quality and workflow confidence",
        curation_note="Quality-control interpretation in this suite is grounded in references that explain why apparently clean quantitative or identification outputs can still hide scope problems.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=(
            "citation:target_decoy_2007",
            "citation:protein_inference_2012",
            "citation:swath_2012",
        ),
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
            "benchmark:targeted_transition_quality_control",
        ),
        context_ids=(
            "context:dia_transition_grounding",
            "context:quant_missingness_is_informative",
        ),
    ),
    LiteratureGroup(
        group_id="literature:fdr_scope",
        focus_area=LiteratureFocusArea.FDR,
        title="FDR scope and identification confidence",
        curation_note="This literature group keeps target-decoy framing and protein-level inference caveats attached to any confidence claim that moves across evidence levels.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        context_ids=("context:digestion_tryptic_specificity",),
    ),
    LiteratureGroup(
        group_id="literature:quantification_rollup",
        focus_area=LiteratureFocusArea.QUANTIFICATION,
        title="Quantification missingness and rollup interpretation",
        curation_note="Quantitative summaries need literature support for missingness, reporter-channel semantics, and the difference between peptide-level and protein-level claims.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=(
            "citation:tmtpro_2020",
            "citation:protein_inference_2012",
            "citation:uniprot_2025",
        ),
        benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
        ),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:quant_rollup_changes_claim_scope",
        ),
    ),
    LiteratureGroup(
        group_id="literature:ptm_localization",
        focus_area=LiteratureFocusArea.PTM,
        title="PTM localization and occupancy caution",
        curation_note="The PTM group keeps modification ontology grounding separate from site-localization confidence and occupancy-style quantitative interpretation.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        context_ids=(
            "context:ptm_localization_confidence",
            "context:ptm_occupancy_scope",
        ),
    ),
    LiteratureGroup(
        group_id="literature:ptm_regulation_limits",
        focus_area=LiteratureFocusArea.PTM,
        title="PTM regulation and occupancy limits",
        curation_note="PTM interpretation stays honest when localization confidence is kept distinct from occupancy, regulation, and pathway-level biological storytelling.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        context_ids=(
            "context:ptm_occupancy_scope",
            "context:ptm_regulation_boundary",
        ),
    ),
    LiteratureGroup(
        group_id="literature:dia_library_scope",
        focus_area=LiteratureFocusArea.DIA,
        title="DIA extraction and spectral-library scope",
        curation_note="This group captures the peptide-centric and library-scoped character of DIA claims so downstream packages do not overstate protein certainty.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012"),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        context_ids=(
            "context:dia_transition_grounding",
            "context:dia_library_scope",
        ),
    ),
    LiteratureGroup(
        group_id="literature:targeted_rollup_caution",
        focus_area=LiteratureFocusArea.TARGETED,
        title="Targeted evidence and protein rollup caution",
        curation_note="Targeted summaries remain grounded when transition-level evidence and protein-level inference are kept explicitly connected instead of being conflated.",
        version_trace=("This literature cluster was reviewed against its linked benchmark and context surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citations, context ids, and benchmark ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
        context_ids=("context:quant_rollup_changes_claim_scope",),
    ),
)


__all__ = [
    "DEFAULT_LITERATURE_GROUPS",
    "LiteratureFocusArea",
    "LiteratureGroup",
]
