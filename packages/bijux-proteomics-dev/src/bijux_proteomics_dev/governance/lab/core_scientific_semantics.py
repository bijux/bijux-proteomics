from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "ALLOWED_SCIENTIFIC_IMPORTS",
    "LAB_CORE_SCIENTIFIC_SEMANTICS_PATH",
    "LabCoreScientificImport",
    "build_lab_core_scientific_semantics_report",
    "run",
    "validate_lab_core_scientific_semantics",
]


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_CORE_SCIENTIFIC_SEMANTICS_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "lab-core-scientific-semantics.toml"
)
SCIENTIFIC_IMPORT_PREFIXES = (
    "bijux_proteomics.dia",
    "bijux_proteomics.io.formats",
    "bijux_proteomics.io.ingestion",
    "bijux_proteomics.ptm",
    "bijux_proteomics.ptm.review",
)
ALLOWED_SCIENTIFIC_IMPORTS = (
    ("benchmarks/claims.py", "bijux_proteomics.dia"),
    ("benchmarks/claims.py", "bijux_proteomics.io.ingestion"),
    ("design/experiments.py", "bijux_proteomics.io.formats"),
    ("handoffs/ptm.py", "bijux_proteomics.ptm"),
    ("handoffs/ptm.py", "bijux_proteomics.ptm.review"),
)


@dataclass(frozen=True)
class LabCoreScientificImport:
    """One governed lab import of core scientific owner semantics."""

    importer_module_path: str
    imported_module_name: str


def _source_modules() -> tuple[Path, ...]:
    return tuple(sorted(LAB_SRC_ROOT.rglob("*.py")))


def build_lab_core_scientific_semantics_report() -> tuple[LabCoreScientificImport, ...]:
    """Build the checked report of lab imports of core scientific owner semantics."""

    entries: set[LabCoreScientificImport] = set()
    for path in _source_modules():
        relative = path.relative_to(LAB_SRC_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(SCIENTIFIC_IMPORT_PREFIXES):
                        entries.add(
                            LabCoreScientificImport(
                                importer_module_path=relative,
                                imported_module_name=alias.name,
                            )
                        )
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                if node.module.startswith(SCIENTIFIC_IMPORT_PREFIXES):
                    entries.add(
                        LabCoreScientificImport(
                            importer_module_path=relative,
                            imported_module_name=node.module,
                        )
                    )
    return tuple(
        sorted(entries, key=lambda entry: (entry.importer_module_path, entry.imported_module_name))
    )


def validate_lab_core_scientific_semantics(
    report: tuple[LabCoreScientificImport, ...] | None = None,
) -> tuple[str, ...]:
    """Fail release when lab starts owning broader core scientific semantics."""

    report = report or build_lab_core_scientific_semantics_report()
    observed = tuple(
        (entry.importer_module_path, entry.imported_module_name) for entry in report
    )
    failures: list[str] = []
    if observed != ALLOWED_SCIENTIFIC_IMPORTS:
        failures.append(
            "lab core scientific imports drifted from the governed operational seam: "
            + ", ".join(f"{path} -> {module}" for path, module in observed)
        )
    unexpected = [
        f"{entry.importer_module_path} -> {entry.imported_module_name}"
        for entry in report
        if (entry.importer_module_path, entry.imported_module_name)
        not in ALLOWED_SCIENTIFIC_IMPORTS
    ]
    if unexpected:
        failures.append(
            "lab added new direct imports of core scientific owner semantics: "
            + ", ".join(sorted(unexpected))
        )
    return tuple(failures)


def _toml_text(report: tuple[LabCoreScientificImport, ...]) -> str:
    lines = [
        "# Generated lab core scientific semantics report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.lab.core_scientific_semantics",
        "",
    ]
    for entry in report:
        lines.extend(
            [
                "[[dependency]]",
                f'importer_module_path = "{entry.importer_module_path}"',
                f'imported_module_name = "{entry.imported_module_name}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: tuple[LabCoreScientificImport, ...]) -> bool:
    if not LAB_CORE_SCIENTIFIC_SEMANTICS_PATH.exists():
        return False
    return LAB_CORE_SCIENTIFIC_SEMANTICS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_lab_core_scientific_semantics_report()
    failures = validate_lab_core_scientific_semantics(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab core scientific semantics report is up to date")
            return 0
        print("lab core scientific semantics report is stale; regenerate it")
        return 1
    LAB_CORE_SCIENTIFIC_SEMANTICS_PATH.write_text(
        _toml_text(report), encoding="utf-8"
    )
    print("generated lab core scientific semantics report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab core scientific semantics report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab core scientific semantics report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
