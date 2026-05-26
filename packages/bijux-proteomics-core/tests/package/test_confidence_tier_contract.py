# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / "bijux_proteomics"
CANONICAL_OWNER = SOURCE_ROOT / "domain" / "confidence.py"
IDENTIFICATION_LABEL_OWNER = SOURCE_ROOT / "identification" / "contracts" / "confidence.py"
ALIAS_OWNERS = {
    "review/evidence_graph/evidence_graph_confidence.py": "EvidenceGraphConfidenceTier",
    "review/claims/biological_hypotheses.py": "BiologicalHypothesisConfidenceTier",
    "study/design/experiment_confidence.py": "ExperimentConfidenceTier",
    "interpretation/pathway_activity.py": "PathwayActivityConfidenceStatus",
    "interpretation/protein_set_scoring.py": "ProteinSetScoreConfidenceStatus",
    "interpretation/disease_phenotype_interpretation.py": "DiseasePhenotypeConfidenceStatus",
    "interpretation/complex_activity.py": "ComplexActivityConfidenceStatus",
    "io/raw/run_qc.py": "SpectrumQualityTier",
    "study/metadata/sample_sheet_repairs.py": "SampleSheetRepairConfidence",
    "workflow/mechanisms.py": "MechanismCardConfidence",
}
GENERIC_CONFIDENCE_VALUES = {
    "high",
    "moderate",
    "low",
    "medium",
    "high_confidence",
    "moderate_confidence",
    "low_confidence",
    "rejected",
    "decoy",
}


def _assigned_string_values(node: ast.ClassDef) -> set[str]:
    values: set[str] = set()
    for statement in node.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        value_node = statement.value
        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            values.add(value_node.value)
    return values


def test_canonical_confidence_tier_owner_defines_shared_values() -> None:
    source_text = CANONICAL_OWNER.read_text(encoding="utf-8")

    assert 'HIGH = "high"' in source_text
    assert 'MODERATE = "moderate"' in source_text
    assert 'LOW = "low"' in source_text
    assert 'MEDIUM = "moderate"' in source_text
    assert 'HIGH_CONFIDENCE = "high"' in source_text
    assert 'MODERATE_CONFIDENCE = "moderate"' in source_text
    assert 'LOW_CONFIDENCE = "low"' in source_text


def test_generic_confidence_alias_owners_route_through_shared_tier() -> None:
    offenders: list[str] = []

    for relative_path, alias_name in ALIAS_OWNERS.items():
        source_text = (SOURCE_ROOT / relative_path).read_text(encoding="utf-8")
        if f"{alias_name} = ConfidenceTier" not in source_text:
            offenders.append(relative_path)

    assert offenders == []


def test_no_other_owner_defines_incompatible_generic_confidence_tiers() -> None:
    offenders: list[str] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        relative_path = path.relative_to(SOURCE_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith(
                ("ConfidenceTier", "ConfidenceLabel", "ConfidenceStatus", "Confidence")
            ):
                continue
            values = _assigned_string_values(node)
            if not values or not values.issubset(GENERIC_CONFIDENCE_VALUES):
                continue
            if relative_path in {
                "domain/confidence.py",
                "identification/contracts/confidence.py",
            }:
                continue
            offenders.append(f"{relative_path}:{node.name}")

    assert offenders == []


def test_biological_report_summary_uses_shared_experiment_confidence_tier() -> None:
    source_text = (
        SOURCE_ROOT / "workflow" / "reports" / "biological_report_models.py"
    ).read_text(encoding="utf-8")

    assert "experiment_confidence_tier: ConfidenceTier" in source_text


def test_identification_confidence_labels_use_canonical_moderate_value() -> None:
    source_text = IDENTIFICATION_LABEL_OWNER.read_text(encoding="utf-8")

    assert "MODERATE = ConfidenceTier.MODERATE.value" in source_text
    assert "MEDIUM = ConfidenceTier.MODERATE.value" in source_text


def test_shared_confidence_tier_owner_normalizes_legacy_labels() -> None:
    source_text = CANONICAL_OWNER.read_text(encoding="utf-8")

    assert 'if normalized in {"high", "high_confidence"}:' in source_text
    assert 'if normalized in {"moderate", "moderate_confidence", "medium"}:' in source_text
    assert 'if normalized in {"low", "low_confidence"}:' in source_text
