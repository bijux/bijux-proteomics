# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated runtime handbook pages for black-box reproducibility."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    LAST_REVIEWED,
    RUNTIME_DIR,
)
from bijux_proteomics_runtime.workflows.black_box_reproducibility import (
    build_runtime_artifact_stability_reports,
    build_runtime_black_box_verification_routes,
    build_runtime_environment_contracts,
    build_runtime_execution_mode_comparisons,
    build_runtime_replay_challenges,
    build_runtime_rerun_refusals,
)

__all__ = [
    "BLACK_BOX_RUN_VERIFICATION_PATH",
    "RAW_VERSUS_IMPORT_EXECUTION_PATH",
    "RUNTIME_ARTIFACT_STABILITY_PATH",
    "RUNTIME_ENVIRONMENT_CONTRACTS_PATH",
    "RUNTIME_EXECUTION_BOUNDARY_PATH",
    "RUNTIME_REPLAY_CHALLENGES_PATH",
    "RUNTIME_RERUN_REFUSALS_PATH",
    "run",
]


RUNTIME_EXECUTION_BOUNDARY_PATH = RUNTIME_DIR / "runtime-execution-boundary.md"
BLACK_BOX_RUN_VERIFICATION_PATH = RUNTIME_DIR / "black-box-run-verification.md"
RAW_VERSUS_IMPORT_EXECUTION_PATH = RUNTIME_DIR / "raw-versus-import-execution.md"
RUNTIME_REPLAY_CHALLENGES_PATH = RUNTIME_DIR / "runtime-replay-challenges.md"
RUNTIME_ENVIRONMENT_CONTRACTS_PATH = RUNTIME_DIR / "runtime-environment-contracts.md"
RUNTIME_ARTIFACT_STABILITY_PATH = RUNTIME_DIR / "runtime-artifact-stability.md"
RUNTIME_RERUN_REFUSALS_PATH = RUNTIME_DIR / "runtime-rerun-refusals.md"


def _front_matter(title: str) -> list[str]:
    return [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
    ]


def _render_execution_boundary() -> str:
    routes = {
        route.workflow_family: route
        for route in build_runtime_black_box_verification_routes()
    }
    challenges = {row.workflow_family: row for row in build_runtime_replay_challenges()}
    refusals = {row.workflow_family: row for row in build_runtime_rerun_refusals()}
    lines = _front_matter("Runtime Execution Boundary")
    lines.extend(
        [
            "# Runtime Execution Boundary",
            "",
            "Start here when the question is: how would an independent reviewer reopen a shipped workflow family without asking maintainers what to trust next?",
            "",
            "## Shortest Rerun Route",
            "",
            "| workflow family | start from | runtime entrypoint | checked bundle | current limit |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for workflow_family in routes:
        route = routes[workflow_family]
        challenge = challenges[workflow_family]
        lines.append(
            f"| `{workflow_family}` | `{route.benchmark_entry_artifact_path}` | "
            f"`{route.canonical_entrypoint}` | `{route.runtime_bundle_artifact_path}` | "
            f"{challenge.current_limit} |"
        )
    lines.extend(
        [
            "",
            "## What To Open Next",
            "",
        ]
    )
    for workflow_family in routes:
        route = routes[workflow_family]
        refusal = refusals[workflow_family]
        lines.extend(
            [
                f"### `{workflow_family}`",
                "",
                f"- start from the public benchmark manifest: `{route.benchmark_entry_artifact_path}`",
                f"- confirm copied-source scope in: `{route.benchmark_source_manifest_path}`",
                f"- reopen the checked runtime bundle: `{route.runtime_bundle_artifact_path}`",
                f"- challenge stage-to-stage continuity with: `{route.stage_lineage_artifact_path}`",
                f"- challenge replay and invalidation with: `{route.replay_artifact_path}`",
                f"- rerun refusal summary: {', '.join(refusal.refusal_reasons) if refusal.refusal_reasons else 'none'}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_black_box_run_verification() -> str:
    routes = build_runtime_black_box_verification_routes()
    lines = _front_matter("Black-Box Run Verification")
    lines.extend(
        [
            "# Black-Box Run Verification",
            "",
            "These routes begin from one public benchmark asset and end at one checked runtime bundle, stage lineage artifact, and replay challenge. The route is black-box on purpose: the reader should not need maintainer narration to find the next artifact.",
            "",
        ]
    )
    for route in routes:
        lines.extend(
            [
                f"## `{route.workflow_family}`",
                "",
                f"- benchmark entry artifact: `{route.benchmark_entry_artifact_path}`",
                f"- source locator manifest: `{route.benchmark_source_manifest_path}`",
                f"- runtime package id: `{route.runtime_package_id}`",
                f"- runtime entrypoint: `{route.canonical_entrypoint}`",
                f"- run mode: `{route.run_mode.value}`",
                f"- checked runtime bundle: `{route.runtime_bundle_artifact_path}`",
                f"- stage lineage artifact: `{route.stage_lineage_artifact_path}`",
                f"- replay artifact: `{route.replay_artifact_path}`",
                f"- validating tests: {', '.join(f'`{path}`' for path in route.validating_test_paths)}",
                f"- note: {route.note}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_raw_versus_import_execution() -> str:
    rows = build_runtime_execution_mode_comparisons()
    lines = _front_matter("Raw Versus Import Execution")
    lines.extend(
        [
            "# Raw Versus Import Execution",
            "",
            "This page makes the execution-mode boundary explicit for each flagship workflow family. It exists to stop import-backed or library-conditioned lanes from quietly inheriting stronger raw-rerun language.",
            "",
            "| workflow family | current run mode | raw rerun supported | imported dependency count |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row.workflow_family}` | `{row.current_run_mode.value}` | "
            f"{'yes' if row.raw_rerun_supported else 'no'} | `{len(row.imported_dependency_paths)}` |"
        )
    lines.extend(["", "## Family Boundaries", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family}`",
                "",
                f"- mode difference: {row.mode_difference_summary}",
                f"- imported dependencies: {', '.join(f'`{path}`' for path in row.imported_dependency_paths)}",
                f"- blocked claims: {', '.join(row.blocked_claims) if row.blocked_claims else 'none'}",
                f"- claim guard: {row.claim_guard}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_runtime_replay_challenges() -> str:
    rows = build_runtime_replay_challenges()
    lines = _front_matter("Runtime Replay Challenges")
    lines.extend(
        [
            "# Runtime Replay Challenges",
            "",
            "Each challenge starts from a clean environment, reopens the tracked benchmark package, and asks the smallest hostile question that should still reconstruct the shipped runtime artifact story.",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"## `{row.workflow_family}`",
                "",
                "Clean-environment requirements:",
                "",
            ]
        )
        for requirement in row.clean_environment_requirements:
            lines.append(f"- {requirement}")
        lines.extend(["", "Minimal steps:", ""])
        for step in row.minimal_steps:
            lines.append(f"- {step}")
        lines.extend(
            [
                "",
                f"- expected artifacts: {', '.join(f'`{path}`' for path in row.expected_artifact_paths)}",
                f"- invalidation cases: {', '.join(f'`{case}`' for case in row.invalidation_cases)}",
                f"- current limit: {row.current_limit}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_runtime_environment_contracts() -> str:
    rows = build_runtime_environment_contracts()
    lines = _front_matter("Runtime Environment Contracts")
    lines.extend(
        [
            "# Runtime Environment Contracts",
            "",
            "These contracts record the supported and unsupported environment combinations for each flagship workflow family so runtime claims do not quietly expand beyond the shipped lane.",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"## `{row.workflow_family}`",
                "",
                f"- runtime package id: `{row.runtime_package_id}`",
                f"- required tools: {', '.join(f'`{tool}`' for tool in row.required_tools)}",
                f"- external dependencies: {', '.join(row.external_dependencies)}",
                f"- supported combinations: {', '.join(row.supported_combinations)}",
                f"- unsupported combinations: {', '.join(row.unsupported_combinations)}",
                f"- note: {row.note}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_runtime_artifact_stability() -> str:
    rows = build_runtime_artifact_stability_reports()
    lines = _front_matter("Runtime Artifact Stability")
    lines.extend(
        [
            "# Runtime Artifact Stability",
            "",
            "This page states what must remain bit-stable, value-stable, or review-stable across repeated flagship reruns. It also names the environment-bound drift that is allowed without pretending the rerun changed meaningfully.",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"## `{row.workflow_family}`",
                "",
                f"- bit-stable paths: {', '.join(f'`{path}`' for path in row.bit_stable_paths)}",
                f"- value-stable surfaces: {', '.join(row.value_stable_surfaces)}",
                f"- review-stable surfaces: {', '.join(row.review_stable_surfaces)}",
                f"- permitted environment drift: {', '.join(f'`{item}`' for item in row.permitted_environment_drift)}",
                f"- note: {row.note}",
                "",
            ]
        )
    return "\n".join(lines)


def _render_runtime_rerun_refusals() -> str:
    rows = build_runtime_rerun_refusals()
    lines = _front_matter("Runtime Rerun Refusals")
    lines.extend(
        [
            "# Runtime Rerun Refusals",
            "",
            "This ledger records when a nominal workflow family still cannot be rerun more faithfully because the repository stops at imported exports, proprietary steps, missing vendor-native inputs, or stronger consequence gaps.",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"## `{row.workflow_family}`",
                "",
                f"- rerun ready: `{'yes' if row.rerun_ready else 'no'}`",
                f"- refusal reasons: {', '.join(row.refusal_reasons) if row.refusal_reasons else 'none'}",
                f"- blocked claims: {', '.join(row.blocked_claims) if row.blocked_claims else 'none'}",
                f"- next evidence paths: {', '.join(f'`{path}`' for path in row.next_evidence_paths)}",
                f"- note: {row.note}",
                "",
            ]
        )
    return "\n".join(lines)


def _expected_outputs() -> dict[Path, str]:
    return {
        RUNTIME_EXECUTION_BOUNDARY_PATH: _render_execution_boundary(),
        BLACK_BOX_RUN_VERIFICATION_PATH: _render_black_box_run_verification(),
        RAW_VERSUS_IMPORT_EXECUTION_PATH: _render_raw_versus_import_execution(),
        RUNTIME_REPLAY_CHALLENGES_PATH: _render_runtime_replay_challenges(),
        RUNTIME_ENVIRONMENT_CONTRACTS_PATH: _render_runtime_environment_contracts(),
        RUNTIME_ARTIFACT_STABILITY_PATH: _render_runtime_artifact_stability(),
        RUNTIME_RERUN_REFUSALS_PATH: _render_runtime_rerun_refusals(),
    }


def run(check: bool = False) -> int:
    outputs = _expected_outputs()
    if check:
        for path, content in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                print(f"runtime black-box docs are stale: {path}")
                return 1
        print("runtime black-box docs are up to date")
        return 0
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("generated runtime black-box docs")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if docs are stale")
    return parser


def main() -> int:
    args = _parser().parse_args()
    return run(check=args.check)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
