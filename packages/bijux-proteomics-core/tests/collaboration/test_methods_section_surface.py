# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    MethodsSectionInput,
    generate_methods_section_from_workflow_evidence,
)


def test_generate_methods_section_from_workflow_evidence_embeds_references() -> None:
    document = generate_methods_section_from_workflow_evidence(
        MethodsSectionInput(
            title="Proteomics Methods",
            workflow_steps=("import", "normalize", "review"),
            evidence_refs=("ev-11", "ev-12"),
            software_versions=("bijux-proteomics-core@1.0.0",),
        )
    )

    assert "ev-11" in document.body
    assert "import; normalize; review" in document.body
