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

_LAST_REVIEWED_BY_TITLE = {
    "Black-Box Run Verification": "2026-07-01",
    "Raw Versus Import Execution": "2026-07-21",
    "Runtime Artifact Stability": "2026-07-22",
    "Runtime Environment Contracts": "2026-07-22",
    "Runtime Execution Boundary": "2026-07-01",
    "Runtime Replay Challenges": "2026-07-01",
    "Runtime Rerun Refusals": "2026-07-22",
}


def _front_matter(title: str) -> list[str]:
    return [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        f"last_reviewed: {_LAST_REVIEWED_BY_TITLE.get(title, LAST_REVIEWED)}",
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
            "## Independent Review Contract",
            "",
            "- start from the public benchmark manifest, not from runtime prose",
            "- reopen the checked bundle before deciding whether the lane still deserves a",
            "  stronger sentence",
            "- use stage lineage and failure replay to test whether the execution story is",
            "  robust enough to survive scrutiny without maintainer narration",
            "",
            "```mermaid",
            "flowchart LR",
            '    manifest["public package manifest"]',
            '    source["copied-source locator and checksum"]',
            '    request["runtime entrypoint and declared mode"]',
            '    bundle["checked run bundle"]',
            '    lineage["stage lineage"]',
            '    failure["failure replay"]',
            '    comparison["declared comparison verdict"]',
            "    manifest --> source --> request --> bundle",
            "    bundle --> lineage --> comparison",
            "    bundle --> failure --> comparison",
            "```",
            "",
            "A reviewer should be able to resolve every node without private credentials,",
            "undocumented files, or a maintainer choosing which differences to ignore.",
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
    lines.extend(
        [
            "## What This Route Proves And What It Does Not",
            "",
            "- it proves that a reviewer can reopen the shipped runtime lane from named",
            "  public roots",
            "- it does not prove that execution alone upgrades benchmark, grounding,",
            "  recommendation, or lab authority",
            "- it should hand off once the question becomes whether the reopened lane still",
            "  deserves stronger language beyond runtime traceability",
            "",
            "## Rerun Closure Record",
            "",
            "| Record | Closure condition |",
            "| --- | --- |",
            "| package identity | manifest and copied-source checksums resolve to the reviewed public package |",
            "| execution identity | entrypoint, runtime version, mode, provider, and environment contract are recorded |",
            "| run history | state transitions, retries, resume or rehydrate events, and terminal disposition are coherent |",
            "| artifact inventory | required outputs, fingerprints, lineage, and declared absences agree with the lane |",
            "| replay pressure | failure replay and invalidation challenges produce the expected governed verdict |",
            "| comparison | byte, value, review, and permitted-environment differences are classified |",
            "| authority handoff | runtime conclusion and every stronger blocked claim are named separately |",
            "",
            "The rerun closes when these records agree. Similar-looking outputs without a",
            "resolved package, run history, or comparison policy do not close it.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_black_box_run_verification() -> str:
    routes = build_runtime_black_box_verification_routes()
    lines = _front_matter("Black-Box Run Verification")
    lines.extend(
        [
            "# Black-Box Run Verification",
            "",
            "These routes begin from one public benchmark asset and end at one checked runtime bundle, stage lineage artifact, and replay challenge. The route is black-box on purpose: the reader should not need maintainer narration to find the next artifact.",
            "",
            'This page is narrower than the rerun kits. The rerun kits answer "where do I',
            'start for this family?" This page answers "what exact artifact chain proves',
            'that the shipped benchmark packet became the checked runtime story?"',
            "",
            "## What Counts As Verification",
            "",
            "- the benchmark entry artifact fixes the public package boundary",
            "- the source locator manifest proves where the benchmark packet points for its",
            "  runtime-facing inputs",
            "- the checked runtime bundle proves the emitted execution summary that the",
            "  repository currently stands behind",
            "- the stage lineage artifact shows that the run is not only a terminal output",
            "- the replay artifact shows how the same route should fail under hostile",
            "  pressure rather than only how it succeeds",
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
    lines.extend(
        [
            "## What This Route Protects Against",
            "",
            "- claiming that a benchmark package is reviewable when no checked runtime story",
            "  exists",
            "- confusing a successful bundle with an untested replay boundary",
            "- hiding execution lineage behind one terminal artifact",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_raw_versus_import_execution() -> str:
    rows = build_runtime_execution_mode_comparisons()
    lines = _front_matter("Raw Versus Import Execution")
    lines.extend(
        [
            "# Raw Versus Import Execution",
            "",
            "Execution mode states where repository-controlled computation begins. It does not, by itself, establish vendor-native acquisition replay, chromatogram processing, external-engine parity, or scientific authority.",
            "",
            "```mermaid",
            "flowchart LR",
            '    A["vendor or acquisition system"] --> X["exported or derived input"]',
            '    X --> R["repository-controlled runtime lane"]',
            '    R --> B["checked bundle and lineage"]',
            '    B --> C["bounded runtime claim"]',
            '    A -. "not implied by raw_executable" .-> R',
            "```",
            "",
            "## Mode Contract",
            "",
            "| mode | repository guarantee | claim ceiling |",
            "| --- | --- | --- |",
            "| `import_only` | the checked lane begins from imported exported-result evidence | no raw or external-engine rerun claim |",
            "| `raw_executable` | the repository can execute its declared transformation from the checked input level | no automatic vendor-native, acquisition-native, or vendor-parity claim |",
            "",
            "The model field `raw_rerun_supported` distinguishes those two repository modes.",
            "On this page, the clearer reader-facing term is **declared lane executable from",
            "checked input** because the input may already be exported or derived.",
            "",
            "## Family Summary",
            "",
            "| workflow family | current run mode | declared lane executable from checked input | imported dependency count | blocked claim count |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row.workflow_family}` | `{row.current_run_mode.value}` | "
            f"{'yes' if row.raw_rerun_supported else 'no'} | "
            f"`{len(row.imported_dependency_paths)}` | `{len(row.blocked_claims)}` |"
        )
    lines.extend(["", "## Family Boundaries", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family}`",
                "",
                f"- run contract: {row.mode_difference_summary}",
                f"- tracked imported dependencies: {', '.join(f'`{path}`' for path in row.imported_dependency_paths)}",
                f"- blocked claims: {', '.join(row.blocked_claims) if row.blocked_claims else 'none'}",
                f"- public claim ceiling: {row.claim_guard}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation Discipline",
            "",
            "A stronger execution mode changes the runtime statement only. Benchmark",
            "acceptance, grounding, recommendation, and lab consequence remain separately",
            "owned decisions. Imported dependencies stay visible even for `raw_executable`",
            "families so a repository rerun cannot be mistaken for vendor-parity replay.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_runtime_replay_challenges() -> str:
    rows = build_runtime_replay_challenges()
    lines = _front_matter("Runtime Replay Challenges")
    lines.extend(
        [
            "# Runtime Replay Challenges",
            "",
            "Each challenge starts from a clean environment, reopens the tracked benchmark package, and asks the smallest hostile question that should still reconstruct the shipped runtime artifact story.",
            "",
            "These are not full benchmark reruns and they are not broad scientific",
            "acceptance suites. They are disciplined replay pressure. Each challenge asks",
            "whether the runtime lane can re-emit the checked story and whether the failure",
            "surface stays visible when the lane is stressed.",
            "",
            "## What A Successful Replay Proves",
            "",
            "- the reviewer can reopen the shipped public package without hidden local state",
            "- the runtime lane still reconstructs the checked bundle and lineage artifacts",
            "- invalidation is documented as part of the route rather than treated as an",
            "  embarrassing exception",
            "- the family still stops exactly where the current release language says it",
            "  stops",
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
    lines.extend(
        [
            "## Reading Discipline",
            "",
            "- use the clean-environment requirements to avoid false confidence from a dirty",
            "  local workspace",
            "- treat the invalidation cases as part of the proof surface because a replay",
            "  route that only describes success is incomplete",
            "- hand off to environment contracts and artifact stability when the reviewer",
            "  asks whether the same replay should remain stable across repeated runs",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_runtime_environment_contracts() -> str:
    rows = build_runtime_environment_contracts()
    lines = _front_matter("Runtime Environment Contracts")
    lines.extend(
        [
            "# Runtime Environment Contracts",
            "",
            "A runtime environment contract identifies the tools, tracked inputs, and external dependencies required to reopen one shipped lane. Unsupported combinations are present claim refusals, not an informal roadmap.",
            "",
            "```mermaid",
            "flowchart LR",
            '    T["required tools"] --> E["declared environment"]',
            '    I["tracked inputs"] --> E',
            '    D["external dependencies"] --> E',
            '    E --> S["supported combinations"]',
            '    E --> U["unsupported combinations"]',
            "```",
            "",
            "## Qualify an environment",
            "",
            "| Decision | Evidence to inspect | Refusal condition |",
            "| --- | --- | --- |",
            "| identify the lane | workflow family, runtime package ID, execution mode, and benchmark manifest | the request does not match one governed lane |",
            "| resolve required tools | tool name, version, configuration, and availability | a required tool or declared capability is absent |",
            "| bind tracked inputs | source paths, digests, schema identities, and benchmark revision | an input is missing, mutable, or does not match the retained contract |",
            "| disclose external dependencies | imported engine outputs, remote services, credentials, licenses, and network assumptions | an external dependency is implicit or cannot be reconstructed |",
            "| compare the supported envelope | operating system, Python and package versions, extras, providers, and checked combinations | the requested combination lies outside retained evidence |",
            "| execute invalidation cases | unavailable provider, changed input, incompatible schema, missing artifact, and other lane-specific challenges | a challenged condition succeeds silently or produces an ambiguous result |",
            "",
            "## Contract Fields",
            "",
            "| field | interpretation |",
            "| --- | --- |",
            "| required tools | minimum repository-owned execution lane |",
            "| external dependencies | systems or imported evidence outside that lane |",
            "| supported combinations | environment combinations defended by retained evidence |",
            "| unsupported combinations | stronger combinations the current release refuses |",
            "",
            "## Family Contracts",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family}`",
                "",
                f"- runtime package id: `{row.runtime_package_id}`",
                f"- required tools: {', '.join(f'`{tool}`' for tool in row.required_tools)}",
                f"- external dependencies: {', '.join(row.external_dependencies)}",
                f"- supported combinations: {', '.join(row.supported_combinations)}",
                f"- unsupported combinations: {', '.join(row.unsupported_combinations)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Review Rule",
            "",
            "An environment claim may expand only when required tools, external",
            "dependencies, replay evidence, and failure behavior expand together. A green",
            "repository execution lane does not erase the unsupported combinations listed",
            "for that family.",
            "",
            "## Record the qualification",
            "",
            "A reviewable environment decision retains the workflow family, runtime",
            "package ID, request fingerprint, input inventory, required and observed tool",
            "versions, package lock or environment identity, external dependencies,",
            "provider decisions, invalidation results, and final disposition.",
            "",
            "| Disposition | Meaning | Operator response |",
            "| --- | --- | --- |",
            "| qualified | the exact declared combination is backed by retained replay evidence | proceed and bind the environment record to the run |",
            "| degraded | execution is possible but one non-blocking environmental property differs | record the difference and keep claims inside the reviewed envelope |",
            "| unsupported | the combination lies outside the retained contract | refuse the stronger environment claim; select a supported lane or add evidence |",
            "| irreproducible | required inputs, tools, or external dependencies cannot be reconstructed | stop replay and preserve the missing dependency as the blocker |",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_runtime_artifact_stability() -> str:
    rows = build_runtime_artifact_stability_reports()
    lines = _front_matter("Runtime Artifact Stability")
    lines.extend(
        [
            "# Runtime Artifact Stability",
            "",
            "Artifact stability separates exact bytes, semantic values, reviewer interpretation, and permitted environment metadata. Treating all drift alike would either reject harmless run identity changes or conceal meaningful contract movement.",
            "",
            "| stability class | required invariant |",
            "| --- | --- |",
            "| bit stable | governed fixture bytes remain identical |",
            "| value stable | named semantic values retain the same meaning |",
            "| review stable | authorized claim scope and interpretation remain unchanged |",
            "| permitted environment drift | named execution metadata may vary without changing the proof surface |",
            "",
            "```mermaid",
            "flowchart LR",
            '    R["repeated run"] --> B["byte comparison"]',
            '    R --> V["semantic value comparison"]',
            '    R --> Q["review interpretation"]',
            '    R --> E["environment metadata"]',
            '    E --> P["allow only declared drift"]',
            "```",
            "",
            "## Classify Drift Before Comparing Runs",
            "",
            "```mermaid",
            "flowchart TD",
            '    pair["baseline and candidate run bundles"] --> identity{"same package and comparison contract?"}',
            '    identity -->|no| incomparable["incomparable; explain identity mismatch"]',
            '    identity -->|yes| inventory["compare artifact inventories"]',
            '    inventory --> bytes["bit-stable paths"]',
            '    inventory --> values["value-stable fields"]',
            '    inventory --> review["review-stable interpretation"]',
            '    inventory --> environment["declared environment drift"]',
            '    bytes --> verdict{"all differences classified?"}',
            "    values --> verdict",
            "    review --> verdict",
            "    environment --> verdict",
            '    verdict -->|yes| comparable["comparable verdict"]',
            '    verdict -->|no| refused["stability refusal"]',
            "```",
            "",
            "Classification is ordered. Package or contract identity is checked before",
            "bytes; artifact inventory is checked before field values; review meaning is",
            "checked even when the numeric comparison passes. An unclassified difference",
            "is a failed comparison, not permitted drift.",
            "",
            "| Drift example | Class | Required response |",
            "| --- | --- | --- |",
            "| changed governed fixture byte | bit stability | fail until the fixture change and its owner are reviewed |",
            "| reordered representation with unchanged governed value | value stability | prove canonical value equivalence and explain byte drift |",
            "| changed blocker, claim scope, or invalidation reason | review stability | treat as contract movement even if result values match |",
            "| new run ID or artifact directory | permitted environment drift | accept only when explicitly named and non-authoritative |",
            "| missing required artifact | inventory failure | refuse comparison; absence cannot be normalized away |",
            "| new artifact with unknown role | unclassified drift | assign ownership and stability class before acceptance |",
            "",
            "## Family Stability Contracts",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family}`",
                "",
                f"- bit-stable paths: {', '.join(f'`{path}`' for path in row.bit_stable_paths)}",
                f"- value-stable surfaces: {', '.join(row.value_stable_surfaces)}",
                f"- review-stable surfaces: {', '.join(row.review_stable_surfaces)}",
                f"- permitted environment drift: {', '.join(f'`{item}`' for item in row.permitted_environment_drift)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Change Rule",
            "",
            "A bit-stable path changes only through an intentional governed fixture update.",
            "Value-stable or review-stable surfaces change only when the underlying runtime",
            "or scientific boundary changes in the same reviewable edit. Permitted",
            "environment drift never authorizes a claim, blocker, or lineage change.",
            "",
            "Stable execution protects rerun honesty; it does not enlarge biological,",
            "analytical, vendor-parity, recommendation, or lab authority.",
            "",
            "A stability verdict must retain both run identities, the comparison contract,",
            "artifact inventories, classified differences, comparison-tool identity, and",
            "the final disposition. A bare “same” or “changed” result is not reviewable.",
            "",
            "## Minimum comparison record",
            "",
            "| Record field | Why it is required |",
            "| --- | --- |",
            "| baseline and candidate identities | prevents comparison against the wrong run or contract |",
            "| artifact inventories | exposes missing, added, and role-changed outputs before value comparison |",
            "| stability policy revision | fixes which paths, fields, meanings, and environment values were governed |",
            "| classified differences | separates byte, value, review, permitted-environment, and unresolved drift |",
            "| comparator identity and tolerances | makes numeric and semantic equivalence reproducible |",
            "| disposition and authority | records who accepted, refused, or escalated the comparison and why |",
            "",
            "Comparison is refused when either run identity is unresolved, a required",
            "artifact is absent, a governed difference has no class, or review meaning",
            "moves without an explicit contract decision. Permitted environment drift",
            "never absorbs a changed result, blocker, or claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_runtime_rerun_refusals() -> str:
    rows = build_runtime_rerun_refusals()
    lines = _front_matter("Runtime Rerun Refusals")
    lines.extend(
        [
            "# Runtime Rerun Refusals",
            "",
            "A rerun refusal is a positive runtime decision: the retained environment,",
            "inputs, provider boundary, artifacts, or downstream evidence do not support",
            "the requested replay claim. The refusal preserves the best supported lane",
            "without describing a weaker reconstruction as faithful execution.",
            "",
            "```mermaid",
            "flowchart TD",
            '    request["requested rerun claim"] --> lane{"governed lane exists?"}',
            '    lane -->|no| refuse["refuse and name missing lane"]',
            '    lane -->|yes| environment{"environment and inputs reconstructable?"}',
            "    environment -->|no| refuse",
            '    environment -->|yes| replay{"artifacts and invalidation cases pass?"}',
            "    replay -->|no| refuse",
            '    replay -->|yes| scope{"claim inside current evidence ceiling?"}',
            '    scope -->|no| narrow["complete replay; narrow the claim"]',
            '    scope -->|yes| accept["record rerun-ready disposition"]',
            "```",
            "",
            "## Current family posture",
            "",
            "| Family | Rerun ready | Present refusal | Blocked claim |",
            "| --- | --- | --- | --- |",
            "",
        ]
    )
    for row in rows:
        lines.append(
            f"| `{row.workflow_family}` | `{'yes' if row.rerun_ready else 'no'}` | "
            f"{'; '.join(row.refusal_reasons) if row.refusal_reasons else 'none'} | "
            f"{'; '.join(row.blocked_claims) if row.blocked_claims else 'none'} |"
        )
    lines.extend(
        [
            "",
            "Rerun-ready means the checked Runtime lane can be reopened under its named",
            "contract. It does not establish raw-vendor parity, scientific transfer,",
            "decision validity, or laboratory consequence beyond that contract.",
            "",
            "## Family evidence",
            "",
        ]
    )
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family}`",
                "",
                f"- rerun ready: `{'yes' if row.rerun_ready else 'no'}`",
                f"- refusal reasons: {', '.join(row.refusal_reasons) if row.refusal_reasons else 'none'}",
                f"- blocked claims: {', '.join(row.blocked_claims) if row.blocked_claims else 'none'}",
                f"- next evidence paths: {', '.join(f'`{path}`' for path in row.next_evidence_paths)}",
                f"- note: {row.note}",
                "",
            ]
        )
    lines.extend(
        [
            "## Close or preserve a refusal",
            "",
            "| Refusal source | Evidence required before reconsideration |",
            "| --- | --- |",
            "| no repository-owned lane | implementation, public entrypoint, retained fixtures, negative paths, and ownership review |",
            "| imported or proprietary upstream step | governed source custody plus executable or independently comparable upstream evidence |",
            "| missing environment or tool | versioned environment contract and clean-environment replay |",
            "| unstable or incomplete artifacts | complete inventory, stability classification, and successful invalidation challenges |",
            "| claim exceeds Runtime authority | scientific, Knowledge, Intelligence, or Lab evidence from the responsible owner |",
            "",
            "A refusal is superseded only by a new record that cites the prior refusal,",
            "identifies the added evidence, replays the negative path, and states the new",
            "claim ceiling. Until then, operators preserve the refusal and use the",
            "strongest supported lane rather than narrating around the missing proof.",
        ]
    )
    return "\n".join(lines) + "\n"


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
