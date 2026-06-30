# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
MANAGED_FINAL_ROW_OWNERS = (
    ("workflow/cards/protein_evidence_cards.py", ("graph_source_row_refs",)),
    (
        "workflow/cards/protein_mechanism_cards.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
    (
        "review/claims/biological_claim_validation.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
    (
        "ptm/cards/evidence_cards.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
    (
        "workflow/cards/mechanisms.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
    (
        "workflow/cards/cross_study_evidence_cards.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
    (
        "io/raw/raw_signal_evidence_cards.py",
        ("source_row_refs", "derived_no_source_reason", "SourceRowLineage"),
    ),
)


def _string_constants(tree: ast.AST) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _name_references(tree: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def test_final_row_owners_expose_source_row_lineage_fields() -> None:
    offenders: list[str] = []

    for relative_path, required_tokens in MANAGED_FINAL_ROW_OWNERS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        names = _name_references(tree)
        constants = _string_constants(tree)
        available_tokens = names | constants
        for token in required_tokens:
            if token not in available_tokens:
                offenders.append(f"{relative_path} missing {token}")

    assert not offenders, (
        "final scientific output owners must preserve source-row lineage tokens: "
        + ", ".join(offenders)
    )
