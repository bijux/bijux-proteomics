# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_proteomics.workflow import (
    IntegratedScientificReportSectionKey,
    IntegratedScientificSentenceRole,
    build_integrated_scientific_report,
    render_integrated_scientific_report_sentences_tsv,
)


def test_build_integrated_scientific_report_preserves_required_sections_and_links(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "integrated_demo_report"
    report = build_integrated_scientific_report(output_dir)

    assert {section.section_key for section in report.sections} == set(
        IntegratedScientificReportSectionKey
    )
    assert report.summary.section_count == len(IntegratedScientificReportSectionKey)
    assert report.summary.scientific_claim_count >= 1
    assert (
        report.summary.scientific_claim_count
        == report.summary.linked_scientific_claim_count
    )

    scientific_claim_sentences = tuple(
        sentence
        for sentence in report.sentences
        if sentence.role is IntegratedScientificSentenceRole.SCIENTIFIC_CLAIM
    )
    assert scientific_claim_sentences
    assert all(sentence.linked_ids for sentence in scientific_claim_sentences)

    sentence_by_id = {sentence.sentence_id: sentence for sentence in report.sentences}
    accepted_sentence = sentence_by_id["accepted-results-1"]
    belief_sentence = sentence_by_id["belief-audit-1"]
    targeted_quality_sentence = sentence_by_id["data-quality-2"]
    experiment_design_sentence = sentence_by_id["experiment-design-1"]

    assert any(
        linked_id.startswith("protein-claim:")
        for linked_id in accepted_sentence.linked_ids
    )
    assert any(
        linked_id.startswith("protein-claim:")
        for linked_id in belief_sentence.linked_ids
    )
    assert targeted_quality_sentence.linked_ids == (
        "targeted-evidence-card:protein:P001",
    )
    assert any(
        row_ref.startswith("study_design:")
        for row_ref in experiment_design_sentence.source_row_refs
    )

    html = (output_dir / report.artifacts.report_html).read_text(encoding="utf-8")
    for title in (
        "Experiment Design",
        "Data Quality",
        "Accepted Results",
        "Downgraded Results",
        "Refused Claims",
        "PTM Evidence",
        "Mechanisms",
        "Validation Candidates",
        "Belief Audit",
    ):
        assert title in html

    sentence_tsv = render_integrated_scientific_report_sentences_tsv(report)
    assert "linked_ids" in sentence_tsv
    assert "scientific_claim" in sentence_tsv
    assert (output_dir / report.artifacts.summary_tsv).exists()
    assert (output_dir / report.artifacts.sentences_tsv).exists()
    assert (output_dir / report.artifacts.report_html).exists()
    assert (output_dir / report.artifacts.report_json).exists()


def test_build_integrated_scientific_report_rejects_top_claim_without_belief_audit(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "integrated_demo_report_invalid_belief_audit"
    report = build_integrated_scientific_report(output_dir)
    payload = json.loads(
        (output_dir / report.source_report_json).read_text(encoding="utf-8")
    )
    top_claim_id = payload["intelligence_report_contract"]["belief_audit_report"][
        "summary"
    ]["top_claim_ids"][0]

    for claim_entry in payload["intelligence_report_contract"]["claim_entries"]:
        if claim_entry["claim"]["claim_id"] == top_claim_id:
            claim_entry["belief_audit"] = None
            break
    else:
        raise AssertionError(f"top claim {top_claim_id} was not present in the report")

    (output_dir / report.source_report_json).write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=f"missing belief audit for top claim {top_claim_id}",
    ):
        build_integrated_scientific_report(output_dir)
