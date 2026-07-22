# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated shared docs for workflow consequence coherence."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    LAST_REVIEWED,
)
from bijux_proteomics_dev.release.governance.workflow_consequence_chain import (
    LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH,
    LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH,
    RECOMMENDATION_CHANGE_PATH,
    WORKFLOW_CONSEQUENCE_MAPS_PATH,
    WorkflowConsequenceMap,
    WorkflowOutcomeLearningLoop,
    WorkflowRecommendationChange,
    WorkflowRefusalGuidance,
    build_workflow_consequence_maps,
    build_workflow_outcome_learning_loops,
    build_workflow_recommendation_changes,
    build_workflow_refusal_guidance_family,
)

__all__ = [
    "LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH",
    "LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH",
    "RECOMMENDATION_CHANGE_PATH",
    "WORKFLOW_CONSEQUENCE_MAPS_PATH",
    "run",
]


def _front_matter(*, title: str, owner: str) -> list[str]:
    return [
        "---",
        f"title: {title}",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        f"owner: {owner}",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
    ]


def _render_strength_line(entry: WorkflowConsequenceMap) -> list[str]:
    return [
        f"- knowledge posture: `{entry.knowledge_strength.value}`",
        f"- recommendation posture: `{entry.intelligence_strength.value}`",
        f"- lab posture: `{entry.lab_strength.value}`",
        f"- current strongest allowed posture: `{entry.weakest_allowed_strength.value}`",
        "- decision-grade remains blocked when the weakest downstream boundary stays below a full recommendation.",
    ]


def _render_consequence_maps() -> str:
    rows = build_workflow_consequence_maps()
    lines = _front_matter(
        title="Workflow Consequence Maps",
        owner="bijux-proteomics-docs",
    )
    lines.extend(
        [
            "# Workflow Consequence Maps",
            "",
            "Each workflow family starts from contradiction pressure, passes through a recommendation posture, and ends at assay burden and the cost of being wrong.",
            "",
            "The value of this page is that it keeps the repository from pretending those three layers are interchangeable. A workflow family can have a strong benchmark packet, a convincing rerun lane, and still stop at a weaker public sentence because the downstream cost of being wrong remains too high.",
            "",
            "## Consequence Rule",
            "",
            "- These are not vote tallies. The weakest downstream boundary controls the strongest honest public sentence.",
            "- A family can look benchmark-strong and still remain recommendation-bounded once comparator pressure, assay burden, or follow-up failure stays unresolved.",
            "- Use the family map to identify the contradiction, control demand, or consequence cost that enforces the downgrade.",
            "",
            "```mermaid",
            "flowchart LR",
            '    claim["grounded family claim"] --> contradiction{"material contradiction?"}',
            '    contradiction -->|yes| narrow["downgrade or refuse"]',
            '    contradiction -->|no| decision["challenged recommendation"]',
            '    decision --> feasible{"follow-up feasible and informative?"}',
            "    feasible -->|no| narrow",
            '    feasible -->|yes| action["bounded laboratory action"]',
            '    action --> outcome["requested-versus-observed outcome"]',
            '    outcome --> next["next decision revision"]',
            "```",
            "",
            "The maps constrain action, not the underlying analytical record. A laboratory refusal does not erase a valid identification or quantification result; it says that the proposed use of that result is not justified under the current controls, burden, and authority.",
            "",
            "| workflow family | knowledge posture | recommendation posture | lab posture | weakest allowed posture |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for entry in rows:
        lines.append(
            f"| `{entry.workflow_family.value}` | `{entry.knowledge_strength.value}` | "
            f"`{entry.intelligence_strength.value}` | `{entry.lab_strength.value}` | "
            f"`{entry.weakest_allowed_strength.value}` |"
        )
    lines.extend(
        [
            "",
            "## Family Maps",
            "",
        ]
    )
    for entry in rows:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`",
                "",
                *(_render_strength_line(entry)),
                "",
                f"- contradiction pressure: {entry.contradiction_summary}",
                f"- knowledge next action: {entry.contradiction_next_action}",
                f"- recommendation summary: {entry.recommendation_summary}",
                f"- recommendation blockers: {', '.join(entry.recommendation_blockers) if entry.recommendation_blockers else 'none'}",
                f"- assay burden and follow-up posture: {entry.lab_summary}",
                f"- control demands: {', '.join(entry.control_demands) if entry.control_demands else 'none'}",
                f"- burden tradeoffs: {', '.join(entry.burden_tradeoffs) if entry.burden_tradeoffs else 'none'}",
                f"- cost of being wrong: {', '.join(entry.cost_of_being_wrong) if entry.cost_of_being_wrong else 'none'}",
                f"- evidence paths: {', '.join(f'`{path}`' for path in entry.evidence_paths)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Continue From Consequence",
            "",
            "- Open [What Changed The Recommendation](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/what-changed-the-recommendation/) when the question is which evidence axis or observed outcome actually moved the call.",
            "- Open [Outcome Learning Loops](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/outcome-learning-loops/) when the question is how requested-versus-observed follow-up should tighten the next recommendation.",
            "- Open [Workflow Refusal Handbook](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/workflow-refusal-handbook/) when the question is whether the honest next action is to stop, rerun, narrow, or refuse.",
            "",
            "## Resulting Interpretation",
            "",
            "The family table states the permitted posture. The family map names the exact contradiction, control demand, burden, and cost-of-error record responsible for that posture. If those records cannot be resolved, the posture is not independently reviewable.",
        ]
    )
    return "\n".join(lines)


def _render_recommendation_change(entry: WorkflowRecommendationChange) -> list[str]:
    return [
        f"### `{entry.workflow_family.value}`",
        "",
        f"- current posture: `{entry.current_strength.value}`",
        f"- without comparator evidence: `{entry.without_comparator.value}`",
        f"- without literature evidence: `{entry.without_literature.value}`",
        f"- with doubled lab burden: `{entry.with_doubled_lab_burden.value}`",
        (
            f"- observed outcome revision: `{entry.observed_outcome_strength.value}`"
            if entry.observed_outcome_strength is not None
            else "- observed outcome revision: no shipped recommendation revision yet"
        ),
        f"- primary change driver: {entry.primary_change_driver}",
        f"- driver signals: {', '.join(entry.driver_signals) if entry.driver_signals else 'none'}",
        f"- evidence paths: {', '.join(f'`{path}`' for path in entry.evidence_paths)}",
        "",
    ]


def _render_recommendation_changes() -> str:
    changes = build_workflow_recommendation_changes()
    lines = _front_matter(
        title="What Changed The Recommendation",
        owner="bijux-proteomics-docs",
    )
    lines.extend(
        [
            "# What Changed The Recommendation",
            "",
            "A recommendation can change when comparator evidence, literature evidence, decision policy, laboratory burden, or an observed outcome changes. The prior decision remains immutable; a revision points back to it and identifies the inputs that moved.",
            "",
            "## How To Read These Counterfactuals",
            "",
            "- Treat each family row as a stress test on the released sentence rather than a marketing recap of the current result.",
            "- If removing one evidence axis or increasing downstream burden collapses the call, the weaker posture is part of the truthful product surface today.",
            "- Observed outcome revisions matter only when they change the next honest sentence, not when they merely add more activity around the same uncertainty.",
            "",
            "## What Counts As A Real Change Driver",
            "",
            "- a comparator path that keeps the public sentence from outrunning transfer pressure",
            "- a literature or grounding surface that keeps the scientific story from sounding cleaner than its evidence state",
            "- a lab-burden shift that makes the same analytical story no longer worth the spend",
            "- an observed outcome that materially changes the next sentence instead of just adding more work around the same uncertainty",
            "",
            "```mermaid",
            "flowchart TD",
            '    prior["retained prior decision"] --> compare["compare input revisions"]',
            '    compare --> evidence{"evidence changed?"}',
            '    compare --> policy{"policy changed?"}',
            '    compare --> burden{"burden changed?"}',
            '    compare --> outcome{"outcome observed?"}',
            '    evidence --> attribution["named driver set"]',
            "    policy --> attribution",
            "    burden --> attribution",
            "    outcome --> attribution",
            '    attribution --> revised["new posture and rationale"]',
            '    revised --> audit["old and new records remain inspectable"]',
            "```",
            "",
        ]
    )
    for entry in changes:
        lines.extend(_render_recommendation_change(entry))
    lines.extend(
        [
            "## Reading Rule",
            "",
            "If comparator removal, literature removal, doubled assay burden, or one observed outcome can collapse the recommendation, the permitted wording stays at the weaker posture. A stronger posture requires a checked counterfactual record demonstrating that the relevant pressure no longer changes the call.",
        ]
    )
    return "\n".join(lines)


def _render_learning_loop(entry: WorkflowOutcomeLearningLoop) -> list[str]:
    requested_assays = (
        ", ".join(f"`{assay}`" for assay in entry.requested_assay_ids)
        if entry.requested_assay_ids
        else "none recorded"
    )
    observed_assays = (
        ", ".join(f"`{assay}`" for assay in entry.observed_assay_ids)
        if entry.observed_assay_ids
        else "none recorded"
    )
    lines = [
        f"### `{entry.workflow_family.value}`",
        "",
        f"- initial posture: `{entry.initial_strength.value}`",
        f"- revised posture after outcome: `{entry.revised_strength.value}`",
        f"- worth the assay spend: {'yes' if entry.worth_it else 'no'}",
        f"- requested assays: {requested_assays}",
        f"- observed assays: {observed_assays}",
        f"- matched assays: {', '.join(f'`{assay}`' for assay in entry.matched_assay_ids) if entry.matched_assay_ids else 'none'}",
        f"- blocked assays: {', '.join(f'`{assay}`' for assay in entry.blocked_assay_ids) if entry.blocked_assay_ids else 'none'}",
        f"- weakened assays: {', '.join(f'`{assay}`' for assay in entry.weakened_assay_ids) if entry.weakened_assay_ids else 'none'}",
        "",
    ]
    for label, values, code_values in (
        ("learning points", entry.learning_points, False),
        ("next adjustments", entry.next_adjustments, False),
        ("evidence paths", entry.evidence_paths, True),
    ):
        lines.extend([f"#### {label}", ""])
        lines.extend(
            f"- `{value}`" if code_values else f"- {value}"
            for value in values
        )
        lines.append("")
    return lines


def _render_outcome_learning_loops() -> str:
    loops = build_workflow_outcome_learning_loops()
    lines = _front_matter(
        title="Outcome Learning Loops",
        owner="bijux-proteomics-lab-docs",
    )
    lines.extend(
        [
            "# Outcome Learning Loops",
            "",
            "Outcome loops compare requested follow-up with observed work and carry the difference into the next recommendation. The prior recommendation, approved handoff, and observation remain separate immutable records.",
            "",
            "## What One Loop Tells You",
            "",
            "Each workflow-family loop keeps the same questions visible:",
            "",
            "- what the recommendation posture was before follow-up",
            "- what assays were requested",
            "- what assays actually happened",
            "- whether the loop was worth the assay spend",
            "- how the observed result should narrow or strengthen the next recommendation",
            "",
            "```mermaid",
            "flowchart LR",
            '    request["requested assays and expected information"] --> observation["observed assays, QC, and deviations"]',
            '    observation --> reconcile["match, block, weaken, or contradict"]',
            '    reconcile --> worth{"information justified burden?"}',
            '    worth -->|yes| revise["versioned evidence and decision revision"]',
            '    worth -->|no| narrow["narrow, hold, or refuse"]',
            '    revise --> preserve["retain prior records for calibration"]',
            '    narrow --> preserve',
            "```",
            "",
            "## Cross-Family Snapshot",
            "",
            "| workflow family | initial posture | revised posture | worth the assay spend | current lesson |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for entry in loops:
        lesson = (
            entry.learning_points[0]
            if entry.learning_points
            else "no shipped learning point yet"
        )
        lines.append(
            f"| `{entry.workflow_family.value}` | `{entry.initial_strength.value}` | "
            f"`{entry.revised_strength.value}` | "
            f"{'yes' if entry.worth_it else 'no'} | {lesson} |"
        )
    lines.extend(
        [
            "",
        ]
    )
    for entry in loops:
        lines.extend(_render_learning_loop(entry))
    lines.extend(
        [
            "## Boundary",
            "",
            "An outcome loop can revise the next recommendation only at the scope supported by its controls and observed assays. Missing assays, failed controls, and weak information gain are evidence for narrowing; they are not silently discarded operational details.",
        ]
    )
    return "\n".join(lines)


def _render_refusal_guidance(entry: WorkflowRefusalGuidance) -> list[str]:
    lines = [
        f"### `{entry.workflow_family.value}`",
        "",
        f"- current posture: `{entry.current_strength.value}`",
        "",
    ]
    for label, conditions in (
        ("stop when", entry.stop_when),
        ("rerun when", entry.rerun_when),
        ("narrow when", entry.narrow_when),
        ("refuse when", entry.refuse_when),
    ):
        lines.extend([f"#### {label}", ""])
        if conditions:
            lines.extend(f"- {condition}" for condition in conditions)
        else:
            lines.append("- no additional family-specific condition is published")
        lines.append("")
    lines.extend(
        [
            "#### evidence paths",
            "",
            *(f"- `{path}`" for path in entry.evidence_paths),
            "",
        ]
    )
    return lines


def _render_refusal_handbook() -> str:
    guidance = build_workflow_refusal_guidance_family()
    lines = _front_matter(
        title="Workflow Refusal Handbook",
        owner="bijux-proteomics-lab-docs",
    )
    lines.extend(
        [
            "# Workflow Refusal Handbook",
            "",
            "A refusal record distinguishes four operational responses. Each response preserves the current evidence and names what can happen next.",
            "",
            "| response | meaning | next admissible action |",
            "| --- | --- | --- |",
            "| stop | the current handoff must not proceed | preserve state and inspect the named blocking condition |",
            "| rerun | the question remains valid and recoverable evidence is missing or invalid | correct the declared condition and create a new run record |",
            "| narrow | a weaker scope remains supported | issue a revised bounded question or recommendation |",
            "| refuse | no responsible action exists inside the current policy or authority | retain the refusal until new evidence or authority changes the precondition |",
            "",
        ]
    )
    for entry in guidance:
        lines.extend(_render_refusal_guidance(entry))
    lines.extend(
        [
            "## Rule",
            "",
            "If the best downstream action is stop, rerun, narrow, or refuse, the public recommendation remains weaker than a full recommendation. A retry creates a new run or decision record; it does not erase the refusal that justified it.",
        ]
    )
    return "\n".join(lines)


def _write(path: Path, text: str) -> None:
    path.write_text(text + "\n", encoding="utf-8")


def _up_to_date(path: Path, text: str) -> bool:
    if not path.exists():
        return False
    return bool(path.read_text(encoding="utf-8") == text + "\n")


def run(check: bool = False) -> int:
    renders: tuple[tuple[Path, str], ...] = (
        (WORKFLOW_CONSEQUENCE_MAPS_PATH, _render_consequence_maps()),
        (RECOMMENDATION_CHANGE_PATH, _render_recommendation_changes()),
        (LAB_CONSEQUENCE_OUTCOME_LEARNING_PATH, _render_outcome_learning_loops()),
        (LAB_CONSEQUENCE_REFUSAL_HANDBOOK_PATH, _render_refusal_handbook()),
    )
    if check:
        stale = [
            render_path.as_posix()
            for render_path, text in renders
            if not _up_to_date(render_path, text)
        ]
        if not stale:
            print("workflow consequence docs are up to date")
            return 0
        for stale_path in stale:
            print(f"stale workflow consequence doc: {stale_path}")
        return 1
    for path, text in renders:
        _write(path, text)
    print("generated workflow consequence docs")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the workflow consequence docs."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if any workflow consequence docs are stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
