# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "bijux_proteomics"
MANAGED_SEMANTIC_ID_OWNERS = (
    (
        "ptm/cards/evidence_cards.py",
        ("build_ptm_card_id", "build_ptm_claim_id", "build_site_id"),
        ("ptm-card:", "ptm-claim:"),
    ),
    (
        "workflow/cards/protein_evidence_cards.py",
        ("build_protein_card_id",),
        ("protein-card:",),
    ),
    (
        "workflow/cards/protein_mechanism_cards.py",
        ("build_protein_mechanism_card_id",),
        ("protein-mechanism-card:",),
    ),
    (
        "workflow/reports/biological_report_claims.py",
        (
            "build_protein_claim_id",
            "build_pathway_claim_id",
            "build_regulator_claim_id",
        ),
        ("protein-claim:", "pathway-claim:", "regulator-claim:"),
    ),
    (
        "interfaces/support/biomarker_candidate_support/biological_candidates.py",
        ("build_protein_id",),
        (),
    ),
    (
        "interfaces/support/biomarker_candidate_support/ptm_candidates.py",
        ("build_site_id",),
        (),
    ),
    (
        "quantification/contracts/matrix_models.py",
        ("build_matrix_id",),
        ("matrix:",),
    ),
    (
        "quantification/contracts/matrix_building.py",
        ("build_matrix_id",),
        ("matrix:",),
    ),
    (
        "quantification/normalization/imputation.py",
        ("build_matrix_id",),
        ("matrix:",),
    ),
    (
        "workflow/exports/artifact_layout.py",
        ("build_artifact_id",),
        ("artifact:",),
    ),
    (
        "workflow/mechanisms.py",
        ("build_mechanism_card_id",),
        (
            "pathway-shift-",
            "kinase-candidate-",
            "complex-change-",
            "compartment-signal-",
            "biomarker-candidate-",
        ),
    ),
    (
        "workflow/cards/cross_study_evidence_cards.py",
        ("build_cross_study_card_id",),
        (),
    ),
    (
        "io/raw/raw_signal_evidence_cards.py",
        ("build_raw_signal_card_id",),
        ("raw_signal_card:",),
    ),
)


def _calls_function(tree: ast.AST, function_name: str) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == function_name:
            return True
    return False


def test_managed_output_owners_route_ids_through_semantic_id_builders() -> None:
    offenders: list[str] = []

    for relative_path, required_builders, _ in MANAGED_SEMANTIC_ID_OWNERS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        for builder_name in required_builders:
            if not _calls_function(tree, builder_name):
                offenders.append(f"{relative_path} missing {builder_name}")

    assert not offenders, (
        "managed output owners must call canonical semantic id builders: "
        + ", ".join(offenders)
    )


def test_managed_output_owners_do_not_inline_semantic_id_namespaces() -> None:
    offenders: list[str] = []

    for relative_path, _, forbidden_prefixes in MANAGED_SEMANTIC_ID_OWNERS:
        tree = ast.parse((SOURCE_ROOT / relative_path).read_text(encoding="utf-8"))
        for forbidden_prefix in forbidden_prefixes:
            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant):
                    continue
                if not isinstance(node.value, str):
                    continue
                if forbidden_prefix in node.value:
                    offenders.append(f"{relative_path} embeds {forbidden_prefix!r}")
                    break

    assert not offenders, (
        "managed output owners must not assemble semantic id prefixes inline: "
        + ", ".join(offenders)
    )
