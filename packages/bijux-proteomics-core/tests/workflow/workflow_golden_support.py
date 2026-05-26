# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import difflib
import json
from pathlib import Path

WORKFLOW_GOLDEN_ROOT = (
    Path(__file__).resolve().parent.parent / "fixtures" / "workflow_goldens"
)

WORKFLOW_GOLDEN_TARGETS: dict[str, tuple[str, ...]] = {
    "advanced_diann": (
        "manifest.json",
        "advanced_diann_summary.tsv",
        "advanced_diann_accepted_proteins.tsv",
        "rejected_evidence.tsv",
    ),
    "advanced_maxquant": (
        "manifest.json",
        "advanced_maxquant_summary.tsv",
        "advanced_maxquant_excluded_protein_groups.tsv",
        "advanced_maxquant_peptide_contributions.tsv",
    ),
    "advanced_fragpipe": (
        "manifest.json",
        "advanced_fragpipe_summary.tsv",
        "advanced_fragpipe_protein_group_discrepancies.tsv",
        "advanced_fragpipe_peptide_evidence.tsv",
    ),
    "advanced_ptm": (
        "manifest.json",
        "advanced_ptm_summary.tsv",
        "ptm_site_quant_matrix.tsv",
        "advanced_ptm_excluded_ambiguous_sites.tsv",
    ),
    "advanced_tmt": (
        "manifest.json",
        "advanced_tmt_summary.tsv",
        "advanced_tmt_peptide_confidence.tsv",
        "advanced_tmt_evidence_cards.tsv",
    ),
    "advanced_targeted": (
        "manifest.json",
        "advanced_targeted_summary.tsv",
        "targeted_validation_confirmed.tsv",
        "advanced_targeted_evidence_cards.tsv",
    ),
}


def golden_fixture_dir(workflow_name: str) -> Path:
    return WORKFLOW_GOLDEN_ROOT / workflow_name


def assert_workflow_golden_outputs_match(workflow_name: str, output_dir: Path) -> None:
    fixture_dir = golden_fixture_dir(workflow_name)
    for file_name in WORKFLOW_GOLDEN_TARGETS[workflow_name]:
        expected_path = fixture_dir / file_name
        actual_path = output_dir / file_name
        assert expected_path.exists(), f"Missing golden fixture {expected_path}"
        assert actual_path.exists(), f"Missing generated output {actual_path}"
        if expected_path.suffix == ".json":
            _assert_json_matches(expected_path, actual_path, workflow_name)
            continue
        _assert_text_matches(expected_path, actual_path)


def _assert_json_matches(expected_path: Path, actual_path: Path, workflow_name: str) -> None:
    expected_payload = _reduce_manifest_payload(
        json.loads(expected_path.read_text(encoding="utf-8")),
        workflow_name,
    )
    actual_payload = _reduce_manifest_payload(
        json.loads(actual_path.read_text(encoding="utf-8")),
        workflow_name,
    )
    if actual_payload == expected_payload:
        return
    expected_text = json.dumps(expected_payload, indent=2, sort_keys=True) + "\n"
    actual_text = json.dumps(actual_payload, indent=2, sort_keys=True) + "\n"
    raise AssertionError(_render_diff(expected_path.name, expected_text, actual_text))


def _assert_text_matches(expected_path: Path, actual_path: Path) -> None:
    expected_text = expected_path.read_text(encoding="utf-8")
    actual_text = actual_path.read_text(encoding="utf-8")
    if actual_text == expected_text:
        return
    raise AssertionError(_render_diff(expected_path.name, expected_text, actual_text))


def _render_diff(file_name: str, expected_text: str, actual_text: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            expected_text.splitlines(),
            actual_text.splitlines(),
            fromfile=f"{file_name}:expected",
            tofile=f"{file_name}:actual",
            lineterm="",
        )
    )


def _reduce_manifest_payload(payload: object, workflow_name: str) -> object:
    if not isinstance(payload, dict) or "artifacts" not in payload:
        return payload
    tracked_file_names = set(WORKFLOW_GOLDEN_TARGETS[workflow_name]) - {"manifest.json"}
    reduced_artifacts = [
        artifact
        for artifact in payload["artifacts"]
        if isinstance(artifact, dict)
        and artifact.get("legacy_relative_path") in tracked_file_names
    ]
    return {
        "manifest_schema_version": payload.get("manifest_schema_version"),
        "layout_name": payload.get("layout_name"),
        "producer_function": payload.get("producer_function"),
        "folder_names": payload.get("folder_names"),
        "artifacts": reduced_artifacts,
    }
