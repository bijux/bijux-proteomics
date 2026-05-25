# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable charter for the core scientific package boundary."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import re

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class CoreScientificDomainFamily(StrEnum):
    """Durable domain families that core is allowed to own."""

    PROGRAM_GOVERNANCE = "program_governance"
    SEQUENCE_AND_CHEMISTRY = "sequence_and_chemistry"
    INGESTION_AND_IDENTIFICATION = "ingestion_and_identification"
    QUANTIFICATION_AND_STUDY = "quantification_and_study"
    PTM_AND_DIA = "ptm_and_dia"
    REVIEW_AND_HANDOFF = "review_and_handoff"
    WORKFLOW_CONTRACTS = "workflow_contracts"
    PACKAGE_SURFACE = "package_surface"


class CoreModuleClassification(StrEnum):
    """Allowed audit outcomes for core source modules."""

    SUBSTANTIVE_SCIENTIFIC_SURFACE = "substantive_scientific_surface"
    THIN_ABSTRACTION = "thin_abstraction"
    COMPATIBILITY_EXPORT = "compatibility_export"
    BOUNDARY_GOVERNANCE = "boundary_governance"
    WRONG_PACKAGE_LOGIC = "wrong_package_logic"


class CoreProductCharter(JsonModel):
    """Durable scientific charter for core ownership."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    value_statement: str = Field(..., min_length=1)
    domain_families: tuple[CoreScientificDomainFamily, ...] = Field(
        default_factory=tuple
    )
    required_inputs: tuple[str, ...] = Field(default_factory=tuple)
    excluded_ownership: tuple[str, ...] = Field(default_factory=tuple)


class CoreDomainFamilyEntry(JsonModel):
    """One durable family of scientific ownership inside core."""

    model_config = ConfigDict(extra="forbid")

    family: CoreScientificDomainFamily
    owned_surface: str = Field(..., min_length=1)
    required_modules: tuple[str, ...] = Field(..., min_length=1)
    release_blocker: str = Field(..., min_length=1)


class CoreModuleAuditEntry(JsonModel):
    """Audit record for one core source module."""

    model_config = ConfigDict(extra="forbid")

    module_path: str = Field(..., min_length=1)
    family: CoreScientificDomainFamily
    classification: CoreModuleClassification
    reason: str = Field(..., min_length=1)


DEFAULT_CORE_CHARTER = CoreProductCharter(
    package_name="bijux-proteomics-core",
    value_statement=(
        "provide the scientific heart of the suite through proteomics domain models, "
        "evidence normalization, uncertainty-aware review artifacts, and workflow "
        "contracts without taking over runtime execution, reference curation, "
        "analytical judgment, or lab operations"
    ),
    domain_families=(
        CoreScientificDomainFamily.PROGRAM_GOVERNANCE,
        CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY,
        CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION,
        CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY,
        CoreScientificDomainFamily.PTM_AND_DIA,
        CoreScientificDomainFamily.REVIEW_AND_HANDOFF,
        CoreScientificDomainFamily.WORKFLOW_CONTRACTS,
        CoreScientificDomainFamily.PACKAGE_SURFACE,
    ),
    required_inputs=(
        "foundation-owned document, hashing, refusal, and provenance primitives",
        "runtime-owned execution backends only through explicit adapters",
    ),
    excluded_ownership=(
        "runtime provider binding and run orchestration",
        "knowledge reference curation and ontology registries",
        "intelligence ranking and recommendation judgment",
        "lab scheduling, protocol control, and operational readiness authority",
    ),
)


DEFAULT_CORE_DOMAIN_ENTRIES: tuple[CoreDomainFamilyEntry, ...] = (
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PROGRAM_GOVERNANCE,
        owned_surface="Program, target, canonical scientific record, review-gate, and validation semantics that define durable scientific state and progression meaning.",
        required_modules=(
            "domain/program_spec.py",
            "domain/programs.py",
            "domain/records.py",
            "domain/targets.py",
            "domain/validation.py",
        ),
        release_blocker="Core cannot ship if lifecycle and program-state semantics fragment into wrapper-only convenience surfaces or downstream reinterpretation.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY,
        owned_surface="Sequence parsing, digestion, amino-acid mass calculation, peptide chemistry, isotope labeling, and modification semantics for proteomics evidence preparation.",
        required_modules=(
            "sequences/core.py",
            "sequences/protein_identity_resolution.py",
            "sequences/digestion.py",
            "sequences/protein_region_context.py",
            "sequences/proteogenomic_peptide_support.py",
            "sequences/peptide_chemical_liability.py",
            "sequences/peptide_detectability.py",
            "sequences/peptide_uniqueness_index.py",
            "sequences/protein_index.py",
            "sequences/theoretical_digest.py",
            "chemistry/amino_acid_mass.py",
            "chemistry/contracts.py",
            "chemistry/isotope_envelope.py",
            "chemistry/modification_registry.py",
            "chemistry/modified_peptide_parser.py",
        ),
        release_blocker="Core cannot ship if sequence and peptide semantics collapse into format glue or tool-specific heuristics.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION,
        owned_surface="Format ingestion, spectrum parsing, search normalization, target-decoy handling, and protein-inference-ready evidence contracts.",
        required_modules=(
            "tabular.py",
            "scientific_tables.py",
            "io/format_validation.py",
            "io/formats.py",
            "io/deisotoping.py",
            "io/ingestion.py",
            "io/mgf_streaming.py",
            "io/mzml_reader.py",
            "io/noise.py",
            "io/run_qc.py",
            "io/spectrum_entropy.py",
            "io/spectrum_peak_matching.py",
            "io/spectra.py",
            "io/spectral_library.py",
            "io/spectral_library_intensity_agreement.py",
            "io/stable_outputs.py",
            "io/target_panel.py",
            "io/transition_table.py",
            "io/chimeric_spectrum.py",
            "io/chromatographic_evidence.py",
            "io/chromatographic_peak_picking.py",
            "io/dia_fragment_coelution.py",
            "io/fragment_ratio_stability.py",
            "io/precursor_isotope_fit.py",
            "io/precursor_validation.py",
            "io/raw_signal_evidence_cards.py",
            "io/retention_time_alignment.py",
            "io/xic_extraction.py",
            "identification/contracts.py",
            "identification/contaminant_evidence.py",
            "identification/diann_import.py",
            "identification/error_rate_annotation.py",
            "identification/cross_run_reproducibility.py",
            "identification/picked_protein_fdr.py",
            "identification/peptide_evidence.py",
            "identification/peptide_target_decoy_fdr.py",
            "identification/psm_features.py",
            "identification/psm_rescoring.py",
            "identification/protein_target_decoy_fdr.py",
            "identification/psm_target_decoy_fdr.py",
            "identification/fragpipe_import.py",
            "identification/comet_import.py",
            "identification/generic_psm_mapper.py",
            "identification/maxquant_import.py",
            "identification/openms_import.py",
            "identification/protein_coverage.py",
            "identification/protein_evidence.py",
            "identification/protein_parsimony.py",
            "identification/protein_grouping.py",
            "identification/sage_import.py",
            "identification/rejected_evidence_table.py",
            "identification/score_separation_diagnostic.py",
            "identification/spectronaut_import.py",
            "identification/search_adapters.py",
        ),
        release_blocker="Core cannot ship if external-engine normalization loses explicit support, loss, and refusal boundaries.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY,
        owned_surface="Study design, MS1 feature parsing, quantification rollup, normalization, and QC semantics for reproducible quantitative analysis.",
        required_modules=(
            "study/contrasts.py",
            "study/contracts.py",
            "study/carryover.py",
            "study/lc_drift.py",
            "study/design_diagnostics.py",
            "study/design_classification.py",
            "study/design_validity.py",
            "study/experiment_confidence.py",
            "study/experiment_feasibility.py",
            "study/experiment_design.py",
            "study/lab_protocol_context.py",
            "study/protocol_consistency.py",
            "study/replicate_structure.py",
            "study/sample_sheet_repairs.py",
            "study/sample_run_identity.py",
            "study/sample_metadata.py",
            "study/laboratory_plans.py",
            "study/laboratory_operations.py",
            "study/qc.py",
            "lab/actions.py",
            "lab/background.py",
            "lab/cohort.py",
            "lab/contamination.py",
            "lab/digestion_diagnosis.py",
            "lab/run_diagnosis.py",
            "lab/sample_identity.py",
            "lab/standards.py",
            "quantification/core_matrix.py",
            "quantification/contracts.py",
            "quantification/batch_effect.py",
            "quantification/censored_differential.py",
            "quantification/composition.py",
            "quantification/design_matrix.py",
            "quantification/differential_abundance.py",
            "quantification/differential_imputation_dependence.py",
            "quantification/differential_result_robustness.py",
            "quantification/heatmap_preparation.py",
            "quantification/imputation.py",
            "quantification/method_agreement.py",
            "quantification/model_rollup.py",
            "quantification/missingness.py",
            "quantification/multi_contrast_consistency.py",
            "quantification/normalization.py",
            "quantification/peptide_level_differential.py",
            "quantification/peptide_intensity_matrix.py",
            "quantification/peptide_profile_inconsistency.py",
            "quantification/power_estimation.py",
            "quantification/protein_intensity_matrix.py",
            "quantification/protein_lfq.py",
            "quantification/sample_exploration.py",
            "quantification/time_course_differential.py",
            "quantification/uncertainty.py",
            "quantification/variance_model.py",
            "quantification/value_provenance.py",
        ),
        release_blocker="Core cannot ship if quantitative outputs stop carrying design and QC meaning that downstream packages depend on.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PTM_AND_DIA,
        owned_surface="PTM localization, occupancy, motif-enrichment background semantics, protein-abundance-corrected site differential semantics, and DIA-native evidence surfaces that preserve uncertainty, library identity, and targeted follow-up meaning.",
        required_modules=(
            "targeted/assay_interference.py",
            "targeted/assay_qc.py",
            "targeted/biomarker_stability.py",
            "targeted/carryover.py",
            "targeted/discovery_peptide_selection.py",
            "targeted/fragment_ratios.py",
            "targeted/panel_design.py",
            "targeted/panel_redundancy.py",
            "targeted/result_validation.py",
            "targeted/validation_planning.py",
            "targeted/validation_evidence_cards.py",
            "targeted/transition_coelution.py",
            "targeted/transition_selection.py",
            "ptm/contracts.py",
            "ptm/ambiguity_handling.py",
            "ptm/abundance_correction.py",
            "ptm/acetylation.py",
            "ptm/context_annotation.py",
            "ptm/crosstalk.py",
            "ptm/evidence_cards.py",
            "ptm/fragment_scoring.py",
            "ptm/hotspots.py",
            "ptm/kinase_inference.py",
            "ptm/localization_risk.py",
            "ptm/localization_scoring.py",
            "ptm/mechanism_classification.py",
            "ptm/motif_analysis.py",
            "ptm/oxidation.py",
            "ptm/ortholog_site_conservation.py",
            "ptm/occupancy_estimation.py",
            "ptm/phosphatase_inference.py",
            "ptm/differential_analysis.py",
            "ptm/peptide_parser.py",
            "ptm/protein_site_mapping.py",
            "ptm/regulator_enrichment.py",
            "ptm/review.py",
            "ptm/site_annotation_import.py",
            "ptm/site_groups.py",
            "ptm/site_quantification.py",
            "proteoforms/assembly.py",
            "proteoforms/quantification.py",
            "dia/contracts.py",
            "dia/library_coverage.py",
            "dia/precursor_matrix.py",
            "dia/protein_matrix.py",
            "dia/run_qc.py",
            "dia/transition_qc.py",
            "targeted/result_import.py",
            "targeted/target_matrix.py",
        ),
        release_blocker="Core cannot ship if PTM or DIA workflows flatten ambiguity into generic evidence records.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.REVIEW_AND_HANDOFF,
        owned_surface="Typed proteomics evidence graphs, evidence-chain reconstruction, review packets, contradiction-aware evidence summaries, collaboration bundles, and core-owned handoff-ready scientific artifacts.",
        required_modules=(
            "review/biomarker_candidate_ranking.py",
            "review/evidence_graph.py",
            "review/evidence_aware_ranking.py",
            "review/biological_claim_validation.py",
            "review/biological_hypotheses.py",
            "review/evidence_graph_confidence.py",
            "review/evidence_graph_downgrades.py",
            "review/evidence_graph_export.py",
            "review/evidence_graph_run_diff.py",
            "review/evidence_graph_queries.py",
            "review/result_explanations.py",
            "review/result_queries.py",
            "review/belief_audit.py",
            "review/evidence_graph_contradictions.py",
            "review/evidence_chain_reconstruction.py",
            "review/contracts.py",
            "review/protein_family_graphs.py",
            "review/analysis_recommendations.py",
            "review/compact_result_summary.py",
            "review/failure_explanations.py",
            "review/collaboration.py",
            "review/structure_reports/render.py",
            "interpretation/biological_context_mapping.py",
            "interpretation/compartment_biology.py",
            "interpretation/complex_activity.py",
            "interpretation/drug_target_interpretation.py",
            "interpretation/disease_phenotype_interpretation.py",
            "interpretation/foreground_background_model.py",
            "interpretation/pathway_activity.py",
            "interpretation/protein_set_enrichment.py",
            "interpretation/protein_set_scoring.py",
            "interpretation/ppi_network_modules.py",
            "interpretation/regulator_inference.py",
            "interpretation/tissue_cell_type_context.py",
            "panels/target_panel.py",
        ),
        release_blocker="Core cannot ship if review-facing scientific artifacts become presentation-only shells without underlying evidence structure.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.WORKFLOW_CONTRACTS,
        owned_surface="Runtime-agnostic workflow blueprints, execution requests, and replayable scientific workflow contracts.",
        required_modules=(
            "workflow/blueprint.py",
            "workflow/biological_reporting.py",
            "workflow/biological_result_graph.py",
            "workflow/cohort_stratification.py",
            "workflow/cross_study_effect_comparison.py",
            "workflow/cross_study_evidence_cards.py",
            "workflow/cross_study_meta_analysis.py",
            "workflow/cross_study_pathway_comparison.py",
            "workflow/cross_study_protein_harmonization.py",
            "workflow/cross_species_effect_comparison.py",
            "workflow/dia_differential_analysis.py",
            "workflow/dia_dda_comparison.py",
            "workflow/interactive_result_comparison.py",
            "workflow/interactive_result_bundle.py",
            "workflow/orchestrator.py",
            "workflow/protein_evidence_cards.py",
            "workflow/protein_mechanism_cards.py",
            "workflow/public_benchmark_descriptors.py",
            "workflow/public_benchmark_runner.py",
            "workflow/public_dataset_comparison.py",
            "workflow/result_manifest.py",
            "workflow/result_search_index.py",
            "workflow/study_result.py",
            "workflow/trust_bundle.py",
            "interfaces/execution/backend.py",
            "interfaces/execution/runner.py",
            "interfaces/execution/runtime_adapter.py",
            "interfaces/runtime_plans.py",
        ),
        release_blocker="Core cannot ship if workflow contracts require runtime internals instead of scientific inputs and explicit adapters.",
    ),
    CoreDomainFamilyEntry(
        family=CoreScientificDomainFamily.PACKAGE_SURFACE,
        owned_surface="Package-level CLI, example surfaces, and adoption contracts that explain and expose core ownership without becoming a shadow runtime.",
        required_modules=(
            "__init__.py",
            "programs.py",
            "interfaces/examples.py",
            "interfaces/cli/app.py",
            "governance/charter.py",
            "benchmarks/adoption.py",
            "benchmarks/scientific_fixture_corpus.py",
        ),
        release_blocker="Core cannot ship if its public package surface describes the wrong owner story or hides the scientific boundary behind stale compatibility language.",
    ),
)


_COMPATIBILITY_IMPORT_RE = re.compile(
    r"^from\s+(bijux_proteomics(?:\.[a-z0-9_]+)+)\s+import\s+\*(?:\s+#.*)?$",
    flags=re.MULTILINE,
)


def _core_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_module_path(module_name: str) -> str:
    relative = module_name.removeprefix("bijux_proteomics.").replace(".", "/")
    source_root = _core_source_root()
    candidate = source_root / f"{relative}.py"
    if candidate.exists():
        return f"{relative}.py"
    package_init = source_root / relative / "__init__.py"
    if package_init.exists():
        return f"{relative}/__init__.py"
    raise ValueError(f"unable to resolve compatibility target for {module_name}")


def _compatibility_target(module_path: str) -> str | None:
    content = (_core_source_root() / module_path).read_text(encoding="utf-8")
    match = _COMPATIBILITY_IMPORT_RE.search(content)
    if match is None:
        return None
    return _resolve_module_path(match.group(1))


def _module_family(module_path: str) -> CoreScientificDomainFamily:
    compatibility_target = _compatibility_target(module_path)
    if compatibility_target is not None:
        return _module_family(compatibility_target)

    if module_path.startswith(
        ("workflow/", "interfaces/execution/")
    ) or module_path in {"interfaces/runtime_plans.py"}:
        return CoreScientificDomainFamily.WORKFLOW_CONTRACTS
    if module_path == "programs.py":
        return CoreScientificDomainFamily.PACKAGE_SURFACE
    if module_path == "__init__.py" or module_path.startswith(
        ("governance/", "interfaces/", "benchmarks/")
    ):
        return CoreScientificDomainFamily.PACKAGE_SURFACE
    if module_path.startswith("domain/"):
        return CoreScientificDomainFamily.PROGRAM_GOVERNANCE
    if module_path.startswith(("sequences/", "chemistry/")) or module_path in {
        "peptide_uniqueness_audit.py",
        "protease_digest_comparison.py",
    }:
        return CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY
    if module_path in {"tabular.py", "scientific_tables.py"} or module_path.startswith(("io/", "identification/")):
        return CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION
    if module_path.startswith(
        (
            "quantification/",
            "study/",
            "lab/",
            "multiplex/",
            "isotope_labeling/",
            "targeted/",
        )
    ):
        return CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY
    if module_path.startswith(("ptm/", "dia/", "proteoforms/")):
        return CoreScientificDomainFamily.PTM_AND_DIA
    if module_path.startswith(
        (
            "review/",
            "biology/",
            "interpretation/",
            "panels/",
        )
    ):
        return CoreScientificDomainFamily.REVIEW_AND_HANDOFF
    raise ValueError(f"unclassified core module path: {module_path}")


def _module_classification(module_path: str) -> CoreModuleClassification:
    if module_path == "governance/charter.py":
        return CoreModuleClassification.BOUNDARY_GOVERNANCE
    if module_path == "__init__.py" or module_path.endswith("/__init__.py"):
        return CoreModuleClassification.THIN_ABSTRACTION
    if _compatibility_target(module_path) is not None:
        return CoreModuleClassification.COMPATIBILITY_EXPORT
    return CoreModuleClassification.SUBSTANTIVE_SCIENTIFIC_SURFACE


def _module_reason(
    module_path: str,
    family: CoreScientificDomainFamily,
    classification: CoreModuleClassification,
) -> str:
    if classification is CoreModuleClassification.BOUNDARY_GOVERNANCE:
        return (
            "The machine-readable charter keeps core scientific ownership explicit, "
            "auditable, and release-blocking."
        )
    if classification is CoreModuleClassification.THIN_ABSTRACTION:
        return (
            "Namespace initializers and the package root aggregate stable exports "
            "without becoming separate scientific owners."
        )
    if classification is CoreModuleClassification.COMPATIBILITY_EXPORT:
        target = _compatibility_target(module_path)
        if target is None:
            raise ValueError(f"missing compatibility target for {module_path}")
        return (
            f"This module is a compatibility export over {target} and must stay a thin "
            "alias rather than growing new scientific logic."
        )
    return {
        CoreScientificDomainFamily.PROGRAM_GOVERNANCE: (
            "This module owns scientific program-state semantics that downstream packages consume."
        ),
        CoreScientificDomainFamily.SEQUENCE_AND_CHEMISTRY: (
            "This module owns sequence and peptide semantics that must stay scientifically precise."
        ),
        CoreScientificDomainFamily.INGESTION_AND_IDENTIFICATION: (
            "This module owns evidence ingestion, support boundaries, or identification semantics."
        ),
        CoreScientificDomainFamily.QUANTIFICATION_AND_STUDY: (
            "This module owns quantitative analysis or study-design meaning instead of workflow transport."
        ),
        CoreScientificDomainFamily.PTM_AND_DIA: (
            "This module owns uncertainty-aware PTM or DIA evidence semantics."
        ),
        CoreScientificDomainFamily.REVIEW_AND_HANDOFF: (
            "This module owns reviewable scientific artifacts and evidence-aware handoff context."
        ),
        CoreScientificDomainFamily.WORKFLOW_CONTRACTS: (
            "This module owns runtime-agnostic scientific workflow contracts or explicit execution adapters."
        ),
        CoreScientificDomainFamily.PACKAGE_SURFACE: (
            "This module owns a package-facing surface that explains or exposes core without taking over runtime authority."
        ),
    }[family]


def _build_module_audit() -> tuple[CoreModuleAuditEntry, ...]:
    source_root = _core_source_root()
    entries: list[CoreModuleAuditEntry] = []
    for path in sorted(source_root.rglob("*.py")):
        module_path = path.relative_to(source_root).as_posix()
        family = _module_family(module_path)
        classification = _module_classification(module_path)
        entries.append(
            CoreModuleAuditEntry(
                module_path=module_path,
                family=family,
                classification=classification,
                reason=_module_reason(module_path, family, classification),
            )
        )
    return tuple(entries)


DEFAULT_CORE_MODULE_AUDIT = _build_module_audit()


def list_core_domain_families() -> tuple[CoreScientificDomainFamily, ...]:
    """Return the exact scientific domain families core is allowed to own."""

    return DEFAULT_CORE_CHARTER.domain_families


def list_core_domain_entries() -> tuple[CoreDomainFamilyEntry, ...]:
    """Return the exact domain-family entries core must satisfy."""

    return DEFAULT_CORE_DOMAIN_ENTRIES


__all__ = [
    "CoreDomainFamilyEntry",
    "CoreModuleAuditEntry",
    "CoreModuleClassification",
    "CoreProductCharter",
    "CoreScientificDomainFamily",
    "DEFAULT_CORE_CHARTER",
    "DEFAULT_CORE_DOMAIN_ENTRIES",
    "DEFAULT_CORE_MODULE_AUDIT",
    "list_core_domain_entries",
    "list_core_domain_families",
]
