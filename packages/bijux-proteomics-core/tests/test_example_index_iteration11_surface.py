# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus_iteration11 import (
    ScientificQuestionExampleIndexEntry,
    build_example_index_by_scientific_question,
)


def test_build_example_index_by_scientific_question_sorts_by_question_and_workflow() -> (
    None
):
    index = build_example_index_by_scientific_question(
        (
            ScientificQuestionExampleIndexEntry(
                question="which proteins differ by treatment",
                input_type="lfq_matrix",
                workflow="lfq_da",
                output_artifact="outputs/da.json",
                evidence_grade="moderate",
                caveats=("small cohort",),
            ),
            ScientificQuestionExampleIndexEntry(
                question="is phosphosite S123 condition-enriched",
                input_type="ptm_site_table",
                workflow="ptm_validation",
                output_artifact="outputs/ptm_review.json",
                evidence_grade="high",
                caveats=("site ambiguity in 1 run",),
            ),
        )
    )

    assert index.entries[0].question.startswith("is phosphosite")
    assert index.entries[1].workflow == "lfq_da"
