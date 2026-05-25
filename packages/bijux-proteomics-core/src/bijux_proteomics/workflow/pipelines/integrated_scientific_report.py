# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Integrated scientific report generation over shipped proteomics demo outputs."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow.pipelines.surprising_demo import SurprisingDemoReport
from bijux_proteomics.workflow.pipelines.surprising_demo_interrogation import (
    ensure_surprising_demo_outputs,
)
from bijux_proteomics_foundation import JsonModel


class IntegratedScientificReportSectionKey(StrEnum):
    """Required section surfaces for the integrated scientific report."""

    EXPERIMENT_DESIGN = "experiment_design"
    DATA_QUALITY = "data_quality"
    ACCEPTED_RESULTS = "accepted_results"
    DOWNGRADED_RESULTS = "downgraded_results"
    REFUSED_CLAIMS = "refused_claims"
    PTM_EVIDENCE = "ptm_evidence"
    MECHANISMS = "mechanisms"
    VALIDATION_CANDIDATES = "validation_candidates"
    BELIEF_AUDIT = "belief_audit"


class IntegratedScientificSentenceRole(StrEnum):
    """Sentence roles inside the integrated scientific report."""

    CONTEXT = "context"
    SCIENTIFIC_CLAIM = "scientific_claim"


class IntegratedScientificReportSentence(JsonModel):
    """One sentence-level report entry with explicit scientific linking."""

    model_config = ConfigDict(extra="forbid")

    sentence_id: str = Field(..., min_length=1)
    section_key: IntegratedScientificReportSectionKey
    role: IntegratedScientificSentenceRole
    text: str = Field(..., min_length=1)
    linked_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_row_refs: tuple[str, ...] = Field(default_factory=tuple)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class IntegratedScientificReportSection(JsonModel):
    """One ordered section of the integrated scientific report."""

    model_config = ConfigDict(extra="forbid")

    section_key: IntegratedScientificReportSectionKey
    title: str = Field(..., min_length=1)
    sentence_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class IntegratedScientificReportSummary(JsonModel):
    """Compact summary over one integrated scientific report."""

    model_config = ConfigDict(extra="forbid")

    section_count: int = Field(..., ge=0)
    sentence_count: int = Field(..., ge=0)
    scientific_claim_count: int = Field(..., ge=0)
    linked_scientific_claim_count: int = Field(..., ge=0)


class IntegratedScientificReportArtifactPaths(JsonModel):
    """Stable artifact paths written by the integrated scientific report owner."""

    model_config = ConfigDict(extra="forbid")

    summary_tsv: str = Field(..., min_length=1)
    sentences_tsv: str = Field(..., min_length=1)
    report_html: str = Field(..., min_length=1)
    report_json: str = Field(..., min_length=1)


class IntegratedScientificReport(JsonModel):
    """Integrated scientific report over shipped demo outputs."""

    model_config = ConfigDict(extra="forbid")

    demo_output_dir: str = Field(..., min_length=1)
    source_report_json: str = Field(..., min_length=1)
    sections: tuple[IntegratedScientificReportSection, ...] = Field(
        default_factory=tuple
    )
    sentences: tuple[IntegratedScientificReportSentence, ...] = Field(
        default_factory=tuple
    )
    summary: IntegratedScientificReportSummary
    artifacts: IntegratedScientificReportArtifactPaths
    note: str = Field(..., min_length=1)


_SECTION_TITLES = {
    IntegratedScientificReportSectionKey.EXPERIMENT_DESIGN: "Experiment Design",
    IntegratedScientificReportSectionKey.DATA_QUALITY: "Data Quality",
    IntegratedScientificReportSectionKey.ACCEPTED_RESULTS: "Accepted Results",
    IntegratedScientificReportSectionKey.DOWNGRADED_RESULTS: "Downgraded Results",
    IntegratedScientificReportSectionKey.REFUSED_CLAIMS: "Refused Claims",
    IntegratedScientificReportSectionKey.PTM_EVIDENCE: "PTM Evidence",
    IntegratedScientificReportSectionKey.MECHANISMS: "Mechanisms",
    IntegratedScientificReportSectionKey.VALIDATION_CANDIDATES: "Validation Candidates",
    IntegratedScientificReportSectionKey.BELIEF_AUDIT: "Belief Audit",
}


def build_integrated_scientific_report(
    demo_output_dir: Path,
) -> IntegratedScientificReport:
    """Build and write the final integrated scientific report for the shipped demo."""

    ensure_surprising_demo_outputs(demo_output_dir)
    source_report = _load_surprising_demo_report(demo_output_dir)
    context = _load_integrated_report_context(demo_output_dir)
    sections, sentences = _build_sections_and_sentences(source_report, context=context)
    _validate_scientific_claim_links(sentences)
    summary = IntegratedScientificReportSummary(
        section_count=len(sections),
        sentence_count=len(sentences),
        scientific_claim_count=sum(
            sentence.role is IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM
            for sentence in sentences
        ),
        linked_scientific_claim_count=sum(
            sentence.role is IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM
            and bool(sentence.linked_ids)
            for sentence in sentences
        ),
    )
    summary_name = "integrated_scientific_report_summary.tsv"
    sentences_name = "integrated_scientific_report_sentences.tsv"
    html_name = "integrated_scientific_report.html"
    json_name = "integrated_scientific_report.json"
    artifacts = IntegratedScientificReportArtifactPaths(
        summary_tsv=summary_name,
        sentences_tsv=sentences_name,
        report_html=html_name,
        report_json=json_name,
    )
    report = IntegratedScientificReport(
        demo_output_dir=str(demo_output_dir),
        source_report_json="surprising_demo_report.json",
        sections=sections,
        sentences=sentences,
        summary=summary,
        artifacts=artifacts,
        note=(
            "integrated scientific report is generated from the shipped demo result "
            "object, evidence graph exports, cards, claims, QC ledgers, and belief audit"
        ),
    )
    (demo_output_dir / summary_name).write_text(
        render_integrated_scientific_report_summary_tsv(report),
        encoding="utf-8",
    )
    (demo_output_dir / sentences_name).write_text(
        render_integrated_scientific_report_sentences_tsv(report),
        encoding="utf-8",
    )
    (demo_output_dir / html_name).write_text(
        render_integrated_scientific_report_html(report),
        encoding="utf-8",
    )
    (demo_output_dir / json_name).write_text(
        report.to_stable_json() + "\n",
        encoding="utf-8",
    )
    return report


def render_integrated_scientific_report_summary_tsv(
    report: IntegratedScientificReport,
) -> str:
    """Render the integrated scientific report summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("section_count", report.summary.section_count),
        ("sentence_count", report.summary.sentence_count),
        ("scientific_claim_count", report.summary.scientific_claim_count),
        (
            "linked_scientific_claim_count",
            report.summary.linked_scientific_claim_count,
        ),
        ("note", report.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_integrated_scientific_report_sentences_tsv(
    report: IntegratedScientificReport,
) -> str:
    """Render sectioned report sentences with explicit links as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sentence_id",
            "section_key",
            "role",
            "text",
            "linked_ids",
            "source_row_refs",
            "artifact_paths",
            "note",
        )
    )
    for sentence in report.sentences:
        writer.writerow(
            (
                sentence.sentence_id,
                sentence.section_key.value,
                sentence.role.value,
                sentence.text,
                ";".join(sentence.linked_ids),
                ";".join(sentence.source_row_refs),
                ";".join(sentence.artifact_paths),
                sentence.note,
            )
        )
    return buffer.getvalue()


def render_integrated_scientific_report_html(
    report: IntegratedScientificReport,
) -> str:
    """Render the integrated scientific report as HTML."""

    sentence_map = {sentence.sentence_id: sentence for sentence in report.sentences}
    lines = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Integrated Scientific Report</title>",
        "</head>",
        "<body>",
        "<section>",
        "<h1>Integrated Scientific Report</h1>",
        (
            "<p>This report is generated from the shipped proteomics demo result object, "
            "evidence graph exports, cards, claims, QC ledgers, and belief audit.</p>"
        ),
    ]
    for section in report.sections:
        lines.extend(
            (
                f'<section id="{escape(section.section_key.value)}">',
                f"<h2>{escape(section.title)}</h2>",
            )
        )
        for sentence_id in section.sentence_ids:
            sentence = sentence_map[sentence_id]
            lines.append(
                f'<p id="{escape(sentence.sentence_id)}">{escape(sentence.text)}</p>'
            )
            if sentence.linked_ids or sentence.source_row_refs:
                lines.append("<ul>")
                if sentence.linked_ids:
                    lines.append(
                        "<li><strong>Linked claims/cards:</strong> "
                        f"{escape('; '.join(sentence.linked_ids))}</li>"
                    )
                if sentence.source_row_refs:
                    lines.append(
                        "<li><strong>Source rows:</strong> "
                        f"{escape('; '.join(sentence.source_row_refs))}</li>"
                    )
                if sentence.artifact_paths:
                    lines.append(
                        "<li><strong>Artifacts:</strong> "
                        f"{escape('; '.join(sentence.artifact_paths))}</li>"
                    )
                lines.append("</ul>")
        lines.append("</section>")
    lines.extend(("</section>", "</body>", "</html>"))
    return "\n".join(lines) + "\n"


class _IntegratedReportContext(JsonModel):
    """Internal artifact context for the integrated scientific report."""

    model_config = ConfigDict(extra="forbid")

    supported_claims: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    rejected_claims: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    protein_cards: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    mechanism_cards: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    pathway_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    ptm_mechanism_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    ptm_ambiguous_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    qc_rows: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    targeted_evidence_cards: tuple[dict[str, str], ...] = Field(default_factory=tuple)


def _load_surprising_demo_report(demo_output_dir: Path) -> SurprisingDemoReport:
    return SurprisingDemoReport.model_validate_json(
        (demo_output_dir / "surprising_demo_report.json").read_text(encoding="utf-8")
    )


def _load_integrated_report_context(demo_output_dir: Path) -> _IntegratedReportContext:
    return _IntegratedReportContext(
        supported_claims=_read_tsv_rows(
            demo_output_dir / "biological_review" / "biological_supported_claims.tsv"
        ),
        rejected_claims=_read_tsv_rows(
            demo_output_dir / "biological_review" / "biological_rejected_claims.tsv"
        ),
        protein_cards=_read_tsv_rows(
            demo_output_dir / "biological_review" / "biological_protein_cards.tsv"
        ),
        mechanism_cards=_read_tsv_rows(
            demo_output_dir
            / "biological_review"
            / "biological_protein_mechanism_cards.tsv"
        ),
        pathway_rows=_read_tsv_rows(
            demo_output_dir
            / "biological_review"
            / "biological_pathway_activity_condition_comparisons.tsv"
        ),
        ptm_mechanism_rows=_read_tsv_rows(
            demo_output_dir / "ptm_review" / "ptm_mechanism_classification.tsv"
        ),
        ptm_ambiguous_rows=_read_tsv_rows(
            demo_output_dir
            / "ptm_review"
            / "advanced_ptm_excluded_ambiguous_sites.tsv"
        ),
        qc_rows=_read_tsv_rows(demo_output_dir / "demo_qc_packets.tsv"),
        targeted_evidence_cards=_read_tsv_rows(
            demo_output_dir
            / "targeted_validation"
            / "advanced_targeted_evidence_cards.tsv"
        ),
    )


def _build_sections_and_sentences(
    source_report: SurprisingDemoReport,
    *,
    context: _IntegratedReportContext,
) -> tuple[
    tuple[IntegratedScientificReportSection, ...],
    tuple[IntegratedScientificReportSentence, ...],
]:
    design = source_report.study_result.design
    graph = source_report.study_result.biological_report.graph_report.graph
    top_supported = tuple(context.supported_claims[:2])
    rejected = context.rejected_claims
    p11111_card = next(
        row
        for row in context.protein_cards
        if row["representative_protein_ref"] == "P11111"
    )
    p22222_card = next(
        row
        for row in context.protein_cards
        if row["representative_protein_ref"] == "P22222"
    )
    q9dec1_card = next(
        row
        for row in context.protein_cards
        if row["representative_protein_ref"] == "Q9DEC1"
    )
    q9dec1_mechanism = next(
        row
        for row in context.mechanism_cards
        if row["representative_protein_ref"] == "Q9DEC1"
    )
    top_mechanisms = tuple(context.mechanism_cards[:2])
    top_targets = tuple(context.targeted_evidence_cards[:2])
    ambiguous_ptm = context.ptm_ambiguous_rows[0]
    ptm_mechanism = context.ptm_mechanism_rows[0]
    belief_top_ids = tuple(source_report.belief_audit_report.summary.top_claim_ids)

    sentences = (
        IntegratedScientificReportSentence(
            sentence_id="experiment-design-1",
            section_key=IntegratedScientificReportSectionKey.EXPERIMENT_DESIGN,
            role=IntegratedScientificSentenceRole.CONTEXT,
            text=(
                f"The integrated demo result object preserves {design.sample_count} biological "
                f"samples across {design.condition_count} conditions and pairs those "
                "label-free results with TMT, PTM, and targeted validation follow-up surfaces."
            ),
            source_row_refs=(
                *(
                    f"study_design:{entry.sample_id}"
                    for entry in source_report.study_result.design.entries
                ),
            ),
            artifact_paths=("surprising_demo_report.json",),
            note="experiment-design context comes directly from the persisted study result object",
        ),
        IntegratedScientificReportSentence(
            sentence_id="experiment-design-2",
            section_key=IntegratedScientificReportSectionKey.EXPERIMENT_DESIGN,
            role=IntegratedScientificSentenceRole.CONTEXT,
            text=(
                f"The same result object preserves {len(graph.nodes)} evidence-graph nodes "
                f"and {len(graph.edges)} edges for downstream citation and audit."
            ),
            source_row_refs=("graph_summary",),
            artifact_paths=("biological_review/biological_evidence_graph_nodes.tsv",),
            note="evidence-graph context is carried by the biological graph report summary",
        ),
        IntegratedScientificReportSentence(
            sentence_id="data-quality-1",
            section_key=IntegratedScientificReportSectionKey.DATA_QUALITY,
            role=IntegratedScientificSentenceRole.CONTEXT,
            text=(
                f"Data quality remains explicit: the demo preserves {len(context.qc_rows)} QC issue "
                "rows across multiplex validation and targeted assay review instead of silently filtering them."
            ),
            source_row_refs=tuple(
                f"demo_qc_packets:{row['subject_id']}:{row['status']}"
                for row in context.qc_rows
            ),
            artifact_paths=("demo_qc_packets.tsv",),
            note="qc context is derived from the shipped demo qc packet ledger",
        ),
        IntegratedScientificReportSentence(
            sentence_id="data-quality-2",
            section_key=IntegratedScientificReportSectionKey.DATA_QUALITY,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Targeted follow-up for protein:P001 remains unreliable because its evidence card "
                "preserves coelution and ratio-drift concerns rather than a clean validation signal."
            ),
            linked_ids=(_targeted_evidence_card_id(top_targets[0]),),
            source_row_refs=(
                f"advanced_targeted_evidence_cards:{top_targets[0]['candidate_id']}",
            ),
            artifact_paths=("targeted_validation/advanced_targeted_evidence_cards.tsv",),
            note="data-quality scientific claim is linked to the targeted evidence card row id",
        ),
        IntegratedScientificReportSentence(
            sentence_id="accepted-results-1",
            section_key=IntegratedScientificReportSectionKey.ACCEPTED_RESULTS,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                f"Accepted results retain {len(top_supported)} supported protein-abundance claims: "
                f"{'; '.join(row['claim_text'] for row in top_supported)}."
            ),
            linked_ids=tuple(row["claim_id"] for row in top_supported),
            source_row_refs=tuple(
                f"biological_supported_claims:{row['claim_id']}" for row in top_supported
            ),
            artifact_paths=("biological_review/biological_supported_claims.tsv",),
            note="accepted-result scientific claims are linked directly to supported claim ids",
        ),
        IntegratedScientificReportSentence(
            sentence_id="accepted-results-2",
            section_key=IntegratedScientificReportSectionKey.ACCEPTED_RESULTS,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "The accepted protein evidence remains high-confidence because P11111 and P22222 "
                "both retain graph-backed protein cards and high-confidence mechanism cards."
            ),
            linked_ids=(
                p11111_card["card_id"],
                p22222_card["card_id"],
                top_mechanisms[0]["card_id"],
                top_mechanisms[1]["card_id"],
            ),
            source_row_refs=(
                f"biological_protein_cards:{p11111_card['card_id']}",
                f"biological_protein_cards:{p22222_card['card_id']}",
                f"biological_protein_mechanism_cards:{top_mechanisms[0]['card_id']}",
                f"biological_protein_mechanism_cards:{top_mechanisms[1]['card_id']}",
            ),
            artifact_paths=(
                "biological_review/biological_protein_cards.tsv",
                "biological_review/biological_protein_mechanism_cards.tsv",
            ),
            note="accepted-result support is linked to evidence card ids rather than prose-only ranking",
        ),
        IntegratedScientificReportSentence(
            sentence_id="downgraded-results-1",
            section_key=IntegratedScientificReportSectionKey.DOWNGRADED_RESULTS,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Protein Q9DEC1 remains downgraded and excluded from the accepted narrative because "
                "its retained card is not significant and carries low sequence-coverage support."
            ),
            linked_ids=(q9dec1_card["card_id"], q9dec1_mechanism["card_id"]),
            source_row_refs=(
                f"biological_protein_cards:{q9dec1_card['card_id']}",
                f"biological_protein_mechanism_cards:{q9dec1_mechanism['card_id']}",
            ),
            artifact_paths=(
                "biological_review/biological_protein_cards.tsv",
                "biological_review/biological_protein_mechanism_cards.tsv",
            ),
            note="downgraded-result sentence is linked to the rejected protein evidence and mechanism cards",
        ),
        IntegratedScientificReportSentence(
            sentence_id="refused-claims-1",
            section_key=IntegratedScientificReportSectionKey.REFUSED_CLAIMS,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Refused claims remain explicit: the demo rejects one weak protein claim and two "
                "pathway narratives instead of silently dropping them from the final review."
            ),
            linked_ids=tuple(row["claim_id"] for row in rejected),
            source_row_refs=tuple(
                f"biological_rejected_claims:{row['claim_id']}" for row in rejected
            ),
            artifact_paths=("biological_review/biological_rejected_claims.tsv",),
            note="refused-claim sentence is linked directly to rejected claim ids",
        ),
        IntegratedScientificReportSentence(
            sentence_id="ptm-evidence-1",
            section_key=IntegratedScientificReportSectionKey.PTM_EVIDENCE,
            role=IntegratedScientificSentenceRole.CONTEXT,
            text=(
                "PTM evidence keeps exact supported sites separate from ambiguity groups, so unresolved "
                "localization is preserved instead of being duplicated into the exact-site matrix."
            ),
            source_row_refs=(
                f"advanced_ptm_excluded_ambiguous_sites:{ambiguous_ptm['site_key']}",
                f"ptm_mechanism_classification:{ptm_mechanism['site_key']}",
            ),
            artifact_paths=(
                "ptm_review/advanced_ptm_excluded_ambiguous_sites.tsv",
                "ptm_review/ptm_mechanism_classification.tsv",
            ),
            note="ptm-evidence context is anchored to ambiguity and mechanism rows even when no ptm claim ids are retained",
        ),
        IntegratedScientificReportSentence(
            sentence_id="ptm-evidence-2",
            section_key=IntegratedScientificReportSectionKey.PTM_EVIDENCE,
            role=IntegratedScientificSentenceRole.CONTEXT,
            text=(
                f"Site {ambiguous_ptm['site_key']} is carried through ambiguity group "
                f"{ambiguous_ptm['group_key']}, while {ptm_mechanism['site_key']} remains "
                f"{ptm_mechanism['mechanism_class']} after protein correction."
            ),
            source_row_refs=(
                f"advanced_ptm_excluded_ambiguous_sites:{ambiguous_ptm['site_key']}",
                f"ptm_mechanism_classification:{ptm_mechanism['site_key']}",
            ),
            artifact_paths=(
                "ptm_review/advanced_ptm_excluded_ambiguous_sites.tsv",
                "ptm_review/ptm_mechanism_classification.tsv",
            ),
            note="ptm section preserves exact source rows for ambiguity and supported mechanism statements",
        ),
        IntegratedScientificReportSentence(
            sentence_id="mechanisms-1",
            section_key=IntegratedScientificReportSectionKey.MECHANISMS,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Mechanism cards preserve P11111 as increased and P22222 as decreased with "
                "high-confidence evidence tiers despite peptide-support caveats."
            ),
            linked_ids=tuple(row["card_id"] for row in top_mechanisms),
            source_row_refs=tuple(
                f"biological_protein_mechanism_cards:{row['card_id']}"
                for row in top_mechanisms
            ),
            artifact_paths=("biological_review/biological_protein_mechanism_cards.tsv",),
            note="mechanism sentence is linked directly to protein mechanism card ids",
        ),
        IntegratedScientificReportSentence(
            sentence_id="validation-candidates-1",
            section_key=IntegratedScientificReportSectionKey.VALIDATION_CANDIDATES,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Validation candidates protein:P001 and protein:P002 remain inconclusive because "
                "their evidence cards preserve insufficient reliable replicates instead of a clean directional follow-up."
            ),
            linked_ids=tuple(_targeted_evidence_card_id(row) for row in top_targets),
            source_row_refs=tuple(
                f"advanced_targeted_evidence_cards:{row['candidate_id']}"
                for row in top_targets
            ),
            artifact_paths=("targeted_validation/advanced_targeted_evidence_cards.tsv",),
            note="validation-candidate sentence is linked to deterministic targeted evidence card ids",
        ),
        IntegratedScientificReportSentence(
            sentence_id="belief-audit-1",
            section_key=IntegratedScientificReportSectionKey.BELIEF_AUDIT,
            role=IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM,
            text=(
                "Belief audit keeps the top supported protein claims challengeable by preserving their "
                "current confidence, retained support, and explicit falsifier paths."
            ),
            linked_ids=belief_top_ids,
            source_row_refs=tuple(
                f"belief_audit:{entry.claim_id}"
                for entry in source_report.belief_audit_report.entries
                if entry.claim_id in set(belief_top_ids)
            ),
            artifact_paths=("demo_belief_audit.tsv",),
            note="belief-audit sentence is linked to the top claim ids preserved by the shipped demo audit",
        ),
    )
    sections = tuple(
        IntegratedScientificReportSection(
            section_key=section_key,
            title=_SECTION_TITLES[section_key],
            sentence_ids=tuple(
                sentence.sentence_id
                for sentence in sentences
                if sentence.section_key is section_key
            ),
            note=f"{_SECTION_TITLES[section_key]} section remains deterministic.",
        )
        for section_key in IntegratedScientificReportSectionKey
    )
    return sections, sentences


def _validate_scientific_claim_links(
    sentences: tuple[IntegratedScientificReportSentence, ...],
) -> None:
    missing = [
        sentence.sentence_id
        for sentence in sentences
        if sentence.role is IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM
        and not sentence.linked_ids
    ]
    if missing:
        raise ValueError(
            "scientific claim sentences must link to claim ids or evidence card ids: "
            + ", ".join(missing)
        )


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        raise ValueError(f"required integrated-report artifact is missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle, delimiter="\t"))


def _targeted_evidence_card_id(row: dict[str, str]) -> str:
    return f"targeted-evidence-card:{row['candidate_id']}"


__all__ = [
    "IntegratedScientificReport",
    "IntegratedScientificReportArtifactPaths",
    "IntegratedScientificReportSection",
    "IntegratedScientificReportSectionKey",
    "IntegratedScientificReportSentence",
    "IntegratedScientificSentenceRole",
    "IntegratedScientificReportSummary",
    "build_integrated_scientific_report",
    "render_integrated_scientific_report_html",
    "render_integrated_scientific_report_sentences_tsv",
    "render_integrated_scientific_report_summary_tsv",
]
