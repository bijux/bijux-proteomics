# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime proof accounting for flagship and simulation-only workflow claims."""

from __future__ import annotations

from pathlib import Path
import re
from typing import TypedDict

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.workflows.assurance import simulation_contract_lane_ids
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkRunMode,
    build_benchmark_run_specs,
)
from bijux_proteomics_runtime.workflows.proof_classes import RuntimeProofClass

__all__ = [
    "RuntimeExecutionShortcutAudit",
    "RuntimeExecutionShortcutAuditEntry",
    "RuntimeExecutionShortcutAuditIssue",
    "RuntimeFlagshipProofGate",
    "RuntimeFlagshipProofGateIssue",
    "RuntimeProofClass",
    "RuntimeProofClaimRow",
    "RuntimeProofMap",
    "RuntimeProofPromotionChecklist",
    "RuntimeProofPromotionChecklistItem",
    "build_runtime_execution_shortcut_audit",
    "build_runtime_flagship_proof_gate",
    "build_runtime_proof_map",
    "build_runtime_proof_promotion_checklist",
    "validate_runtime_execution_shortcut_audit",
]

_SHORTCUT_PATTERN = re.compile(r"^\s*def (?P<name>_fake_[a-z0-9_]+)\(", re.MULTILINE)
_PROHIBITED_FAMILY_TOKENS = ("end_to_end", "integrity", "replay", "execution")


class _ShortcutClassification(TypedDict):
    """Typed classification payload for one fake-helper exception."""

    proof_class: RuntimeProofClass
    counts_toward_flagship_proof: bool
    justified_exception: bool
    justification: str


class RuntimeExecutionShortcutAuditEntry(JsonModel):
    """One remaining fake or simulated execution helper in runtime tests."""

    model_config = ConfigDict(extra="forbid")

    helper_id: str = Field(..., min_length=1)
    helper_name: str = Field(..., min_length=1)
    test_path: str = Field(..., min_length=1)
    line_number: int = Field(..., ge=1)
    proof_class: RuntimeProofClass
    counts_toward_flagship_proof: bool
    justified_exception: bool
    justification: str = Field(..., min_length=1)


class RuntimeExecutionShortcutAuditIssue(JsonModel):
    """One invalid fake or simulated helper use in runtime tests."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)


class RuntimeExecutionShortcutAudit(JsonModel):
    """Report listing every remaining fake or simulated runtime test helper."""

    model_config = ConfigDict(extra="forbid")

    audit_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[RuntimeExecutionShortcutAuditEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeProofClaimRow(JsonModel):
    """One shipped runtime claim and the proof class that currently backs it."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    proof_class: RuntimeProofClass
    claim_surface: str = Field(..., min_length=1)
    claim_summary: str = Field(..., min_length=1)
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    counts_toward_flagship_authority: bool
    note: str = Field(..., min_length=1)


class RuntimeProofMap(JsonModel):
    """Runtime proof map across flagship, replay, and simulation-only surfaces."""

    model_config = ConfigDict(extra="forbid")

    map_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    claims: tuple[RuntimeProofClaimRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeFlagshipProofGateIssue(JsonModel):
    """One blocker on counting a workflow family toward flagship authority."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    detail: str = Field(..., min_length=1)


class RuntimeFlagshipProofGate(JsonModel):
    """Release-facing runtime proof gate for outsider-auditable authority."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(..., min_length=1)
    blocked_workflow_families: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[RuntimeFlagshipProofGateIssue, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class RuntimeProofPromotionChecklistItem(JsonModel):
    """One maintainer task before a family may claim raw-executable runtime proof."""

    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    current_proof_class: RuntimeProofClass
    target_proof_class: RuntimeProofClass
    required_path: str = Field(..., min_length=1)
    requirement_summary: str = Field(..., min_length=1)
    satisfied: bool
    blocker_reason: str = Field(..., min_length=1)


class RuntimeProofPromotionChecklist(JsonModel):
    """Maintainer checklist for proving a family beyond import or simulation."""

    model_config = ConfigDict(extra="forbid")

    checklist_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    items: tuple[RuntimeProofPromotionChecklistItem, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_runtime_execution_shortcut_audit(
    repo_root: Path | None = None,
) -> RuntimeExecutionShortcutAudit:
    """List the remaining fake execution helpers in runtime tests."""

    root = _repo_root() if repo_root is None else repo_root
    entries: list[RuntimeExecutionShortcutAuditEntry] = []
    for relative_path in sorted(
        path.relative_to(root).as_posix()
        for path in (root / "packages" / "bijux-proteomics-runtime" / "tests").rglob(
            "test_*.py"
        )
    ):
        content = (root / relative_path).read_text(encoding="utf-8")
        for match in _SHORTCUT_PATTERN.finditer(content):
            helper_name = match.group("name")
            classification = _shortcut_classifications().get((relative_path, helper_name))
            if classification is None:
                entries.append(
                    RuntimeExecutionShortcutAuditEntry(
                        helper_id=f"{relative_path}::{helper_name}",
                        helper_name=helper_name,
                        test_path=relative_path,
                        line_number=content[: match.start()].count("\n") + 1,
                        proof_class=RuntimeProofClass.SIMULATION_ONLY,
                        counts_toward_flagship_proof=True,
                        justified_exception=False,
                        justification=(
                            "unclassified fake execution helper; classify or remove it before "
                            "counting this test family as real runtime proof"
                        ),
                    )
                )
                continue
            entries.append(
                RuntimeExecutionShortcutAuditEntry(
                    helper_id=f"{relative_path}::{helper_name}",
                    helper_name=helper_name,
                    test_path=relative_path,
                    line_number=content[: match.start()].count("\n") + 1,
                    proof_class=classification["proof_class"],
                    counts_toward_flagship_proof=classification[
                        "counts_toward_flagship_proof"
                    ],
                    justified_exception=classification["justified_exception"],
                    justification=classification["justification"],
                )
            )
    return RuntimeExecutionShortcutAudit(
        audit_id="runtime-execution-shortcut-audit",
        artifact_path="artifacts/runtime/proof-accounting/runtime_execution_shortcut_audit.json",
        entries=tuple(entries),
        note=(
            "Fake helpers are allowed only when they are explicitly classified as simulation-only "
            "and excluded from flagship runtime proof accounting."
        ),
    )


def validate_runtime_execution_shortcut_audit(
    repo_root: Path | None = None,
) -> tuple[RuntimeExecutionShortcutAuditIssue, ...]:
    """Fail when fake helpers leak into real runtime proof families."""

    audit = build_runtime_execution_shortcut_audit(repo_root)
    issues: list[RuntimeExecutionShortcutAuditIssue] = []
    for entry in audit.entries:
        if not entry.justified_exception and entry.proof_class is RuntimeProofClass.SIMULATION_ONLY:
            issues.append(
                RuntimeExecutionShortcutAuditIssue(
                    code="unclassified-fake-helper",
                    detail=(
                        f"{entry.helper_id} is still present without an approved simulation-only "
                        "classification"
                    ),
                )
            )
        if any(token in entry.test_path for token in _PROHIBITED_FAMILY_TOKENS) and not (
            entry.proof_class is RuntimeProofClass.SIMULATION_ONLY
            and entry.justified_exception
            and not entry.counts_toward_flagship_proof
        ):
            issues.append(
                RuntimeExecutionShortcutAuditIssue(
                    code="fake-helper-in-proof-family",
                    detail=(
                        f"{entry.helper_id} still appears inside a real execution, replay, "
                        "integrity, or end-to-end family"
                    ),
                )
            )
        if entry.counts_toward_flagship_proof and entry.proof_class is RuntimeProofClass.SIMULATION_ONLY:
            issues.append(
                RuntimeExecutionShortcutAuditIssue(
                    code="simulation-counted-as-flagship-proof",
                    detail=(
                        f"{entry.helper_id} is marked simulation-only but still counted toward "
                        "flagship proof"
                    ),
                )
            )
    return tuple(issues)


def build_runtime_proof_map() -> RuntimeProofMap:
    """Build the proof map for shipped runtime claims."""

    claims: list[RuntimeProofClaimRow] = []
    for spec in build_benchmark_run_specs():
        proof_class = _proof_class_for_run_mode(spec.run_mode)
        claims.append(
            RuntimeProofClaimRow(
                claim_id=f"{spec.workflow_family}:review-surface",
                workflow_family=spec.workflow_family,
                proof_class=proof_class,
                claim_surface="flagship_runtime_lane",
                claim_summary=(
                    "current flagship runtime lane for this workflow family"
                ),
                artifact_paths=spec.public_package_paths
                + (spec.primary_input_path,)
                + spec.companion_input_paths,
                validating_test_paths=spec.validating_test_paths,
                counts_toward_flagship_authority=True,
                note=(
                    "The flagship runtime lane is the strongest runtime proof surface used by "
                    "outsider review and release-candidate accounting."
                ),
            )
        )
        if spec.workflow_family != "sequence_to_digest":
            claims.append(
                RuntimeProofClaimRow(
                    claim_id=f"{spec.workflow_family}:failure-replay",
                    workflow_family=spec.workflow_family,
                    proof_class=RuntimeProofClass.REPLAY_BACKED_EXECUTION,
                    claim_surface="flagship_failure_replay",
                    claim_summary=(
                        "failure replay and invalidation surface for the flagship runtime lane"
                    ),
                    artifact_paths=(
                        f"packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/{_flagship_family_id(spec.workflow_family)}/failure_replay.json",
                    ),
                    validating_test_paths=(
                        "packages/bijux-proteomics-runtime/tests/workflows/test_flagship_run_bundle_surface.py",
                    ),
                    counts_toward_flagship_authority=False,
                    note=(
                        "Replay-backed proof is real runtime evidence, but it does not replace the "
                        "strongest primary lane when the question is outsider authority."
                    ),
                )
            )
    for lane_id in simulation_contract_lane_ids():
        claims.append(
            RuntimeProofClaimRow(
                claim_id=f"{lane_id}:simulation-contract",
                workflow_family="external_engine_simulation",
                proof_class=RuntimeProofClass.SIMULATION_ONLY,
                claim_surface="simulation_contract",
                claim_summary=(
                    "deterministic simulation contract for external engine behavior"
                ),
                artifact_paths=(
                    "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py",
                ),
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py",
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_assurance_surface.py",
                ),
                counts_toward_flagship_authority=False,
                note=(
                    "Simulation contracts stay visible so reviewers can inspect them without "
                    "mistaking them for flagship workflow proof."
                ),
            )
        )
    return RuntimeProofMap(
        map_id="runtime-proof-map",
        artifact_path="artifacts/runtime/proof-accounting/runtime_proof_map.json",
        claims=tuple(claims),
        note=(
            "Every shipped runtime claim must name whether it is backed by raw execution, "
            "import-backed execution, replay-backed execution, or pure simulation."
        ),
    )


def build_runtime_flagship_proof_gate(
    repo_root: Path | None = None,
) -> RuntimeFlagshipProofGate:
    """Build the gate that blocks fake-backed runtime proof from release authority."""

    issues: list[RuntimeFlagshipProofGateIssue] = []
    audit = build_runtime_execution_shortcut_audit(repo_root)
    proof_map = build_runtime_proof_map()
    shortcut_tests = {
        entry.test_path
        for entry in audit.entries
        if entry.counts_toward_flagship_proof
    }
    blocked: set[str] = set()
    for claim in proof_map.claims:
        if not claim.counts_toward_flagship_authority:
            continue
        if claim.proof_class is RuntimeProofClass.SIMULATION_ONLY:
            blocked.add(claim.workflow_family)
            issues.append(
                RuntimeFlagshipProofGateIssue(
                    workflow_family=claim.workflow_family,
                    code="simulation-cannot-earn-flagship-authority",
                    detail=(
                        f"{claim.claim_id} is still simulation-only, so it cannot count toward "
                        "outsider-auditable or release-candidate authority"
                    ),
                )
            )
        helper_paths = tuple(
            path for path in claim.validating_test_paths if path in shortcut_tests
        )
        if helper_paths:
            blocked.add(claim.workflow_family)
            issues.append(
                RuntimeFlagshipProofGateIssue(
                    workflow_family=claim.workflow_family,
                    code="fake-helper-still-present-in-flagship-path",
                    detail=(
                        f"{claim.claim_id} still depends on a validating test with fake execution "
                        f"helpers: {', '.join(helper_paths)}"
                    ),
                )
            )
    return RuntimeFlagshipProofGate(
        gate_id="runtime-flagship-proof-gate",
        blocked_workflow_families=tuple(sorted(blocked)),
        issues=tuple(issues),
        note=(
            "A workflow family cannot count toward outsider authority when its strongest runtime "
            "lane still depends on fake execution helpers or simulation-only proof."
        ),
    )


def build_runtime_proof_promotion_checklist() -> RuntimeProofPromotionChecklist:
    """Build the maintainer checklist for promoting runtime proof classes."""

    current_claims = {
        claim.workflow_family: claim
        for claim in build_runtime_proof_map().claims
        if claim.counts_toward_flagship_authority
    }
    items: list[RuntimeProofPromotionChecklistItem] = []
    for workflow_family, required_path, summary, blocker in (
        (
            "dda_import",
            "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py",
            "replace the current import-backed DDA lane with one raw review path over tracked spectra inputs",
            "the strongest DDA runtime lane still resolves through run_benchmark_dda_import_path",
        ),
        (
            "dia_import",
            "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py",
            "replace the current import-backed DIA lane with one raw review path over tracked DIA evidence inputs",
            "the strongest DIA runtime lane still resolves through run_benchmark_dia_import_path",
        ),
        (
            "targeted_review",
            "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json",
            "promote targeted from import-facing review to raw-executable runtime review with tracked acquisition-side evidence",
            "the targeted benchmark package still authorizes only an import-backed runtime lane",
        ),
    ):
        claim = current_claims[workflow_family]
        items.append(
            RuntimeProofPromotionChecklistItem(
                item_id=f"{workflow_family}:raw-proof-promotion",
                workflow_family=workflow_family,
                current_proof_class=claim.proof_class,
                target_proof_class=RuntimeProofClass.RAW_EXECUTION,
                required_path=required_path,
                requirement_summary=summary,
                satisfied=claim.proof_class is RuntimeProofClass.RAW_EXECUTION,
                blocker_reason=(
                    "already raw-executable"
                    if claim.proof_class is RuntimeProofClass.RAW_EXECUTION
                    else blocker
                ),
            )
        )
    return RuntimeProofPromotionChecklist(
        checklist_id="runtime-proof-promotion-checklist",
        artifact_path="artifacts/runtime/proof-accounting/runtime_proof_promotion_checklist.json",
        items=tuple(items),
        note=(
            "This checklist prevents import or simulation lanes from quietly inheriting raw-executable "
            "trust without concrete tracked inputs, runtime entrypoints, and checked benchmark assets."
        ),
    )


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def _proof_class_for_run_mode(run_mode: BenchmarkRunMode) -> RuntimeProofClass:
    if run_mode is BenchmarkRunMode.RAW_EXECUTABLE:
        return RuntimeProofClass.RAW_EXECUTION
    if run_mode is BenchmarkRunMode.IMPORT_ONLY:
        return RuntimeProofClass.IMPORT_BACKED_EXECUTION
    return RuntimeProofClass.SIMULATION_ONLY


def _flagship_family_id(workflow_family: str) -> str:
    return {
        "sequence_to_digest": "sequence_to_digest",
        "dda_import": "dda",
        "dda_generalization_import": "dda",
        "dia_import": "dia",
        "dia_generalization_review": "dia",
        "quant_review": "lfq",
        "quant_generalization_review": "lfq",
        "multiplex_review": "multiplex",
        "multiplex_generalization_review": "multiplex",
        "ptm_review": "ptm",
        "ptm_generalization_review": "ptm",
        "targeted_review": "targeted",
        "targeted_generalization_review": "targeted",
    }[workflow_family]


def _shortcut_classifications() -> dict[tuple[str, str], _ShortcutClassification]:
    simulation_justification = (
        "this helper exists only inside the container and scheduler smoke-contract tests, "
        "which model launch-bundle publication and mocked environment transitions rather than "
        "flagship scientific runtime proof"
    )
    cli_justification = (
        "this helper exists only inside CLI envelope tests, where the question is API response "
        "shape rather than real runtime execution"
    )
    performance_justification = (
        "this helper exists only inside a performance-control benchmark so timing noise from the "
        "full execution path does not masquerade as scientific runtime proof"
    )
    return {
        (
            "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py",
            "_fake_run_flow_from_fixture",
        ): {
            "proof_class": RuntimeProofClass.SIMULATION_ONLY,
            "counts_toward_flagship_proof": False,
            "justified_exception": True,
            "justification": simulation_justification,
        },
        (
            "packages/bijux-proteomics-runtime/tests/execution/test_runtime_container_and_scheduler_end_to_end.py",
            "_fake_run_flow",
        ): {
            "proof_class": RuntimeProofClass.SIMULATION_ONLY,
            "counts_toward_flagship_proof": False,
            "justified_exception": True,
            "justification": simulation_justification,
        },
        (
            "packages/bijux-proteomics-runtime/tests/api/test_runtime_cli_surface.py",
            "_fake_run_sequence",
        ): {
            "proof_class": RuntimeProofClass.SIMULATION_ONLY,
            "counts_toward_flagship_proof": False,
            "justified_exception": True,
            "justification": cli_justification,
        },
        (
            "packages/bijux-proteomics-runtime/tests/api/test_runtime_cli_surface.py",
            "_fake_import_result",
        ): {
            "proof_class": RuntimeProofClass.SIMULATION_ONLY,
            "counts_toward_flagship_proof": False,
            "justified_exception": True,
            "justification": cli_justification,
        },
        (
            "packages/bijux-proteomics-runtime/tests/performance/test_runtime_execution_control_benchmark_surface.py",
            "_fake_success",
        ): {
            "proof_class": RuntimeProofClass.SIMULATION_ONLY,
            "counts_toward_flagship_proof": False,
            "justified_exception": True,
            "justification": performance_justification,
        },
    }
