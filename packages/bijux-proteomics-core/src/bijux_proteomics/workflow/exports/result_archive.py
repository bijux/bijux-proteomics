# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Archive rehydration owner for workflow result manifests and preserved result surfaces."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.domain.errors import (
    InvalidWorkflowError,
    SchemaError,
)
from bijux_proteomics.lab.actions import (
    LabActionPacket,
    build_lab_action_packets_from_qc_assessment,
    parse_lab_action_assessment_tsv,
    parse_lab_action_packet_tsv,
    render_lab_action_packets_tsv,
)
from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
    ProteomicsEvidenceType,
    build_proteomics_evidence_graph,
)
from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultCard,
    InteractiveResultCardKind,
    InteractiveResultGraphEdge,
    InteractiveResultGraphNode,
    InteractiveResultSourceKind,
    build_interactive_result_bundle_from_artifacts,
)
from bijux_proteomics.workflow.exports.result_manifest import (
    ResultManifestInputKind,
    ResultManifestReport,
    ResultManifestSourceKind,
)
from bijux_proteomics.workflow.studies.study_results import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyDesignEntry,
    ProteomicsStudyDesignSnapshot,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
    ProteomicsStudyStatisticKind,
    ProteomicsStudyStatisticSurface,
)


def load_result_archive(path: Path) -> ProteomicsStudyResult:
    """Load one archived result manifest into a queryable study result."""

    manifest_path = _resolve_manifest_path(path)
    try:
        manifest = ResultManifestReport.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except ValidationError as exc:
        raise SchemaError(
            f"result archive manifest is invalid: {manifest_path}"
        ) from exc
    biological_report_dir = _resolve_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
    )
    ptm_report_dir = _resolve_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.PTM_REPORT,
    )
    if biological_report_dir is None and ptm_report_dir is None:
        raise InvalidWorkflowError(
            "result archive rehydration requires at least one biological or PTM source report"
        )
    run_qc_paths = _resolve_run_qc_paths(manifest=manifest, manifest_path=manifest_path)
    lab_action_packet_paths = _resolve_lab_action_packet_paths(
        manifest=manifest,
        manifest_path=manifest_path,
    )
    bundle = build_interactive_result_bundle_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_paths,
    )
    archived_lab_action_packets = _load_archived_lab_action_packets(
        lab_action_packet_paths
    )
    study_kind = _derive_archived_study_kind(bundle)
    matrix_surfaces = _build_matrix_surfaces(bundle)
    statistic_surfaces = _build_statistic_surfaces(bundle)
    qc_surfaces = _build_qc_surfaces(
        bundle,
        archived_lab_action_packets=archived_lab_action_packets,
    )
    card_surfaces = _build_card_surfaces(bundle)
    conclusions = _build_conclusions(
        manifest=manifest,
        manifest_path=manifest_path,
        bundle=bundle,
    )
    return ProteomicsStudyResult(
        study_kind=study_kind,
        source_surface="ResultManifestReport",
        design=_build_design_snapshot(bundle),
        matrix_surfaces=matrix_surfaces,
        statistic_surfaces=statistic_surfaces,
        qc_surfaces=qc_surfaces,
        card_surfaces=card_surfaces,
        biological_conclusions=conclusions,
        archived_lab_action_packets=archived_lab_action_packets,
        interactive_result_bundle=bundle,
        archive_manifest=manifest,
        archived_evidence_graph=_build_archived_evidence_graph(bundle),
        summary=ProteomicsStudyResultSummary(
            design_entry_count=bundle.summary.sample_count,
            matrix_surface_count=len(matrix_surfaces),
            statistic_surface_count=len(statistic_surfaces),
            qc_surface_count=len(qc_surfaces),
            card_surface_count=len(card_surfaces),
            conclusion_count=len(conclusions),
        ),
        note=(
            "result archive rehydration rebuilds a study result from the preserved result "
            "manifest, exported report directories, archived cards, claims, QC entries, "
            "lab action packets, plot and matrix artifacts, and the interactive evidence bundle without "
            "rerunning an analytical workflow"
        ),
    )


def write_result_archive_lab_action_packets(
    *,
    out_path: Path,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> tuple[LabActionPacket, ...]:
    """Write archived lab action packets for failed run or sample QC ledgers."""

    entries = tuple(
        entry
        for path in run_qc_assessment_tsv_paths
        for entry in parse_lab_action_assessment_tsv(path)
    )
    packets = build_lab_action_packets_from_qc_assessment(entries)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_output_table_tsv(out_path, render_lab_action_packets_tsv(packets))
    return packets


def _resolve_manifest_path(path: Path) -> Path:
    manifest_path = path / "result_manifest.json" if path.is_dir() else path
    if not manifest_path.exists():
        raise InvalidWorkflowError(
            f"result archive manifest is missing from path: {manifest_path}"
        )
    return manifest_path


def _resolve_source_report_dir(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    source_kind: ResultManifestSourceKind,
) -> Path | None:
    for source_report in manifest.source_reports:
        if source_report.source_kind is source_kind:
            return _resolve_archive_path(manifest_path.parent, source_report.report_dir)
    return None


def _resolve_run_qc_paths(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
) -> tuple[Path, ...]:
    paths = []
    for input_entry in manifest.inputs:
        if input_entry.input_kind is ResultManifestInputKind.RUN_QC_ASSESSMENT:
            paths.append(_resolve_archive_path(manifest_path.parent, input_entry.path))
    return tuple(paths)


def _resolve_lab_action_packet_paths(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
) -> tuple[Path, ...]:
    return tuple(
        _resolve_archive_path(manifest_path.parent, entry.path)
        for entry in manifest.inputs
        if entry.input_kind is ResultManifestInputKind.LAB_ACTION_PACKET
    )


def _resolve_archive_path(base_dir: Path, archived_path: str) -> Path:
    candidate = Path(archived_path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def _derive_archived_study_kind(bundle: InteractiveResultBundle) -> ProteomicsStudyKind:
    source_kinds = {report.source_kind for report in bundle.source_reports}
    if source_kinds == {InteractiveResultSourceKind.PTM_REPORT}:
        return ProteomicsStudyKind.PTM
    return ProteomicsStudyKind.ARCHIVED


def _build_design_snapshot(
    bundle: InteractiveResultBundle,
) -> ProteomicsStudyDesignSnapshot:
    entries = tuple(
        ProteomicsStudyDesignEntry(
            sample_id=sample.sample_id,
            condition=sample.condition,
            replicate=sample.replicate,
            fraction=sample.fraction,
            batch=sample.batch,
            pair_id=None,
            multiplex_group=None,
            multiplex_channel=None,
            sample_role=None,
        )
        for sample in bundle.samples
    )
    return ProteomicsStudyDesignSnapshot(
        entries=entries,
        sample_count=len(entries),
        condition_count=len({entry.condition for entry in entries if entry.condition}),
        batch_count=len({entry.batch for entry in entries if entry.batch}),
        paired_sample_count=0,
        multiplexed_sample_count=0,
        note=(
            "design snapshot was rehydrated from archived interactive sample metadata "
            "without requiring a fresh experimental-design workflow parse"
        ),
    )


def _build_matrix_surfaces(
    bundle: InteractiveResultBundle,
) -> tuple[ProteomicsStudyMatrixSurface, ...]:
    surfaces: list[ProteomicsStudyMatrixSurface] = []
    if any(
        plot.plot_kind.value == "biological_heatmap_matrix" for plot in bundle.plots
    ):
        surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="biological_heatmap_matrix",
                kind=ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
                entity_count=bundle.summary.protein_count,
                sample_count=bundle.summary.sample_count,
                note="archived biological heatmap matrix remains available through the result bundle",
            )
        )
    if bundle.summary.ptm_site_count > 0:
        surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="ptm_site_quant_matrix",
                kind=ProteomicsStudyMatrixKind.PTM_SITE,
                entity_count=bundle.summary.ptm_site_count,
                sample_count=bundle.summary.sample_count,
                note="archived PTM site matrix remains available through the result bundle",
            )
        )
    if bundle.summary.protein_count > 0:
        surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="archived_protein_results",
                kind=ProteomicsStudyMatrixKind.LABEL_FREE_PROTEIN,
                entity_count=bundle.summary.protein_count,
                sample_count=bundle.summary.sample_count,
                note="archived protein-level results remain queryable without rerunning protein quantification",
            )
        )
    return tuple(surfaces)


def _build_statistic_surfaces(
    bundle: InteractiveResultBundle,
) -> tuple[ProteomicsStudyStatisticSurface, ...]:
    surfaces: list[ProteomicsStudyStatisticSurface] = []
    protein_significant_count = sum(
        1
        for protein in bundle.proteins
        if protein.significant is True
        or (
            protein.significant is None
            and protein.adjusted_p_value is not None
            and protein.adjusted_p_value <= 0.05
        )
    )
    if bundle.summary.protein_count > 0:
        surfaces.append(
            ProteomicsStudyStatisticSurface(
                surface_name="archived_protein_differential",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN,
                entity_count=bundle.summary.protein_count,
                significant_entity_count=protein_significant_count,
                note="archived protein differential statistics remain queryable without rerunning inference",
            )
        )
    ptm_significant_count = sum(
        1
        for site in bundle.ptm_sites
        if site.adjusted_p_value is not None and site.adjusted_p_value <= 0.05
    )
    if bundle.summary.ptm_site_count > 0:
        surfaces.append(
            ProteomicsStudyStatisticSurface(
                surface_name="archived_ptm_site_differential",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PTM_SITE,
                entity_count=bundle.summary.ptm_site_count,
                significant_entity_count=ptm_significant_count,
                note="archived PTM site differential statistics remain queryable without rerunning inference",
            )
        )
    return tuple(surfaces)


def _build_qc_surfaces(
    bundle: InteractiveResultBundle,
    *,
    archived_lab_action_packets: tuple[LabActionPacket, ...],
) -> tuple[ProteomicsStudyQcSurface, ...]:
    surfaces: list[ProteomicsStudyQcSurface] = []
    if bundle.qc_entries:
        issue_count = sum(
            1
            for entry in bundle.qc_entries
            if entry.status.lower() not in {"pass", "ok"}
        )
        surfaces.append(
            ProteomicsStudyQcSurface(
                surface_name="archived_result_qc",
                kind=ProteomicsStudyQcKind.ARCHIVED_RESULT,
                issue_count=issue_count,
                note="archived QC entries were grouped from preserved experiment-confidence and run-QC surfaces",
            )
        )
    if archived_lab_action_packets:
        surfaces.append(
            ProteomicsStudyQcSurface(
                surface_name="archived_lab_action_packets",
                kind=ProteomicsStudyQcKind.LAB_ACTION_PACKET,
                issue_count=len(archived_lab_action_packets),
                note="archived lab action packets preserve failed run or sample troubleshooting across result handoff",
            )
        )
    return tuple(surfaces)


def _load_archived_lab_action_packets(
    paths: tuple[Path, ...],
) -> tuple[LabActionPacket, ...]:
    packets = [packet for path in paths for packet in parse_lab_action_packet_tsv(path)]
    return tuple(
        sorted(
            packets,
            key=lambda packet: (
                packet.entity_type,
                packet.entity_id,
                packet.problem,
                packet.severity,
            ),
        )
    )


def _build_card_surfaces(
    bundle: InteractiveResultBundle,
) -> tuple[ProteomicsStudyCardSurface, ...]:
    cards_by_kind: dict[InteractiveResultCardKind, list[InteractiveResultCard]] = {
        kind: [] for kind in InteractiveResultCardKind
    }
    for card in bundle.cards:
        cards_by_kind.setdefault(card.card_kind, []).append(card)
    surfaces: list[ProteomicsStudyCardSurface] = []
    for card_kind, study_kind, surface_name in (
        (
            InteractiveResultCardKind.PROTEIN_EVIDENCE,
            ProteomicsStudyCardKind.PROTEIN_EVIDENCE,
            "archived_protein_cards",
        ),
        (
            InteractiveResultCardKind.PROTEIN_MECHANISM,
            ProteomicsStudyCardKind.PROTEIN_MECHANISM,
            "archived_protein_mechanism_cards",
        ),
        (
            InteractiveResultCardKind.PTM_EVIDENCE,
            ProteomicsStudyCardKind.PTM_EVIDENCE,
            "archived_ptm_evidence_cards",
        ),
    ):
        cards = cards_by_kind.get(card_kind, [])
        if not cards:
            continue
        surfaces.append(
            ProteomicsStudyCardSurface(
                surface_name=surface_name,
                kind=study_kind,
                card_count=len(cards),
                warning_count=sum(bool(card.warning_codes) for card in cards),
                note="card surface was rehydrated from archived interactive result cards",
            )
        )
    return tuple(surfaces)


def _build_conclusions(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    bundle: InteractiveResultBundle,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    conclusions: list[ProteomicsStudyConclusionEntry] = []
    biological_report_dir = _resolve_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
    )
    ptm_report_dir = _resolve_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.PTM_REPORT,
    )
    if biological_report_dir is not None:
        conclusions.extend(
            _load_biological_claims(
                manifest=manifest,
                manifest_path=manifest_path,
                source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
            )
        )
        conclusions.extend(
            _load_biological_hypotheses(
                manifest=manifest,
                manifest_path=manifest_path,
            )
        )
        conclusions.extend(
            _load_regulator_conclusions(
                manifest=manifest,
                manifest_path=manifest_path,
            )
        )
    if ptm_report_dir is not None:
        conclusions.extend(
            _load_ptm_claims(
                manifest=manifest,
                manifest_path=manifest_path,
                bundle=bundle,
            )
        )
    return tuple(
        sorted(
            conclusions,
            key=lambda entry: (entry.kind.value, entry.subject_id, entry.conclusion_id),
        )
    )


def _load_biological_claims(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    source_kind: ResultManifestSourceKind,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    entries: list[ProteomicsStudyConclusionEntry] = []
    for artifact_key, conclusion_kind in (
        ("supported_claim_tsv", ProteomicsStudyConclusionKind.SUPPORTED_CLAIM),
        ("rejected_claim_tsv", ProteomicsStudyConclusionKind.REJECTED_CLAIM),
    ):
        for row in _read_source_rows(
            manifest=manifest,
            manifest_path=manifest_path,
            source_kind=source_kind,
            artifact_key=artifact_key,
        ):
            entries.append(
                ProteomicsStudyConclusionEntry(
                    conclusion_id=row["claim_id"],
                    kind=conclusion_kind,
                    subject_id=row["subject_id"],
                    subject_label=row["subject_label"],
                    status=row["status"],
                    score=_parse_optional_float(row.get("robustness_score")),
                    evidence_surface=artifact_key,
                    summary_text=row["claim_text"],
                )
            )
    return tuple(entries)


def _load_biological_hypotheses(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    entries = []
    for row in _read_source_rows(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
        artifact_key="biological_hypothesis_tsv",
    ):
        entries.append(
            ProteomicsStudyConclusionEntry(
                conclusion_id=row["hypothesis_id"],
                kind=ProteomicsStudyConclusionKind.BIOLOGICAL_HYPOTHESIS,
                subject_id=row["subject_id"],
                subject_label=row["subject_label"],
                status=row["confidence_tier"],
                score=_parse_optional_float(row.get("confidence_score")),
                evidence_surface="biological_hypothesis_tsv",
                summary_text=row["claim"],
            )
        )
    return tuple(entries)


def _load_regulator_conclusions(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    entries = []
    for row in _read_source_rows(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
        artifact_key="regulator_inference_tsv",
    ):
        entries.append(
            ProteomicsStudyConclusionEntry(
                conclusion_id=row["regulator"],
                kind=ProteomicsStudyConclusionKind.REGULATOR_INFERENCE,
                subject_id=row["regulator"],
                subject_label=row["regulator"],
                status=row["direction"],
                score=_parse_optional_float(row.get("score")),
                evidence_surface="regulator_inference_tsv",
                summary_text=row["note"],
            )
        )
    return tuple(entries)


def _load_ptm_claims(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    bundle: InteractiveResultBundle,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    site_labels = {site.site_key: site.site_key for site in bundle.ptm_sites}
    entries = []
    for row in _read_source_rows(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=ResultManifestSourceKind.PTM_REPORT,
        artifact_key="evidence_claim_tsv",
    ):
        site_key = row["site_key"]
        entries.append(
            ProteomicsStudyConclusionEntry(
                conclusion_id=row["claim_id"],
                kind=ProteomicsStudyConclusionKind.PTM_NARRATIVE_CLAIM,
                subject_id=site_key,
                subject_label=site_labels.get(site_key, site_key),
                status=row["claim_kind"],
                score=None,
                evidence_surface="evidence_claim_tsv",
                summary_text=row["text"],
            )
        )
    return tuple(entries)


def _read_source_rows(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    source_kind: ResultManifestSourceKind,
    artifact_key: str,
) -> tuple[dict[str, str], ...]:
    report_dir = _require_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=source_kind,
    )
    relative_path = _find_artifact_relative_path(
        manifest=manifest,
        source_kind=source_kind,
        artifact_key=artifact_key,
    )
    if relative_path is None:
        return ()
    artifact_path = report_dir / relative_path
    if not artifact_path.exists():
        return ()
    return _read_tsv_rows(artifact_path)


def _require_source_report_dir(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    source_kind: ResultManifestSourceKind,
) -> Path:
    path = _resolve_source_report_dir(
        manifest=manifest,
        manifest_path=manifest_path,
        source_kind=source_kind,
    )
    if path is None:
        raise InvalidWorkflowError(
            f"source report directory is missing for {source_kind.value}"
        )
    return path


def _find_artifact_relative_path(
    *,
    manifest: ResultManifestReport,
    source_kind: ResultManifestSourceKind,
    artifact_key: str,
) -> str | None:
    for entry in manifest.files:
        if entry.source_kind is source_kind and entry.artifact_key == artifact_key:
            return entry.relative_path
    return None


def _build_archived_evidence_graph(
    bundle: InteractiveResultBundle,
) -> ProteomicsEvidenceGraph | None:
    if not bundle.graph_nodes:
        return None
    nodes = tuple(_build_evidence_node(node) for node in bundle.graph_nodes)
    edges = tuple(_build_evidence_edge(edge) for edge in bundle.graph_edges)
    return build_proteomics_evidence_graph(nodes, edges)


def _build_evidence_node(node: InteractiveResultGraphNode) -> ProteomicsEvidenceNode:
    return ProteomicsEvidenceNode(
        node_id=node.node_id,
        entity_type=ProteomicsEvidenceNodeKind(node.entity_type),
        entity_ref=node.entity_ref,
        label=node.label or node.entity_ref,
        claim_state=node.claim_state or "observed",
        trust_class=node.trust_class or "unreviewed",
        contradiction_ids=node.contradiction_ids,
        context_refs=tuple(_parse_context_ref(value) for value in node.context_refs),
    )


def _build_evidence_edge(edge: InteractiveResultGraphEdge) -> ProteomicsEvidenceEdge:
    if edge.source_row_ref is None:
        raise SchemaError(
            f"archived evidence edge is missing source_row_ref: {edge.source_node_id}->{edge.target_node_id}"
        )
    if edge.confidence is None:
        raise SchemaError(
            f"archived evidence edge is missing confidence: {edge.source_node_id}->{edge.target_node_id}"
        )
    if edge.evidence_type is None:
        raise SchemaError(
            f"archived evidence edge is missing evidence_type: {edge.source_node_id}->{edge.target_node_id}"
        )
    if edge.reason is None:
        raise SchemaError(
            f"archived evidence edge is missing reason: {edge.source_node_id}->{edge.target_node_id}"
        )
    return ProteomicsEvidenceEdge(
        source_node_id=edge.source_node_id,
        target_node_id=edge.target_node_id,
        relation=ProteomicsEvidenceEdgeKind(edge.relation),
        source_row_ref=edge.source_row_ref,
        confidence=float(edge.confidence),
        evidence_type=ProteomicsEvidenceType(edge.evidence_type),
        reason=edge.reason,
        support_count=edge.support_count or 1,
    )


def _parse_context_ref(value: str) -> ProteomicsEvidenceContextRef:
    entity_type_value, separator, entity_ref = value.partition(":")
    if not separator or not entity_ref:
        raise SchemaError(f"archived evidence context ref is malformed: {value!r}")
    return ProteomicsEvidenceContextRef(
        entity_type=ProteomicsEvidenceNodeKind(entity_type_value),
        entity_ref=entity_ref,
    )


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise SchemaError(f"{path.name!r} must include a header row")
        return tuple(
            {
                str(key or "").strip(): str(value or "").strip()
                for key, value in row.items()
            }
            for row in reader
        )


def _parse_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return float(normalized)


__all__ = [
    "load_result_archive",
    "write_result_archive_lab_action_packets",
]
