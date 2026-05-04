# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus import (
    ExternalEngineCorpusLicensingEntry,
    ExternalEngineCorpusPolicy,
    build_external_engine_corpus_licensing_plan,
)


def test_build_external_engine_corpus_licensing_plan_sorts_unique_artifact_classes() -> (
    None
):
    plan = build_external_engine_corpus_licensing_plan(
        (
            ExternalEngineCorpusLicensingEntry(
                artifact_class="engine_binary",
                policy=ExternalEngineCorpusPolicy.REFERENCE,
                rationale="binary redistribution is restricted",
                follow_up_action="link vendor download and version checksum",
            ),
            ExternalEngineCorpusLicensingEntry(
                artifact_class="search_result_table",
                policy=ExternalEngineCorpusPolicy.USER_SUPPLIED,
                rationale="result export license varies by provider",
                follow_up_action="accept user-provided exports only",
            ),
        )
    )

    assert plan.entries[0].artifact_class == "engine_binary"
    assert plan.entries[1].policy.value == "user_supplied"
