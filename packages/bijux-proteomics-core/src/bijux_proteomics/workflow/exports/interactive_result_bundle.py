# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Frontend-ready interactive result bundles over governed report artifacts."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm.reporting import PtmReportExportManifest
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportExportManifest,
)
from bijux_proteomics_foundation import JsonModel


class InteractiveResultSourceKind(StrEnum):
    """Stable source families that contribute to one UI bundle."""

    BIOLOGICAL_REPORT = "biological_report"
    PTM_REPORT = "ptm_report"
    RUN_QC_ASSESSMENT = "run_qc_assessment"


class InteractiveResultCardKind(StrEnum):
    """Stable card families surfaced to interactive clients."""

    PROTEIN_EVIDENCE = "protein_evidence"
    PROTEIN_MECHANISM = "protein_mechanism"
    PTM_EVIDENCE = "ptm_evidence"


class InteractiveResultQcKind(StrEnum):
    """Stable QC-ledger families surfaced to interactive clients."""

    EXPERIMENT_COMPONENT = "experiment_component"
    SECTION_CONFIDENCE = "section_confidence"
    RUN_QC_ASSESSMENT = "run_qc_assessment"


class InteractiveResultPlotKind(StrEnum):
    """Stable plot or matrix assets that a UI can render directly."""

    BIOLOGICAL_VOLCANO_TSV = "biological_volcano_tsv"
    BIOLOGICAL_VOLCANO_JSON = "biological_volcano_json"
    BIOLOGICAL_VOLCANO_SVG = "biological_volcano_svg"
    BIOLOGICAL_VOLCANO_HTML = "biological_volcano_html"
    BIOLOGICAL_HEATMAP_MATRIX = "biological_heatmap_matrix"
    BIOLOGICAL_HEATMAP_COLUMNS = "biological_heatmap_columns"
    BIOLOGICAL_HEATMAP_ROWS = "biological_heatmap_rows"
    BIOLOGICAL_SAMPLE_PCA = "biological_sample_pca"
    PTM_DIFFERENTIAL_VOLCANO = "ptm_differential_volcano"
    PTM_MOTIF_LOGO = "ptm_motif_logo"
    PTM_MOTIF_FREQUENCY = "ptm_motif_frequency"
    PTM_MOTIF_WINDOWS = "ptm_motif_windows"


class InteractiveResultSourceReport(JsonModel):
    """One governed report directory contributing surfaces to the UI bundle."""

    model_config = ConfigDict(extra="forbid")

    source_kind: InteractiveResultSourceKind
    report_dir: str = Field(..., min_length=1)
    manifest_json: str | None = None
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class InteractiveResultSample(JsonModel):
    """One sample surfaced for an interactive result client."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    batch: str | None = None
    replicate: str | None = None
    fraction: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    pc1: float | None = None
    pc2: float | None = None
    outlier: bool | None = None
    outlier_reasons: tuple[str, ...] = Field(default_factory=tuple)
    source_reports: tuple[InteractiveResultSourceKind, ...] = Field(default_factory=tuple)


class InteractiveResultProtein(JsonModel):
    """One protein-level result object for interactive clients."""

    model_config = ConfigDict(extra="forbid")

    object_id: str = Field(..., min_length=1)
    protein_group_id: str | None = None
    representative_protein_ref: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    gene_symbol: str | None = None
    condition_a: str | None = None
    condition_b: str | None = None
    log2_fold_change: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    significant: bool | None = None
    evidence_tier: str | None = None
    peptide_ids: tuple[str, ...] = Field(default_factory=tuple)
    pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    ptm_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_reports: tuple[InteractiveResultSourceKind, ...] = Field(default_factory=tuple)


class InteractiveResultPeptide(JsonModel):
    """One peptide observation or protein-linked peptide object."""

    model_config = ConfigDict(extra="forbid")

    peptide_id: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    sequence: str = Field(..., min_length=1)
    localized_peptide: str | None = None
    canonical_peptide: str | None = None
    sample_id: str | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    modification_names: tuple[str, ...] = Field(default_factory=tuple)
    site_keys: tuple[str, ...] = Field(default_factory=tuple)
    charge: int | None = Field(default=None, ge=1)
    score: float | None = None
    q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    source_reports: tuple[InteractiveResultSourceKind, ...] = Field(default_factory=tuple)


class InteractiveResultPtmSite(JsonModel):
    """One PTM-site object for interactive clients."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(..., min_length=1)
    protein_ref: str = Field(..., min_length=1)
    residue: str | None = None
    position: int | None = Field(default=None, ge=1)
    modification_name: str | None = None
    localization_tier: str | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    log2_fold_change: float | None = None
    corrected_log2_fold_change: float | None = None
    protein_correction_status: str | None = None
    mechanism_class: str | None = None
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)


class InteractiveResultPathway(JsonModel):
    """One pathway object merged across enrichment and activity surfaces."""

    model_config = ConfigDict(extra="forbid")

    pathway_id: str = Field(..., min_length=1)
    pathway_name: str | None = None
    source_name: str | None = None
    source_accession: str | None = None
    condition_a: str | None = None
    condition_b: str | None = None
    comparison_confidence_status: str | None = None
    activity_score_delta: float | None = None
    enrichment_ratio: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    foreground_overlap_count: int | None = Field(default=None, ge=0)
    supporting_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_member_ids: tuple[str, ...] = Field(default_factory=tuple)


class InteractiveResultQcEntry(JsonModel):
    """One QC or confidence entry made explicit for interactive clients."""

    model_config = ConfigDict(extra="forbid")

    qc_id: str = Field(..., min_length=1)
    qc_kind: InteractiveResultQcKind
    scope: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    severity: str | None = None
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    message: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)


class InteractiveResultCard(JsonModel):
    """One card object linked back to evidence-rich result surfaces."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(..., min_length=1)
    card_kind: InteractiveResultCardKind
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    confidence_label: str | None = None
    evidence_tier: str | None = None
    warning_codes: tuple[str, ...] = Field(default_factory=tuple)
    linked_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    linked_site_keys: tuple[str, ...] = Field(default_factory=tuple)
    linked_pathway_ids: tuple[str, ...] = Field(default_factory=tuple)
    graph_node_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_surface: str = Field(..., min_length=1)


class InteractiveResultGraphNode(JsonModel):
    """One graph node carried into the interactive result bundle."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    entity_ref: str = Field(..., min_length=1)
    label: str | None = None
    claim_state: str | None = None
    trust_class: str | None = None
    contradiction_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_refs: tuple[str, ...] = Field(default_factory=tuple)


class InteractiveResultGraphEdge(JsonModel):
    """One graph edge carried into the interactive result bundle."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    source_row_ref: str | None = None
    confidence: str | None = None
    evidence_type: str | None = None
    reason: str | None = None
    support_count: int | None = Field(default=None, ge=0)


class InteractiveResultPlot(JsonModel):
    """One renderable plot or matrix asset surfaced to a frontend."""

    model_config = ConfigDict(extra="forbid")

    plot_kind: InteractiveResultPlotKind
    source_kind: InteractiveResultSourceKind
    relative_path: str = Field(..., min_length=1)
    media_type: str = Field(..., min_length=1)


class InteractiveResultBundleSummary(JsonModel):
    """Compact summary over one interactive result bundle."""

    model_config = ConfigDict(extra="forbid")

    biological_report_available: bool
    ptm_report_available: bool
    run_qc_input_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    ptm_site_count: int = Field(..., ge=0)
    pathway_count: int = Field(..., ge=0)
    qc_entry_count: int = Field(..., ge=0)
    card_count: int = Field(..., ge=0)
    graph_node_count: int = Field(..., ge=0)
    graph_edge_count: int = Field(..., ge=0)
    plot_count: int = Field(..., ge=0)


class InteractiveResultBundle(JsonModel):
    """One frontend-ready result bundle over governed exported report artifacts."""

    model_config = ConfigDict(extra="forbid")

    source_reports: tuple[InteractiveResultSourceReport, ...] = Field(default_factory=tuple)
    summary: InteractiveResultBundleSummary
    samples: tuple[InteractiveResultSample, ...] = Field(default_factory=tuple)
    proteins: tuple[InteractiveResultProtein, ...] = Field(default_factory=tuple)
    peptides: tuple[InteractiveResultPeptide, ...] = Field(default_factory=tuple)
    ptm_sites: tuple[InteractiveResultPtmSite, ...] = Field(default_factory=tuple)
    pathways: tuple[InteractiveResultPathway, ...] = Field(default_factory=tuple)
    qc_entries: tuple[InteractiveResultQcEntry, ...] = Field(default_factory=tuple)
    cards: tuple[InteractiveResultCard, ...] = Field(default_factory=tuple)
    graph_nodes: tuple[InteractiveResultGraphNode, ...] = Field(default_factory=tuple)
    graph_edges: tuple[InteractiveResultGraphEdge, ...] = Field(default_factory=tuple)
    plots: tuple[InteractiveResultPlot, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class _LoadedReportArtifacts(TypedDict):
    report_dir: Path
    artifact_paths: dict[str, str]
    source_report: InteractiveResultSourceReport


class _SampleEntry(TypedDict):
    sample_id: str
    condition: str | None
    batch: str | None
    replicate: str | None
    fraction: str | None
    instrument: str | None
    search_engine: str | None
    pc1: float | None
    pc2: float | None
    outlier: bool | None
    outlier_reasons: tuple[str, ...]
    source_reports: set[InteractiveResultSourceKind]


class _PathwayEntry(TypedDict):
    pathway_id: str
    pathway_name: str | None
    source_name: str | None
    source_accession: str | None
    condition_a: str | None
    condition_b: str | None
    comparison_confidence_status: str | None
    activity_score_delta: float | None
    enrichment_ratio: float | None
    adjusted_p_value: float | None
    foreground_overlap_count: int | None
    supporting_protein_refs: tuple[str, ...]
    unresolved_member_ids: tuple[str, ...]


_ManifestModel = (
    type[BiologicalResultReportExportManifest] | type[PtmReportExportManifest]
)


_BIOLOGICAL_FALLBACK_ARTIFACTS = {
    "summary_tsv": "biological_report_summary.tsv",
    "protein_card_tsv": "biological_protein_cards.tsv",
    "protein_mechanism_card_tsv": "biological_protein_mechanism_cards.tsv",
    "pathway_entry_tsv": "biological_pathway_entries.tsv",
    "pathway_activity_condition_comparison_tsv": (
        "biological_pathway_activity_condition_comparisons.tsv"
    ),
    "pathway_activity_member_contribution_tsv": (
        "biological_pathway_activity_members.tsv"
    ),
    "pathway_activity_unresolved_member_tsv": (
        "biological_pathway_activity_unresolved.tsv"
    ),
    "experiment_confidence_components_tsv": (
        "biological_experiment_confidence_components.tsv"
    ),
    "section_confidence_tsv": "biological_report_section_confidence.tsv",
    "evidence_graph_nodes_tsv": "biological_evidence_graph_nodes.tsv",
    "evidence_graph_edges_tsv": "biological_evidence_graph_edges.tsv",
    "heatmap_column_metadata_tsv": "biological_heatmap_columns.tsv",
    "sample_pca_scores_tsv": "biological_sample_pca_scores.tsv",
    "volcano_tsv": "biological_volcano.tsv",
    "volcano_json": "biological_volcano.json",
    "volcano_svg": "biological_volcano.svg",
    "volcano_html": "biological_volcano.html",
    "heatmap_matrix_tsv": "biological_heatmap_matrix.tsv",
    "heatmap_row_metadata_tsv": "biological_heatmap_rows.tsv",
}

_PTM_FALLBACK_ARTIFACTS = {
    "summary_tsv": "ptm_report_summary.tsv",
    "peptide_tsv": "ptm_peptides.tsv",
    "site_tsv": "ptm_sites.tsv",
    "site_quant_matrix_tsv": "ptm_site_quant_matrix.tsv",
    "differential_tsv": "ptm_differential.tsv",
    "differential_volcano_tsv": "ptm_differential_volcano.tsv",
    "evidence_card_tsv": "ptm_evidence_cards.tsv",
    "motif_window_tsv": "ptm_motif_windows.tsv",
    "motif_frequency_tsv": "ptm_motif_frequency.tsv",
    "motif_logo_tsv": "ptm_motif_logo.tsv",
}


def build_interactive_result_bundle_from_artifacts(
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
) -> InteractiveResultBundle:
    """Build one frontend-ready result bundle from governed report directories."""

    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and not run_qc_assessment_tsv_paths
    ):
        raise ValueError(
            "interactive result bundle requires at least one biological report, PTM report, or QC assessment input"
        )
    biological_artifacts = _load_report_artifacts(
        report_dir=biological_report_dir,
        source_kind=InteractiveResultSourceKind.BIOLOGICAL_REPORT,
        manifest_filename="biological_report_manifest.json",
        manifest_model=BiologicalResultReportExportManifest,
        fallback_artifacts=_BIOLOGICAL_FALLBACK_ARTIFACTS,
    )
    ptm_artifacts = _load_report_artifacts(
        report_dir=ptm_report_dir,
        source_kind=InteractiveResultSourceKind.PTM_REPORT,
        manifest_filename="ptm_report_manifest.json",
        manifest_model=PtmReportExportManifest,
        fallback_artifacts=_PTM_FALLBACK_ARTIFACTS,
    )
    samples = _build_samples(
        biological_artifacts=biological_artifacts,
        ptm_artifacts=ptm_artifacts,
    )
    proteins = _build_proteins(
        biological_artifacts=biological_artifacts,
        ptm_artifacts=ptm_artifacts,
    )
    peptides = _build_peptides(
        biological_artifacts=biological_artifacts,
        ptm_artifacts=ptm_artifacts,
    )
    ptm_sites = _build_ptm_sites(ptm_artifacts=ptm_artifacts)
    pathways = _build_pathways(biological_artifacts=biological_artifacts)
    qc_entries = _build_qc_entries(
        biological_artifacts=biological_artifacts,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    cards = _build_cards(
        biological_artifacts=biological_artifacts,
        ptm_artifacts=ptm_artifacts,
    )
    graph_nodes, graph_edges = _build_graph(biological_artifacts=biological_artifacts)
    plots = _build_plots(
        biological_artifacts=biological_artifacts,
        ptm_artifacts=ptm_artifacts,
    )
    source_reports = tuple(
        report
        for report in (
            None if biological_artifacts is None else biological_artifacts["source_report"],
            None if ptm_artifacts is None else ptm_artifacts["source_report"],
        )
        if report is not None
    )
    return InteractiveResultBundle(
        source_reports=source_reports,
        summary=InteractiveResultBundleSummary(
            biological_report_available=biological_artifacts is not None,
            ptm_report_available=ptm_artifacts is not None,
            run_qc_input_count=len(run_qc_assessment_tsv_paths),
            sample_count=len(samples),
            protein_count=len(proteins),
            peptide_count=len(peptides),
            ptm_site_count=len(ptm_sites),
            pathway_count=len(pathways),
            qc_entry_count=len(qc_entries),
            card_count=len(cards),
            graph_node_count=len(graph_nodes),
            graph_edge_count=len(graph_edges),
            plot_count=len(plots),
        ),
        samples=samples,
        proteins=proteins,
        peptides=peptides,
        ptm_sites=ptm_sites,
        pathways=pathways,
        qc_entries=qc_entries,
        cards=cards,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        plots=plots,
        note=(
            "interactive result bundle lifts governed report artifacts into one "
            "frontend-ready JSON surface so external clients do not need to parse TSV ledgers directly"
        ),
    )


def render_interactive_result_bundle_summary_tsv(bundle: InteractiveResultBundle) -> str:
    """Render a compact interactive result bundle summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("biological_report_available", str(bundle.summary.biological_report_available).lower()),
        ("ptm_report_available", str(bundle.summary.ptm_report_available).lower()),
        ("run_qc_input_count", bundle.summary.run_qc_input_count),
        ("sample_count", bundle.summary.sample_count),
        ("protein_count", bundle.summary.protein_count),
        ("peptide_count", bundle.summary.peptide_count),
        ("ptm_site_count", bundle.summary.ptm_site_count),
        ("pathway_count", bundle.summary.pathway_count),
        ("qc_entry_count", bundle.summary.qc_entry_count),
        ("card_count", bundle.summary.card_count),
        ("graph_node_count", bundle.summary.graph_node_count),
        ("graph_edge_count", bundle.summary.graph_edge_count),
        ("plot_count", bundle.summary.plot_count),
        ("note", bundle.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def _load_report_artifacts(
    *,
    report_dir: Path | None,
    source_kind: InteractiveResultSourceKind,
    manifest_filename: str,
    manifest_model: _ManifestModel,
    fallback_artifacts: dict[str, str],
) -> _LoadedReportArtifacts | None:
    if report_dir is None:
        return None
    artifact_paths: dict[str, str]
    manifest_json = None
    manifest_path = report_dir / manifest_filename
    if manifest_path.exists():
        manifest = manifest_model.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        artifact_paths = {
            key: value
            for key, value in manifest.artifacts.to_dict().items()
            if isinstance(value, str) and value
        }
        manifest_json = manifest_filename
    else:
        artifact_paths = {
            key: value for key, value in fallback_artifacts.items() if (report_dir / value).exists()
        }
    return {
        "report_dir": report_dir,
        "artifact_paths": artifact_paths,
        "source_report": InteractiveResultSourceReport(
            source_kind=source_kind,
            report_dir=str(report_dir),
            manifest_json=manifest_json,
            artifact_paths=artifact_paths,
        ),
    }


def _build_samples(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultSample, ...]:
    entries: dict[str, _SampleEntry] = {}
    if biological_artifacts is not None:
        report_dir = biological_artifacts["report_dir"]
        artifact_paths = biological_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "heatmap_column_metadata_tsv"):
            entry = entries.setdefault(
                row["sample_id"],
                {
                    "sample_id": row["sample_id"],
                    "condition": _empty_to_none(row.get("condition")),
                    "batch": _empty_to_none(row.get("batch")),
                    "replicate": _empty_to_none(row.get("replicate")),
                    "fraction": _empty_to_none(row.get("fraction")),
                    "instrument": _empty_to_none(row.get("instrument")),
                    "search_engine": _empty_to_none(row.get("search_engine")),
                    "pc1": None,
                    "pc2": None,
                    "outlier": None,
                    "outlier_reasons": (),
                    "source_reports": {InteractiveResultSourceKind.BIOLOGICAL_REPORT},
                },
            )
            entry["source_reports"].add(InteractiveResultSourceKind.BIOLOGICAL_REPORT)
        for row in _read_optional_rows(report_dir, artifact_paths, "sample_pca_scores_tsv"):
            entry = entries.setdefault(
                row["sample_id"],
                {
                    "sample_id": row["sample_id"],
                    "condition": _empty_to_none(row.get("condition")),
                    "batch": _empty_to_none(row.get("batch")),
                    "replicate": None,
                    "fraction": None,
                    "instrument": None,
                    "search_engine": None,
                    "pc1": None,
                    "pc2": None,
                    "outlier": None,
                    "outlier_reasons": (),
                    "source_reports": {InteractiveResultSourceKind.BIOLOGICAL_REPORT},
                },
            )
            entry["condition"] = entry["condition"] or _empty_to_none(row.get("condition"))
            entry["batch"] = entry["batch"] or _empty_to_none(row.get("batch"))
            entry["pc1"] = _parse_optional_float(row.get("pc1"))
            entry["pc2"] = _parse_optional_float(row.get("pc2"))
            entry["outlier"] = _parse_optional_bool(row.get("outlier"))
            entry["outlier_reasons"] = _split_multi(row.get("outlier_reasons", ""))
            entry["source_reports"].add(InteractiveResultSourceKind.BIOLOGICAL_REPORT)
    if ptm_artifacts is not None:
        report_dir = ptm_artifacts["report_dir"]
        artifact_paths = ptm_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "peptide_tsv"):
            sample_id = _empty_to_none(row.get("sample_id"))
            if sample_id is None:
                continue
            entry = entries.setdefault(
                sample_id,
                {
                    "sample_id": sample_id,
                    "condition": None,
                    "batch": None,
                    "replicate": None,
                    "fraction": None,
                    "instrument": None,
                    "search_engine": None,
                    "pc1": None,
                    "pc2": None,
                    "outlier": None,
                    "outlier_reasons": (),
                    "source_reports": {InteractiveResultSourceKind.PTM_REPORT},
                },
            )
            entry["source_reports"].add(InteractiveResultSourceKind.PTM_REPORT)
        for row in _read_optional_matrix_rows(report_dir, artifact_paths, "site_quant_matrix_tsv"):
            sample_id = row["sample_id"]
            entry = entries.setdefault(
                sample_id,
                {
                    "sample_id": sample_id,
                    "condition": None,
                    "batch": None,
                    "replicate": None,
                    "fraction": None,
                    "instrument": None,
                    "search_engine": None,
                    "pc1": None,
                    "pc2": None,
                    "outlier": None,
                    "outlier_reasons": (),
                    "source_reports": {InteractiveResultSourceKind.PTM_REPORT},
                },
            )
            entry["source_reports"].add(InteractiveResultSourceKind.PTM_REPORT)
    return tuple(
        InteractiveResultSample(
            sample_id=str(entry["sample_id"]),
            condition=_coerce_optional_str(entry["condition"]),
            batch=_coerce_optional_str(entry["batch"]),
            replicate=_coerce_optional_str(entry["replicate"]),
            fraction=_coerce_optional_str(entry["fraction"]),
            instrument=_coerce_optional_str(entry["instrument"]),
            search_engine=_coerce_optional_str(entry["search_engine"]),
            pc1=entry["pc1"],
            pc2=entry["pc2"],
            outlier=entry["outlier"],
            outlier_reasons=tuple(entry["outlier_reasons"]),
            source_reports=tuple(sorted(entry["source_reports"], key=lambda value: value.value)),
        )
        for entry in sorted(entries.values(), key=lambda item: str(item["sample_id"]))
    )


def _build_proteins(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultProtein, ...]:
    proteins: dict[str, InteractiveResultProtein] = {}
    if biological_artifacts is not None:
        report_dir = biological_artifacts["report_dir"]
        artifact_paths = biological_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "protein_card_tsv"):
            protein_group_id = row["protein_group_id"]
            representative = row["representative_protein_ref"]
            proteins[protein_group_id] = InteractiveResultProtein(
                object_id=f"protein:{protein_group_id}",
                protein_group_id=protein_group_id,
                representative_protein_ref=representative,
                protein_refs=_split_multi(row.get("protein_refs", "")),
                gene_symbol=_empty_to_none(row.get("gene_symbol")),
                condition_a=_empty_to_none(row.get("condition_a")),
                condition_b=_empty_to_none(row.get("condition_b")),
                log2_fold_change=_parse_optional_float(row.get("log2_fold_change")),
                adjusted_p_value=_parse_optional_float(row.get("adjusted_p_value")),
                significant=_parse_optional_bool(row.get("significant")),
                evidence_tier=_empty_to_none(row.get("evidence_tier")),
                peptide_ids=tuple(
                    f"protein-peptide:{protein_group_id}:{peptide}"
                    for peptide in _split_multi(row.get("peptides", ""))
                ),
                pathway_ids=_split_multi(row.get("pathway_ids", "")),
                ptm_site_keys=_split_multi(row.get("ptm_sites", "")),
                warning_codes=_split_multi(row.get("warning_codes", "")),
                graph_node_ids=tuple(
                    sorted(
                        {
                            row["graph_claim_node_id"],
                            row["graph_subject_node_id"],
                            *_split_multi(row.get("graph_support_node_ids", "")),
                        }
                    )
                ),
                source_reports=(InteractiveResultSourceKind.BIOLOGICAL_REPORT,),
            )
    if ptm_artifacts is not None:
        report_dir = ptm_artifacts["report_dir"]
        artifact_paths = ptm_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "evidence_card_tsv"):
            protein_ref = row["protein_ref"]
            existing = next(
                (
                    entry
                    for entry in proteins.values()
                    if entry.representative_protein_ref == protein_ref
                ),
                None,
            )
            if existing is not None:
                continue
            proteins[protein_ref] = InteractiveResultProtein(
                object_id=f"protein:{protein_ref}",
                protein_group_id=None,
                representative_protein_ref=protein_ref,
                protein_refs=(protein_ref,),
                gene_symbol=None,
                condition_a=_empty_to_none(row.get("condition_a")),
                condition_b=_empty_to_none(row.get("condition_b")),
                log2_fold_change=_parse_optional_float(row.get("log2_fold_change")),
                adjusted_p_value=_parse_optional_float(row.get("adjusted_p_value")),
                significant=None,
                evidence_tier=None,
                peptide_ids=(),
                pathway_ids=(),
                ptm_site_keys=(row["site_key"],),
                warning_codes=_split_multi(row.get("warning_codes", "")),
                graph_node_ids=(),
                source_reports=(InteractiveResultSourceKind.PTM_REPORT,),
            )
    return tuple(
        sorted(
            proteins.values(),
            key=lambda entry: (entry.representative_protein_ref, entry.object_id),
        )
    )


def _build_peptides(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultPeptide, ...]:
    peptides: list[InteractiveResultPeptide] = []
    if biological_artifacts is not None:
        report_dir = biological_artifacts["report_dir"]
        artifact_paths = biological_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "protein_card_tsv"):
            protein_group_id = row["protein_group_id"]
            protein_refs = _split_multi(row.get("protein_refs", ""))
            for peptide in _split_multi(row.get("peptides", "")):
                peptides.append(
                    InteractiveResultPeptide(
                        peptide_id=f"protein-peptide:{protein_group_id}:{peptide}",
                        source_surface="biological_protein_cards",
                        sequence=peptide,
                        localized_peptide=None,
                        canonical_peptide=peptide,
                        sample_id=None,
                        protein_refs=protein_refs,
                        modification_names=(),
                        site_keys=(),
                        charge=None,
                        score=None,
                        q_value=None,
                        source_reports=(InteractiveResultSourceKind.BIOLOGICAL_REPORT,),
                    )
                )
    if ptm_artifacts is not None:
        report_dir = ptm_artifacts["report_dir"]
        artifact_paths = ptm_artifacts["artifact_paths"]
        site_keys_by_peptide: dict[str, set[str]] = {}
        for artifact_key in ("site_tsv", "site_quant_matrix_tsv"):
            for row in _read_optional_rows(report_dir, artifact_paths, artifact_key):
                site_key = row["site_key"]
                for peptide in _split_multi(row.get("localized_peptides", "")):
                    site_keys_by_peptide.setdefault(peptide, set()).add(site_key)
        for row in _read_optional_rows(report_dir, artifact_paths, "peptide_tsv"):
            linked_site_keys = tuple(
                sorted(
                    site_keys_by_peptide.get(row["localized_peptide"], set())
                    | site_keys_by_peptide.get(row["canonical_peptide"], set())
                )
            )
            peptides.append(
                InteractiveResultPeptide(
                    peptide_id=f"ptm-peptide:{row['spectrum_id']}",
                    source_surface="ptm_peptides",
                    sequence=row["sequence"],
                    localized_peptide=_empty_to_none(row.get("localized_peptide")),
                    canonical_peptide=_empty_to_none(row.get("canonical_peptide")),
                    sample_id=_empty_to_none(row.get("sample_id")),
                    protein_refs=_split_multi(row.get("protein_refs", "")),
                    modification_names=_split_multi(row.get("modification_names", "")),
                    site_keys=linked_site_keys,
                    charge=_parse_optional_int(row.get("charge")),
                    score=_parse_optional_float(row.get("score")),
                    q_value=_parse_optional_float(row.get("q_value")),
                    source_reports=(InteractiveResultSourceKind.PTM_REPORT,),
                )
            )
    return tuple(
        sorted(
            peptides,
            key=lambda entry: (entry.sequence, entry.peptide_id),
        )
    )


def _build_ptm_sites(
    *,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultPtmSite, ...]:
    if ptm_artifacts is None:
        return ()
    report_dir = ptm_artifacts["report_dir"]
    artifact_paths = ptm_artifacts["artifact_paths"]
    sample_ids_by_site: dict[str, tuple[str, ...]] = {}
    for row in _read_optional_rows(report_dir, artifact_paths, "site_tsv"):
        sample_ids_by_site[row["site_key"]] = _split_multi(row.get("sample_ids", ""))
    entries: dict[str, InteractiveResultPtmSite] = {}
    for row in _read_optional_rows(report_dir, artifact_paths, "evidence_card_tsv"):
        entries[row["site_key"]] = InteractiveResultPtmSite(
            site_key=row["site_key"],
            protein_ref=row["protein_ref"],
            residue=_empty_to_none(row.get("residue")),
            position=_parse_optional_int(row.get("position")),
            modification_name=_empty_to_none(row.get("modification_name")),
            localization_tier=_empty_to_none(row.get("localization_tier")),
            adjusted_p_value=_parse_optional_float(row.get("adjusted_p_value")),
            log2_fold_change=_parse_optional_float(row.get("log2_fold_change")),
            corrected_log2_fold_change=_parse_optional_float(
                row.get("corrected_log2_fold_change")
            ),
            protein_correction_status=_empty_to_none(
                row.get("protein_correction_status")
            ),
            mechanism_class=_empty_to_none(row.get("mechanism_class")),
            warning_codes=_split_multi(row.get("warning_codes", "")),
            claim_ids=_split_multi(row.get("claim_ids", "")),
            sample_ids=sample_ids_by_site.get(row["site_key"], ()),
        )
    for row in _read_optional_rows(report_dir, artifact_paths, "site_tsv"):
        if row["site_key"] in entries:
            continue
        entries[row["site_key"]] = InteractiveResultPtmSite(
            site_key=row["site_key"],
            protein_ref=row["protein_ref"],
            residue=_empty_to_none(row.get("residue")),
            position=_parse_optional_int(row.get("position")),
            modification_name=_empty_to_none(row.get("modification_name")),
            localization_tier=None,
            adjusted_p_value=None,
            log2_fold_change=None,
            corrected_log2_fold_change=None,
            protein_correction_status=None,
            mechanism_class=None,
            warning_codes=(),
            claim_ids=(),
            sample_ids=_split_multi(row.get("sample_ids", "")),
        )
    return tuple(sorted(entries.values(), key=lambda entry: entry.site_key))


def _build_pathways(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultPathway, ...]:
    if biological_artifacts is None:
        return ()
    report_dir = biological_artifacts["report_dir"]
    artifact_paths = biological_artifacts["artifact_paths"]
    supporting_proteins: dict[str, set[str]] = {}
    for row in _read_optional_rows(
        report_dir,
        artifact_paths,
        "pathway_activity_member_contribution_tsv",
    ):
        supporting_proteins.setdefault(row["pathway_id"], set()).update(
            _split_multi(row.get("observed_protein_refs", ""))
        )
    unresolved_members: dict[str, set[str]] = {}
    for row in _read_optional_rows(
        report_dir,
        artifact_paths,
        "pathway_activity_unresolved_member_tsv",
    ):
        unresolved_members.setdefault(row["pathway_id"], set()).add(row["member_id"])
    entries: dict[str, _PathwayEntry] = {}
    for row in _read_optional_rows(
        report_dir,
        artifact_paths,
        "pathway_activity_condition_comparison_tsv",
    ):
        entries[row["pathway_id"]] = {
            "pathway_id": row["pathway_id"],
            "pathway_name": _empty_to_none(row.get("pathway_name")),
            "source_name": _empty_to_none(row.get("source_name")),
            "source_accession": _empty_to_none(row.get("source_accession")),
            "condition_a": _empty_to_none(row.get("condition_a")),
            "condition_b": _empty_to_none(row.get("condition_b")),
            "comparison_confidence_status": _empty_to_none(
                row.get("comparison_confidence_status")
            ),
            "activity_score_delta": _parse_optional_float(row.get("activity_score_delta")),
            "enrichment_ratio": None,
            "adjusted_p_value": None,
            "foreground_overlap_count": None,
            "supporting_protein_refs": tuple(
                sorted(supporting_proteins.get(row["pathway_id"], set()))
            ),
            "unresolved_member_ids": tuple(
                sorted(unresolved_members.get(row["pathway_id"], set()))
            ),
        }
    for row in _read_optional_rows(report_dir, artifact_paths, "pathway_entry_tsv"):
        entry = entries.setdefault(
            row["pathway_id"],
            {
                "pathway_id": row["pathway_id"],
                "pathway_name": _empty_to_none(row.get("pathway_name")),
                "source_name": _empty_to_none(row.get("source_name")),
                "source_accession": _empty_to_none(row.get("source_accession")),
                "condition_a": None,
                "condition_b": None,
                "comparison_confidence_status": None,
                "activity_score_delta": None,
                "enrichment_ratio": None,
                "adjusted_p_value": None,
                "foreground_overlap_count": None,
                "supporting_protein_refs": tuple(
                    sorted(supporting_proteins.get(row["pathway_id"], set()))
                ),
                "unresolved_member_ids": tuple(
                    sorted(unresolved_members.get(row["pathway_id"], set()))
                ),
            },
        )
        entry["enrichment_ratio"] = _parse_optional_float(row.get("enrichment_ratio"))
        entry["adjusted_p_value"] = _parse_optional_float(row.get("adjusted_p_value"))
        entry["foreground_overlap_count"] = _parse_optional_int(
            row.get("foreground_overlap_count")
        )
    return tuple(
        InteractiveResultPathway(**entry)
        for _, entry in sorted(entries.items())
    )


def _build_qc_entries(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> tuple[InteractiveResultQcEntry, ...]:
    entries: list[InteractiveResultQcEntry] = []
    if biological_artifacts is not None:
        report_dir = biological_artifacts["report_dir"]
        artifact_paths = biological_artifacts["artifact_paths"]
        for row in _read_optional_rows(
            report_dir,
            artifact_paths,
            "experiment_confidence_components_tsv",
        ):
            component = row.get("component", "")
            entries.append(
                InteractiveResultQcEntry(
                    qc_id=f"experiment_component:{component}",
                    qc_kind=InteractiveResultQcKind.EXPERIMENT_COMPONENT,
                    scope="report",
                    entity_id=component,
                    status=row.get("tier", ""),
                    severity=row.get("tier", ""),
                    reason_codes=_split_multi(row.get("reason_codes", "")),
                    message=row.get("message", ""),
                    source_surface="biological_experiment_confidence_components",
                )
            )
        for row in _read_optional_rows(
            report_dir,
            artifact_paths,
            "section_confidence_tsv",
        ):
            entries.append(
                InteractiveResultQcEntry(
                    qc_id=f"section_confidence:{row['section_key']}",
                    qc_kind=InteractiveResultQcKind.SECTION_CONFIDENCE,
                    scope="section",
                    entity_id=row["section_key"],
                    status=row["confidence_label"],
                    severity=row["confidence_label"],
                    reason_codes=(),
                    message=row["rationale"],
                    source_surface="biological_report_section_confidence",
                )
            )
    for path in run_qc_assessment_tsv_paths:
        for row in _read_tsv_rows(path):
            entity_id = _empty_to_none(row.get("entity_id")) or _empty_to_none(
                row.get("run_id")
            )
            if entity_id is None:
                continue
            message = _empty_to_none(row.get("message")) or (
                "run QC assessment row preserved without a free-text message"
            )
            entries.append(
                InteractiveResultQcEntry(
                    qc_id=f"run_qc:{path.name}:{entity_id}",
                    qc_kind=InteractiveResultQcKind.RUN_QC_ASSESSMENT,
                    scope=_empty_to_none(row.get("scope")) or "run",
                    entity_id=entity_id,
                    status=_empty_to_none(row.get("qc_status")) or "unknown",
                    severity=_empty_to_none(row.get("severity")),
                    reason_codes=_split_multi(row.get("status_reason_codes", "")),
                    message=message,
                    source_surface=path.name,
                )
            )
    return tuple(sorted(entries, key=lambda entry: entry.qc_id))


def _build_cards(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultCard, ...]:
    cards: list[InteractiveResultCard] = []
    protein_graph_node_ids_by_card_id: dict[str, tuple[str, ...]] = {}
    if biological_artifacts is not None:
        report_dir = biological_artifacts["report_dir"]
        artifact_paths = biological_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "protein_card_tsv"):
            graph_node_ids = tuple(
                sorted(
                    {
                        row["graph_claim_node_id"],
                        row["graph_subject_node_id"],
                        *_split_multi(row.get("graph_support_node_ids", "")),
                    }
                )
            )
            protein_graph_node_ids_by_card_id[row["card_id"]] = graph_node_ids
            cards.append(
                InteractiveResultCard(
                    card_id=row["card_id"],
                    card_kind=InteractiveResultCardKind.PROTEIN_EVIDENCE,
                    subject_id=row["protein_group_id"],
                    subject_label=_empty_to_none(row.get("gene_symbol"))
                    or row["representative_protein_ref"],
                    confidence_label=None,
                    evidence_tier=_empty_to_none(row.get("evidence_tier")),
                    warning_codes=_split_multi(row.get("warning_codes", "")),
                    linked_protein_refs=_split_multi(row.get("protein_refs", "")),
                    linked_site_keys=_split_multi(row.get("ptm_sites", "")),
                    linked_pathway_ids=_split_multi(row.get("pathway_ids", "")),
                    graph_node_ids=graph_node_ids,
                    source_surface="biological_protein_cards",
                )
            )
        for row in _read_optional_rows(
            report_dir,
            artifact_paths,
            "protein_mechanism_card_tsv",
        ):
            cards.append(
                InteractiveResultCard(
                    card_id=row["card_id"],
                    card_kind=InteractiveResultCardKind.PROTEIN_MECHANISM,
                    subject_id=row["protein_group_id"],
                    subject_label=_empty_to_none(row.get("gene_symbol"))
                    or row["representative_protein_ref"],
                    confidence_label=_empty_to_none(row.get("confidence_tier")),
                    evidence_tier=_empty_to_none(row.get("evidence_tier")),
                    warning_codes=_split_multi(row.get("warning_codes", "")),
                    linked_protein_refs=(row["representative_protein_ref"],),
                    linked_site_keys=_split_multi(row.get("ptm_site_keys", "")),
                    linked_pathway_ids=_split_multi(row.get("pathway_ids", "")),
                    graph_node_ids=protein_graph_node_ids_by_card_id.get(
                        row["protein_card_id"],
                        (row["graph_claim_node_id"],),
                    ),
                    source_surface="biological_protein_mechanism_cards",
                )
            )
    if ptm_artifacts is not None:
        report_dir = ptm_artifacts["report_dir"]
        artifact_paths = ptm_artifacts["artifact_paths"]
        for row in _read_optional_rows(report_dir, artifact_paths, "evidence_card_tsv"):
            cards.append(
                InteractiveResultCard(
                    card_id=row["card_id"],
                    card_kind=InteractiveResultCardKind.PTM_EVIDENCE,
                    subject_id=row["site_key"],
                    subject_label=row["site_key"],
                    confidence_label=_empty_to_none(row.get("localization_tier")),
                    evidence_tier=None,
                    warning_codes=_split_multi(row.get("warning_codes", "")),
                    linked_protein_refs=(row["protein_ref"],),
                    linked_site_keys=(row["site_key"],),
                    linked_pathway_ids=(),
                    graph_node_ids=(),
                    source_surface="ptm_evidence_cards",
                )
            )
    return tuple(sorted(cards, key=lambda entry: (entry.card_kind.value, entry.card_id)))


def _build_graph(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
) -> tuple[tuple[InteractiveResultGraphNode, ...], tuple[InteractiveResultGraphEdge, ...]]:
    if biological_artifacts is None:
        return (), ()
    report_dir = biological_artifacts["report_dir"]
    artifact_paths = biological_artifacts["artifact_paths"]
    nodes = tuple(
        InteractiveResultGraphNode(
            node_id=row["node_id"],
            entity_type=row["entity_type"],
            entity_ref=row["entity_ref"],
            label=_empty_to_none(row.get("label")),
            claim_state=_empty_to_none(row.get("claim_state")),
            trust_class=_empty_to_none(row.get("trust_class")),
            contradiction_ids=_split_pipe(row.get("contradiction_ids", "")),
            context_refs=_split_pipe(row.get("context_refs", "")),
        )
        for row in _read_optional_rows(report_dir, artifact_paths, "evidence_graph_nodes_tsv")
    )
    edges = tuple(
        InteractiveResultGraphEdge(
            source_node_id=row["source_node_id"],
            target_node_id=row["target_node_id"],
            relation=row["relation"],
            source_row_ref=_empty_to_none(row.get("source_row_ref")),
            confidence=_empty_to_none(row.get("confidence")),
            evidence_type=_empty_to_none(row.get("evidence_type")),
            reason=_empty_to_none(row.get("reason")),
            support_count=_parse_optional_int(row.get("support_count")),
        )
        for row in _read_optional_rows(report_dir, artifact_paths, "evidence_graph_edges_tsv")
    )
    return nodes, edges


def _build_plots(
    *,
    biological_artifacts: _LoadedReportArtifacts | None,
    ptm_artifacts: _LoadedReportArtifacts | None,
) -> tuple[InteractiveResultPlot, ...]:
    plots: list[InteractiveResultPlot] = []
    if biological_artifacts is not None:
        for artifact_key, plot_kind in (
            ("volcano_tsv", InteractiveResultPlotKind.BIOLOGICAL_VOLCANO_TSV),
            ("volcano_json", InteractiveResultPlotKind.BIOLOGICAL_VOLCANO_JSON),
            ("volcano_svg", InteractiveResultPlotKind.BIOLOGICAL_VOLCANO_SVG),
            ("volcano_html", InteractiveResultPlotKind.BIOLOGICAL_VOLCANO_HTML),
            ("heatmap_matrix_tsv", InteractiveResultPlotKind.BIOLOGICAL_HEATMAP_MATRIX),
            (
                "heatmap_column_metadata_tsv",
                InteractiveResultPlotKind.BIOLOGICAL_HEATMAP_COLUMNS,
            ),
            (
                "heatmap_row_metadata_tsv",
                InteractiveResultPlotKind.BIOLOGICAL_HEATMAP_ROWS,
            ),
            ("sample_pca_scores_tsv", InteractiveResultPlotKind.BIOLOGICAL_SAMPLE_PCA),
        ):
            relative_path = _artifact_path(biological_artifacts, artifact_key)
            if relative_path is not None:
                plots.append(
                    InteractiveResultPlot(
                        plot_kind=plot_kind,
                        source_kind=InteractiveResultSourceKind.BIOLOGICAL_REPORT,
                        relative_path=relative_path,
                        media_type=_media_type_from_suffix(relative_path),
                    )
                )
    if ptm_artifacts is not None:
        for artifact_key, plot_kind in (
            (
                "differential_volcano_tsv",
                InteractiveResultPlotKind.PTM_DIFFERENTIAL_VOLCANO,
            ),
            ("motif_logo_tsv", InteractiveResultPlotKind.PTM_MOTIF_LOGO),
            ("motif_frequency_tsv", InteractiveResultPlotKind.PTM_MOTIF_FREQUENCY),
            ("motif_window_tsv", InteractiveResultPlotKind.PTM_MOTIF_WINDOWS),
        ):
            relative_path = _artifact_path(ptm_artifacts, artifact_key)
            if relative_path is not None:
                plots.append(
                    InteractiveResultPlot(
                        plot_kind=plot_kind,
                        source_kind=InteractiveResultSourceKind.PTM_REPORT,
                        relative_path=relative_path,
                        media_type=_media_type_from_suffix(relative_path),
                    )
                )
    return tuple(sorted(plots, key=lambda entry: (entry.source_kind.value, entry.plot_kind.value)))


def _artifact_path(artifacts: _LoadedReportArtifacts, artifact_key: str) -> str | None:
    artifact_paths = artifacts["artifact_paths"]
    value = artifact_paths.get(artifact_key)
    if not isinstance(value, str) or not value:
        return None
    return value


def _read_optional_rows(
    report_dir: Path,
    artifact_paths: dict[str, str],
    artifact_key: str,
) -> tuple[dict[str, str], ...]:
    relative_path = artifact_paths.get(artifact_key)
    if relative_path is None:
        return ()
    path = report_dir / relative_path
    if not path.exists():
        return ()
    return _read_tsv_rows(path)


def _read_optional_matrix_rows(
    report_dir: Path,
    artifact_paths: dict[str, str],
    artifact_key: str,
) -> tuple[dict[str, str], ...]:
    relative_path = artifact_paths.get(artifact_key)
    if relative_path is None:
        return ()
    path = report_dir / relative_path
    if not path.exists():
        return ()
    rows = _read_tsv_rows(path)
    if not rows:
        return ()
    static_fields = {
        "site_key",
        "protein_ref",
        "residue",
        "position",
        "modification_name",
        "target_decoy_label",
        "localization_tier",
        "ambiguous",
        "shared_peptide",
        "candidate_positions",
        "localized_peptides",
    }
    sample_ids = tuple(key for key in rows[0].keys() if key not in static_fields)
    return tuple({"sample_id": sample_id} for sample_id in sample_ids)


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path.name!r} must include a header row")
        return tuple(
            {
                str(key or "").strip(): str(value or "").strip()
                for key, value in row.items()
            }
            for row in reader
        )


def _split_multi(value: str) -> tuple[str, ...]:
    parts = [part.strip() for part in value.split(";")]
    return tuple(part for part in parts if part)


def _split_pipe(value: str) -> tuple[str, ...]:
    parts = [part.strip() for part in value.split("|")]
    return tuple(part for part in parts if part)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return None if not normalized else normalized


def _parse_optional_float(value: str | None) -> float | None:
    normalized = _empty_to_none(value)
    if normalized is None:
        return None
    return float(normalized)


def _parse_optional_int(value: str | None) -> int | None:
    normalized = _empty_to_none(value)
    if normalized is None:
        return None
    return int(normalized)


def _parse_optional_bool(value: str | None) -> bool | None:
    normalized = _empty_to_none(value)
    if normalized is None:
        return None
    lowered = normalized.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"expected boolean text but received {normalized!r}")


def _coerce_optional_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return _empty_to_none(value)
    return str(value)


def _media_type_from_suffix(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".html": "text/html",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".tsv": "text/tab-separated-values",
    }.get(suffix, "application/octet-stream")


__all__ = [
    "InteractiveResultBundle",
    "InteractiveResultBundleSummary",
    "InteractiveResultCard",
    "InteractiveResultCardKind",
    "InteractiveResultGraphEdge",
    "InteractiveResultGraphNode",
    "InteractiveResultPathway",
    "InteractiveResultPeptide",
    "InteractiveResultPlot",
    "InteractiveResultPlotKind",
    "InteractiveResultProtein",
    "InteractiveResultPtmSite",
    "InteractiveResultQcEntry",
    "InteractiveResultQcKind",
    "InteractiveResultSample",
    "InteractiveResultSourceKind",
    "InteractiveResultSourceReport",
    "build_interactive_result_bundle_from_artifacts",
    "render_interactive_result_bundle_summary_tsv",
]
