from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT
from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabModuleClassification,
)

__all__ = [
    "LAB_PACKET_ONLY_MODULES_PATH",
    "LabModuleShapeEntry",
    "LabModuleShapeGuard",
    "LabModuleShapeMetrics",
    "LabModuleShapeReport",
    "build_lab_module_shape_report",
    "run",
    "validate_lab_module_shapes",
]


@dataclass(frozen=True)
class LabModuleShapeEntry:
    """One lab module whose current shape is packet-only or reshaping-only."""

    module_path: str
    shape: str
    public_class_count: int
    public_function_count: int


@dataclass(frozen=True)
class LabModuleShapeMetrics:
    """Current counts for packet-only and reshaping-only lab modules."""

    packet_only_module_count: int
    reshaping_only_module_count: int
    entries: tuple[LabModuleShapeEntry, ...]


@dataclass(frozen=True)
class LabModuleShapeGuard:
    """Release-blocking ceilings over packet-only and reshaping-only growth."""

    max_packet_only_module_count: int
    max_reshaping_only_module_count: int
    max_total_reported_modules: int


@dataclass(frozen=True)
class LabModuleShapeReport:
    """Checked report over packet-only and reshaping-only lab modules."""

    metrics: LabModuleShapeMetrics
    guard: LabModuleShapeGuard


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_PACKET_ONLY_MODULES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-packet-only-modules.toml"
)
_PACKET_BASE_NAMES = {"JsonModel", "StrEnum", "Enum"}


def _base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _shape_entry(module_path: str, classification: LabModuleClassification) -> LabModuleShapeEntry | None:
    path = LAB_SRC_ROOT / module_path
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    public_classes = [
        node for node in tree.body if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    ]
    public_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]
    public_class_count = len(public_classes)
    public_function_count = len(public_functions)

    if classification is LabModuleClassification.THIN_ABSTRACTION:
        return LabModuleShapeEntry(
            module_path=module_path,
            shape="reshaping_only",
            public_class_count=public_class_count,
            public_function_count=public_function_count,
        )

    if classification is not LabModuleClassification.OPERATIONAL_VALUE:
        return None

    if public_function_count != 0 or public_class_count == 0:
        return None
    if not all(
        any(_base_name(base) in _PACKET_BASE_NAMES for base in class_node.bases)
        for class_node in public_classes
    ):
        return None
    return LabModuleShapeEntry(
        module_path=module_path,
        shape="packet_only",
        public_class_count=public_class_count,
        public_function_count=public_function_count,
    )


def build_lab_module_shape_report() -> LabModuleShapeReport:
    """Build the checked report over packet-only and reshaping-only lab modules."""

    entries = tuple(
        sorted(
            (
                entry
                for audit_entry in DEFAULT_LAB_MODULE_AUDIT
                for entry in [
                    _shape_entry(audit_entry.module_path, audit_entry.classification)
                ]
                if entry is not None
            ),
            key=lambda entry: (entry.shape, entry.module_path),
        )
    )
    packet_only_module_count = sum(1 for entry in entries if entry.shape == "packet_only")
    reshaping_only_module_count = sum(
        1 for entry in entries if entry.shape == "reshaping_only"
    )
    metrics = LabModuleShapeMetrics(
        packet_only_module_count=packet_only_module_count,
        reshaping_only_module_count=reshaping_only_module_count,
        entries=entries,
    )
    return LabModuleShapeReport(
        metrics=metrics,
        guard=LabModuleShapeGuard(
            max_packet_only_module_count=packet_only_module_count,
            max_reshaping_only_module_count=reshaping_only_module_count,
            max_total_reported_modules=len(entries),
        ),
    )


def validate_lab_module_shapes() -> tuple[str, ...]:
    """Fail when packet-only or reshaping-only module counts grow."""

    report = build_lab_module_shape_report()
    failures: list[str] = []
    if (
        report.metrics.packet_only_module_count
        > report.guard.max_packet_only_module_count
    ):
        failures.append("lab packet-only module count grew beyond the guarded baseline")
    if (
        report.metrics.reshaping_only_module_count
        > report.guard.max_reshaping_only_module_count
    ):
        failures.append(
            "lab reshaping-only module count grew beyond the guarded baseline"
        )
    if len(report.metrics.entries) > report.guard.max_total_reported_modules:
        failures.append("lab packet-only or reshaping-only module count grew")
    return tuple(failures)


def _toml_text(report: LabModuleShapeReport) -> str:
    lines = [
        "# Generated lab packet-only and reshaping-only module report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.lab_packet_only_modules",
        "",
        "[metrics]",
        f"packet_only_module_count = {report.metrics.packet_only_module_count}",
        f"reshaping_only_module_count = {report.metrics.reshaping_only_module_count}",
        "",
        "[guard]",
        f"max_packet_only_module_count = {report.guard.max_packet_only_module_count}",
        f"max_reshaping_only_module_count = {report.guard.max_reshaping_only_module_count}",
        f"max_total_reported_modules = {report.guard.max_total_reported_modules}",
        "",
    ]
    for entry in report.metrics.entries:
        lines.extend(
            [
                "[[module]]",
                f'module_path = "{entry.module_path}"',
                f'shape = "{entry.shape}"',
                f"public_class_count = {entry.public_class_count}",
                f"public_function_count = {entry.public_function_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: LabModuleShapeReport) -> bool:
    if not LAB_PACKET_ONLY_MODULES_PATH.exists():
        return False
    return LAB_PACKET_ONLY_MODULES_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_lab_module_shape_report()
    failures = validate_lab_module_shapes()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print(
                "lab packet-only and reshaping-only module report is up to date"
            )
            return 0
        print("lab packet-only and reshaping-only module report is stale; regenerate it")
        return 1
    LAB_PACKET_ONLY_MODULES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab packet-only and reshaping-only module report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab packet-only and reshaping-only module report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab packet-only and reshaping-only module report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
