# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Package-level scientific examples for the core public surface."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    PsmParseReport,
    PsmRecord,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    ScoreOrientation,
    SearchAdapterKind,
    SearchAdapterManifest,
    SearchAdapterNormalizationReport,
    SearchResultFamily,
    SearchResultFamilyPolicy,
)
from bijux_proteomics.identification.search_adapters.input_review import (
    build_search_adapter_field_accounting,
)
from bijux_proteomics.ptm.review import evaluate_glycopeptide_support_boundary
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    build_digest_policy,
    compute_digest_policy_hash,
    digest_sequence,
    get_protease_rule,
)
from bijux_proteomics_foundation import JsonModel


class ScientificExampleObservation(JsonModel):
    """One user-readable observation inside a package example."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    scientific_meaning: str = Field(..., min_length=1)


class CoreScientificExample(JsonModel):
    """One package-level core example grounded in real behavior."""

    model_config = ConfigDict(extra="forbid")

    example_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    scientific_question: str = Field(..., min_length=1)
    owner_surface: str = Field(..., min_length=1)
    observations: tuple[ScientificExampleObservation, ...] = Field(
        default_factory=tuple
    )
    caveats: tuple[str, ...] = Field(default_factory=tuple)


def build_sequence_digest_example() -> CoreScientificExample:
    """Show a proteomics reader a simple digest example with no runtime context."""

    sequence = "MPEPTIDERKPEPTIDEK"
    peptides = digest_sequence(
        sequence,
        protease=get_protease_rule("trypsin"),
        missed_cleavages=1,
        mode=PeptideDigestionMode.FULL,
    )
    policy = build_digest_policy(
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        missed_cleavages=1,
        min_length=7,
        max_length=30,
        min_mass=None,
        max_mass=None,
    )
    policy_hash = compute_digest_policy_hash(policy)
    peptide_sequences = tuple(peptide.sequence for peptide in peptides)
    return CoreScientificExample(
        example_id="core.sequence-digest",
        title="Tryptic digest walkthrough",
        scientific_question=(
            "Which peptides does a simple tryptic digest yield before any runtime or "
            "downstream review layer gets involved?"
        ),
        owner_surface="bijux_proteomics.sequences.digestion",
        observations=(
            ScientificExampleObservation(
                label="input_sequence",
                value=sequence,
                scientific_meaning="Core starts from the protein sequence itself, not from an execution wrapper.",
            ),
            ScientificExampleObservation(
                label="digested_peptides",
                value=", ".join(peptide_sequences),
                scientific_meaning="The resulting peptide list is a direct scientific output of the digestion rules.",
            ),
            ScientificExampleObservation(
                label="digest_policy_hash",
                value=policy_hash,
                scientific_meaning="The policy hash keeps cleavage assumptions reproducible across repeated scientific review.",
            ),
        ),
        caveats=(
            "This example demonstrates sequence semantics only and does not claim search, quantification, or runtime execution support.",
        ),
    )


def build_glycopeptide_refusal_example() -> CoreScientificExample:
    """Show honest refusal behavior when glyco-specific evidence is missing."""

    report = evaluate_glycopeptide_support_boundary(
        requested_workflow="glycopeptide_site_review",
        has_glycan_composition=False,
        has_glycosite_localization=True,
        has_oxonium_ion_support=False,
        treats_as_ordinary_modification=True,
    )
    return CoreScientificExample(
        example_id="core.glycopeptide-refusal",
        title="Unsupported glycopeptide walkthrough",
        scientific_question=(
            "What does core return when a workflow asks for glycopeptide interpretation "
            "without the evidence needed to preserve glyco semantics?"
        ),
        owner_surface="bijux_proteomics.ptm.review",
        observations=(
            ScientificExampleObservation(
                label="disposition",
                value=report.disposition.value,
                scientific_meaning="Core refuses the workflow instead of flattening glycopeptides into ordinary modifications.",
            ),
            ScientificExampleObservation(
                label="missing_evidence",
                value=", ".join(report.missing_evidence_fields),
                scientific_meaning="The refusal points to the exact glyco-specific evidence fields that are missing.",
            ),
            ScientificExampleObservation(
                label="reason",
                value=report.reason,
                scientific_meaning="The refusal reason is precise enough for a scientist to decide what evidence must be added next.",
            ),
        ),
        caveats=report.notes,
    )


def build_loss_aware_search_normalization_example() -> CoreScientificExample:
    """Show mapped, preserved, unsupported, and lost fields for normalized search data."""

    mapping = SearchResultColumnMapping(
        spectrum_id="scan_id",
        peptide="stripped_peptide",
        charge="precursor_charge",
        score="score_discriminant",
        protein_refs="protein_group",
        q_value="qvalue",
        decoy_label="decoy_flag",
        protein_separator=";",
    )
    manifest = SearchAdapterManifest(
        adapter_kind=SearchAdapterKind.SAGE,
        display_name="Sage example",
        description="Example normalization manifest for package-level field accounting.",
        score_orientation=ScoreOrientation.HIGHER_BETTER,
        result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
        native_columns=(
            "scan_id",
            "stripped_peptide",
            "precursor_charge",
            "score_discriminant",
            "protein_group",
            "decoy_flag",
            "qvalue",
            "analysis_batch",
            "missing_runtime_tag",
        ),
        mapping=mapping,
        default_decoy_policy=TargetDecoyLabelPolicy(
            protein_prefix="DECOY_",
            explicit_decoy_values=("decoy", "1"),
            explicit_target_values=("target", "0"),
        ),
        supports_q_value=True,
        supports_explicit_decoy_label=True,
        supports_protein_refs=True,
    )
    policy = SearchResultFamilyPolicy(
        result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
        requires_target_decoy_evidence=True,
        requires_protein_references=True,
        allows_library_style_scores=False,
        note="database target-decoy normalization expects explicit decoy evidence",
    )
    parse_report = PsmParseReport(
        total_rows=1,
        accepted_records=(
            PsmRecord(
                spectrum_id="scan-1",
                peptide="PEPTIDEK",
                canonical_peptide="PEPTIDEK",
                charge=2,
                score=42.0,
                q_value=0.01,
                protein_refs=("P11111",),
                target_decoy_label=TargetDecoyLabel.TARGET,
            ),
        ),
        rejected_rows=(),
        column_mapping=mapping,
    )
    normalization_report = SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        family_policy=policy,
        source_columns=(
            "scan_id",
            "stripped_peptide",
            "precursor_charge",
            "score_discriminant",
            "protein_group",
            "decoy_flag",
            "qvalue",
            "analysis_batch",
            "novel_metric",
        ),
        parse_report=parse_report,
        normalized_records=parse_report.accepted_records,
        evidence_rows=(),
    )
    accounting = build_search_adapter_field_accounting(normalization_report)
    return CoreScientificExample(
        example_id="core.loss-aware-search-normalization",
        title="Loss-aware search normalization walkthrough",
        scientific_question=(
            "Which fields survive normalization, which stay preserved but unmapped, "
            "and which are lost or unsupported when a search-engine export enters core?"
        ),
        owner_surface="bijux_proteomics.identification.search_adapters",
        observations=(
            ScientificExampleObservation(
                label="mapped_columns",
                value=", ".join(accounting.mapped_columns),
                scientific_meaning="These source columns land directly on the stable PSM contract.",
            ),
            ScientificExampleObservation(
                label="preserved_native_only_columns",
                value=", ".join(accounting.preserved_native_only_columns),
                scientific_meaning="These native columns are kept visible even though they are not first-class normalized fields.",
            ),
            ScientificExampleObservation(
                label="unsupported_columns",
                value=", ".join(accounting.unsupported_columns),
                scientific_meaning="These columns arrive from the engine but stay explicitly unsupported instead of being silently guessed at.",
            ),
            ScientificExampleObservation(
                label="lost_columns",
                value=", ".join(accounting.lost_columns),
                scientific_meaning="These expected native fields are absent, so normalization reports the loss instead of pretending full coverage.",
            ),
        ),
        caveats=(
            "This example focuses on field accounting and does not claim complete engine-specific parameter or calibration coverage.",
        ),
    )


__all__ = [
    "CoreScientificExample",
    "ScientificExampleObservation",
    "build_glycopeptide_refusal_example",
    "build_loss_aware_search_normalization_example",
    "build_sequence_digest_example",
]
