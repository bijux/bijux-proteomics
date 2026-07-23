from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    build_package_dependency_policy_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)

__all__ = [
    "REPOSITORY_PRODUCT_SHAPE_PATH",
    "ArtifactHandoffEntry",
    "PackageRoleEntry",
    "RepositoryLifecycleStageEntry",
    "RepositoryProductShapeReport",
    "build_repository_product_shape_report",
    "run",
    "validate_repository_product_shape",
]


REPOSITORY_PRODUCT_SHAPE_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "repository-product-shape.toml"
)


@dataclass(frozen=True)
class RepositoryLifecycleStageEntry:
    """One durable cross-package stage in the repository product lifecycle."""

    stage_id: str
    title: str
    owner_package: str
    handoff_class: str
    summary: str
    docs_path: str
    primary_path: str


@dataclass(frozen=True)
class ArtifactHandoffEntry:
    """One owned artifact handoff that crosses package boundaries."""

    handoff_class: str
    owner_package: str
    producer_packages: tuple[str, ...]
    consumer_packages: tuple[str, ...]
    examples: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class PackageRoleEntry:
    """One package role inside the cross-package product shape."""

    distribution_name: str
    role_kind: str
    role_summary: str
    docs_path: str
    readme_path: str
    allowed_outbound_imports: tuple[str, ...]
    forbidden_outbound_imports: tuple[str, ...]
    owned_handoff_classes: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryProductShapeReport:
    """Machine-readable repository shape for docs and boundary governance."""

    stages: tuple[RepositoryLifecycleStageEntry, ...]
    handoffs: tuple[ArtifactHandoffEntry, ...]
    packages: tuple[PackageRoleEntry, ...]


def _stage_entries() -> tuple[RepositoryLifecycleStageEntry, ...]:
    return (
        RepositoryLifecycleStageEntry(
            stage_id="shared-contracts",
            title="Shared contracts and identifiers",
            owner_package="bijux-proteomics-foundation",
            handoff_class="foundation-contract",
            summary=(
                "Foundation fixes the shared schema, identifier, and serialization "
                "rules that every other package consumes."
            ),
            docs_path="docs/03-bijux-proteomics-foundation/foundation/package-overview.md",
            primary_path=(
                "packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation"
            ),
        ),
        RepositoryLifecycleStageEntry(
            stage_id="benchmark-intake",
            title="Benchmark asset intake and domain contracts",
            owner_package="bijux-proteomics-core",
            handoff_class="benchmark-asset-bundle",
            summary=(
                "Core owns flagship benchmark asset intake, durable scientific "
                "contracts, and the workflow request shapes that runtime executes."
            ),
            docs_path="docs/04-bijux-proteomics-core/foundation/flagship-benchmark-assets.md",
            primary_path="packages/bijux-proteomics-core/benchmark-assets",
        ),
        RepositoryLifecycleStageEntry(
            stage_id="runtime-execution",
            title="Runtime execution and replay",
            owner_package="bijux-proteomics-runtime",
            handoff_class="runtime-run-bundle",
            summary=(
                "Runtime turns owned workflow requests into reproducible execution "
                "artifacts, replay bundles, and operator-visible run state."
            ),
            docs_path="docs/09-bijux-proteomics-runtime/index.md",
            primary_path=(
                "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime"
            ),
        ),
        RepositoryLifecycleStageEntry(
            stage_id="scientific-review",
            title="Scientific review and evidence memory",
            owner_package="bijux-proteomics-knowledge",
            handoff_class="scientific-review-bundle",
            summary=(
                "Knowledge turns execution outputs and external references into "
                "grounded evidence state, contradiction handling, and review memory."
            ),
            docs_path="docs/06-bijux-proteomics-knowledge/index.md",
            primary_path=(
                "packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge"
            ),
        ),
        RepositoryLifecycleStageEntry(
            stage_id="recommendation-posture",
            title="Recommendation posture and refusal logic",
            owner_package="bijux-proteomics-intelligence",
            handoff_class="recommendation-record",
            summary=(
                "Intelligence converts reviewed evidence into recommendation "
                "strength, sensitivity notes, and refusal posture."
            ),
            docs_path="docs/05-bijux-proteomics-intelligence/index.md",
            primary_path=(
                "packages/bijux-proteomics-intelligence/src/"
                "bijux_proteomics_intelligence"
            ),
        ),
        RepositoryLifecycleStageEntry(
            stage_id="lab-consequence",
            title="Lab consequence and observed outcomes",
            owner_package="bijux-proteomics-lab",
            handoff_class="lab-consequence-record",
            summary=(
                "Lab owns assay planning, readiness, handoff honesty, and the "
                "observed-outcome loop that feeds later review."
            ),
            docs_path="docs/07-bijux-proteomics-lab/index.md",
            primary_path="packages/bijux-proteomics-lab/src/bijux_proteomics_lab",
        ),
    )


def _handoff_entries() -> tuple[ArtifactHandoffEntry, ...]:
    return (
        ArtifactHandoffEntry(
            handoff_class="foundation-contract",
            owner_package="bijux-proteomics-foundation",
            producer_packages=("bijux-proteomics-foundation",),
            consumer_packages=(
                "bijux-proteomics-core",
                "bijux-proteomics-runtime",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-knowledge",
                "bijux-proteomics-lab",
            ),
            examples=(
                "DocumentSchema",
                "JsonModel",
                "ProgramId",
            ),
            summary=(
                "Shared contracts move across every product package without moving "
                "domain, recommendation, execution, or lab ownership upward."
            ),
        ),
        ArtifactHandoffEntry(
            handoff_class="benchmark-asset-bundle",
            owner_package="bijux-proteomics-core",
            producer_packages=("bijux-proteomics-core",),
            consumer_packages=(
                "bijux-proteomics-runtime",
                "bijux-proteomics-knowledge",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-lab",
            ),
            examples=(
                "flagship benchmark manifest",
                "challenge corpus package",
                "workflow execution request",
            ),
            summary=(
                "Core owns the benchmark package and runtime-agnostic workflow "
                "request that the rest of the suite consumes."
            ),
        ),
        ArtifactHandoffEntry(
            handoff_class="runtime-run-bundle",
            owner_package="bijux-proteomics-runtime",
            producer_packages=("bijux-proteomics-runtime",),
            consumer_packages=(
                "bijux-proteomics-knowledge",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-lab",
            ),
            examples=(
                "run manifest",
                "artifact ledger",
                "review output bundle",
            ),
            summary=(
                "Runtime owns replayable run outputs and the operator-facing bundle "
                "that later scientific and lab layers read."
            ),
        ),
        ArtifactHandoffEntry(
            handoff_class="scientific-review-bundle",
            owner_package="bijux-proteomics-knowledge",
            producer_packages=("bijux-proteomics-knowledge",),
            consumer_packages=(
                "bijux-proteomics-intelligence",
                "bijux-proteomics-lab",
            ),
            examples=(
                "evidence bundle",
                "contradiction ledger",
                "knowledge decision brief",
            ),
            summary=(
                "Knowledge owns the grounded evidence memory that recommendation "
                "and lab consequence must consume rather than recreate."
            ),
        ),
        ArtifactHandoffEntry(
            handoff_class="recommendation-record",
            owner_package="bijux-proteomics-intelligence",
            producer_packages=("bijux-proteomics-intelligence",),
            consumer_packages=("bijux-proteomics-lab",),
            examples=(
                "ranking brief",
                "recommendation stance",
                "refusal explanation",
            ),
            summary=(
                "Intelligence owns recommendation posture and the refusal logic "
                "that determines whether lab follow-up is justified."
            ),
        ),
        ArtifactHandoffEntry(
            handoff_class="lab-consequence-record",
            owner_package="bijux-proteomics-lab",
            producer_packages=("bijux-proteomics-lab",),
            consumer_packages=(
                "bijux-proteomics-knowledge",
                "bijux-proteomics-intelligence",
            ),
            examples=(
                "assay plan",
                "lab handoff",
                "observed outcome record",
            ),
            summary=(
                "Lab owns executable follow-up plans and the observed outcomes that "
                "must tighten later knowledge and recommendation posture."
            ),
        ),
    )


def _package_role_data() -> dict[str, tuple[str, str, str, tuple[str, ...]]]:
    return {
        "agentic-proteins": (
            "compatibility",
            "legacy compatibility bridge for runtime entrypoints and imports",
            "docs/02-agentic-proteins/foundation/compatibility-contract.md",
            (),
        ),
        "bijux-proteomics": (
            "alias",
            "install and command alias for bijux-proteomics-core",
            "packages/bijux-proteomics/README.md",
            (),
        ),
        "bijux-proteomics-dev": (
            "maintainer",
            "maintainer automation, docs checks, and release governance",
            "docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/index.md",
            (),
        ),
        "bijux-proteomics-foundation": (
            "product",
            "shared contracts, identifiers, and deterministic serialization",
            "docs/03-bijux-proteomics-foundation/index.md",
            ("foundation-contract",),
        ),
        "bijux-proteomics-core": (
            "product",
            "benchmark assets, durable scientific contracts, and workflow requests",
            "docs/04-bijux-proteomics-core/index.md",
            ("benchmark-asset-bundle",),
        ),
        "bijux-proteomics-runtime": (
            "product",
            "execution, provider binding, deterministic replay, and operator entrypoints",
            "docs/09-bijux-proteomics-runtime/index.md",
            ("runtime-run-bundle",),
        ),
        "bijux-proteomics-intelligence": (
            "product",
            "recommendation posture, ranking sensitivity, and refusal behavior",
            "docs/05-bijux-proteomics-intelligence/index.md",
            ("recommendation-record",),
        ),
        "bijux-proteomics-knowledge": (
            "product",
            "scientific memory, provenance, contradiction handling, and review state",
            "docs/06-bijux-proteomics-knowledge/index.md",
            ("scientific-review-bundle",),
        ),
        "bijux-proteomics-lab": (
            "product",
            "assay consequence planning, readiness, and observed outcomes",
            "docs/07-bijux-proteomics-lab/index.md",
            ("lab-consequence-record",),
        ),
        "proteomics": (
            "alias",
            "install and import alias for bijux-proteomics-core",
            "packages/proteomics/README.md",
            (),
        ),
        "proteomics-core": (
            "alias",
            "install and import alias for bijux-proteomics-core",
            "packages/proteomics-core/README.md",
            (),
        ),
        "proteomics-foundation": (
            "alias",
            "install and import alias for bijux-proteomics-foundation",
            "packages/proteomics-foundation/README.md",
            (),
        ),
        "proteomics-runtime": (
            "alias",
            "install and import alias for bijux-proteomics-runtime",
            "packages/proteomics-runtime/README.md",
            (),
        ),
        "proteomics-intelligence": (
            "alias",
            "install and import alias for bijux-proteomics-intelligence",
            "packages/proteomics-intelligence/README.md",
            (),
        ),
        "proteomics-knowledge": (
            "alias",
            "install and import alias for bijux-proteomics-knowledge",
            "packages/proteomics-knowledge/README.md",
            (),
        ),
        "proteomics-lab": (
            "alias",
            "install and import alias for bijux-proteomics-lab",
            "packages/proteomics-lab/README.md",
            (),
        ),
    }


def _package_entries() -> tuple[PackageRoleEntry, ...]:
    by_package = {
        entry.distribution_name: entry
        for entry in build_package_dependency_policy_report().entries
    }
    workspace = workspace_package_names()
    entries: list[PackageRoleEntry] = []
    role_data = _package_role_data()
    for package_name in workspace:
        role_kind, role_summary, docs_path, owned_handoff_classes = role_data[
            package_name
        ]
        allowed_outbound_imports = by_package[package_name].allowed_outbound_edges
        forbidden = tuple(
            package
            for package in workspace
            if package != package_name and package not in allowed_outbound_imports
        )
        entries.append(
            PackageRoleEntry(
                distribution_name=package_name,
                role_kind=role_kind,
                role_summary=role_summary,
                docs_path=docs_path,
                readme_path=f"packages/{package_name}/README.md",
                allowed_outbound_imports=allowed_outbound_imports,
                forbidden_outbound_imports=forbidden,
                owned_handoff_classes=owned_handoff_classes,
            )
        )
    return tuple(entries)


def build_repository_product_shape_report() -> RepositoryProductShapeReport:
    """Build the repository product shape report."""

    return RepositoryProductShapeReport(
        stages=_stage_entries(),
        handoffs=_handoff_entries(),
        packages=_package_entries(),
    )


def validate_repository_product_shape() -> tuple[str, ...]:
    """Validate that the repository product shape still matches live surfaces."""

    report = build_repository_product_shape_report()
    failures: list[str] = []
    package_names = set(workspace_package_names())
    stage_ids = {entry.stage_id for entry in report.stages}
    handoff_ids = {entry.handoff_class for entry in report.handoffs}
    package_by_name = {entry.distribution_name: entry for entry in report.packages}
    dependency_policy = {
        entry.distribution_name: entry.allowed_outbound_edges
        for entry in build_package_dependency_policy_report().entries
    }

    if set(_package_role_data()) != package_names:
        failures.append("repository product shape package list drifted from workspace")

    for stage in report.stages:
        if stage.owner_package not in package_names:
            failures.append(f"unknown stage owner {stage.owner_package}")
        if stage.handoff_class not in handoff_ids:
            failures.append(
                f"stage {stage.stage_id} references unknown handoff {stage.handoff_class}"
            )
        for relative_path in (stage.docs_path, stage.primary_path):
            if not (REPO_ROOT / relative_path).exists():
                failures.append(
                    f"stage {stage.stage_id} missing evidence path {relative_path}"
                )

    for handoff in report.handoffs:
        if handoff.owner_package not in package_names:
            failures.append(f"unknown handoff owner {handoff.owner_package}")
        for package_name in handoff.producer_packages + handoff.consumer_packages:
            if package_name not in package_names:
                failures.append(
                    f"handoff {handoff.handoff_class} references unknown package {package_name}"
                )

    for package in report.packages:
        if package.docs_path and not (REPO_ROOT / package.docs_path).exists():
            failures.append(
                f"{package.distribution_name}: missing docs path {package.docs_path}"
            )
        if not (REPO_ROOT / package.readme_path).exists():
            failures.append(
                f"{package.distribution_name}: missing README path {package.readme_path}"
            )
        if (
            dependency_policy[package.distribution_name]
            != package.allowed_outbound_imports
        ):
            failures.append(
                f"{package.distribution_name}: allowed outbound imports drifted from package dependency policy"
            )
        expected_forbidden = tuple(
            candidate
            for candidate in workspace_package_names()
            if candidate != package.distribution_name
            and candidate not in package.allowed_outbound_imports
        )
        if expected_forbidden != package.forbidden_outbound_imports:
            failures.append(
                f"{package.distribution_name}: forbidden outbound imports no longer match the workspace complement"
            )
        if not set(package.owned_handoff_classes) <= handoff_ids:
            failures.append(
                f"{package.distribution_name}: references unknown owned handoff classes"
            )

    if len(stage_ids) != len(report.stages):
        failures.append("duplicate repository lifecycle stage id")
    if len(handoff_ids) != len(report.handoffs):
        failures.append("duplicate artifact handoff id")
    if len(package_by_name) != len(report.packages):
        failures.append("duplicate package role entry")

    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: RepositoryProductShapeReport) -> str:
    lines = [
        "# Generated repository product shape.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.foundation.repository_product_shape",
        "",
    ]
    for stage in report.stages:
        lines.extend(
            [
                "[[stage]]",
                f'stage_id = "{stage.stage_id}"',
                f'title = "{stage.title}"',
                f'owner_package = "{stage.owner_package}"',
                f'handoff_class = "{stage.handoff_class}"',
                f'summary = "{stage.summary}"',
                f'docs_path = "{stage.docs_path}"',
                f'primary_path = "{stage.primary_path}"',
                "",
            ]
        )
    for handoff in report.handoffs:
        lines.extend(
            [
                "[[handoff]]",
                f'handoff_class = "{handoff.handoff_class}"',
                f'owner_package = "{handoff.owner_package}"',
                f"producer_packages = [{_render_tuple(handoff.producer_packages)}]",
                f"consumer_packages = [{_render_tuple(handoff.consumer_packages)}]",
                f"examples = [{_render_tuple(handoff.examples)}]",
                f'summary = "{handoff.summary}"',
                "",
            ]
        )
    for package in report.packages:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{package.distribution_name}"',
                f'role_kind = "{package.role_kind}"',
                f'role_summary = "{package.role_summary}"',
                f'docs_path = "{package.docs_path}"',
                f'readme_path = "{package.readme_path}"',
                (
                    "allowed_outbound_imports = "
                    f"[{_render_tuple(package.allowed_outbound_imports)}]"
                ),
                (
                    "forbidden_outbound_imports = "
                    f"[{_render_tuple(package.forbidden_outbound_imports)}]"
                ),
                f"owned_handoff_classes = [{_render_tuple(package.owned_handoff_classes)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: RepositoryProductShapeReport) -> bool:
    if not REPOSITORY_PRODUCT_SHAPE_PATH.exists():
        return False
    return REPOSITORY_PRODUCT_SHAPE_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_repository_product_shape_report()
    failures = validate_repository_product_shape()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("repository product shape is up to date")
            return 0
        print("repository product shape is stale; regenerate it")
        return 1
    REPOSITORY_PRODUCT_SHAPE_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated repository product shape")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the repository product shape."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the repository product shape is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
