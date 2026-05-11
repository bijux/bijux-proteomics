"""Explicit public API contracts for publishable workspace packages."""

from __future__ import annotations

from dataclasses import dataclass
import importlib

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_import_path,
)

__all__ = [
    "PackagePublicSurfaceContract",
    "default_public_surface_contracts",
    "validate_public_surface_contracts",
]


@dataclass(frozen=True)
class PackagePublicSurfaceContract:
    """Supported import surfaces for one publishable package."""

    distribution_name: str
    import_root: str
    supported_modules: tuple[str, ...] = ()
    supported_attributes: tuple[str, ...] = ()


def default_public_surface_contracts() -> tuple[PackagePublicSurfaceContract, ...]:
    """Return the supported public import surfaces for each package."""
    return (
        PackagePublicSurfaceContract(
            distribution_name="agentic-proteins",
            import_root="agentic_proteins",
            supported_attributes=("AppConfig", "create_app", "RunManager", "cli"),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics",
            import_root="bijux_proteomics_alias",
            supported_attributes=("__version__",),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-core",
            import_root="bijux_proteomics",
            supported_attributes=(
                "DigestPolicy",
                "parse_fasta_document",
                "parse_experimental_design_table",
                "build_normalized_run_bundle",
                "build_fdr_audit_trail",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-foundation",
            import_root="bijux_proteomics_foundation",
            supported_attributes=(
                "DocumentSchema",
                "JsonModel",
                "hash_payload",
                "to_canonical_json",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-intelligence",
            import_root="bijux_proteomics_intelligence",
            supported_attributes=(
                "candidates",
                "governance",
                "interpretation",
                "judgment",
                "learning",
                "posture",
                "reviews",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-knowledge",
            import_root="bijux_proteomics_knowledge",
            supported_attributes=(
                "EvidenceBundle",
                "EvidenceClaim",
                "EvidenceRecord",
                "KnowledgeDecisionBrief",
                "evaluate_schema_compatibility",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-lab",
            import_root="bijux_proteomics_lab",
            supported_attributes=(
                "plan_experiment_batches",
                "build_advisory_assay_plan",
                "build_executable_assay_plan",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-runtime",
            import_root="bijux_proteomics_runtime",
            supported_attributes=("AppConfig", "create_app", "RunManager", "cli"),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics",
            import_root="proteomics",
            supported_attributes=(
                "DigestPolicy",
                "parse_fasta_document",
                "parse_experimental_design_table",
                "build_normalized_run_bundle",
                "build_fdr_audit_trail",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-core",
            import_root="proteomics_core",
            supported_attributes=(
                "DigestPolicy",
                "parse_fasta_document",
                "parse_experimental_design_table",
                "build_normalized_run_bundle",
                "build_fdr_audit_trail",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-foundation",
            import_root="proteomics_foundation",
            supported_attributes=(
                "DocumentSchema",
                "JsonModel",
                "hash_payload",
                "to_canonical_json",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-intelligence",
            import_root="proteomics_intelligence",
            supported_attributes=(
                "candidates",
                "governance",
                "interpretation",
                "judgment",
                "learning",
                "posture",
                "reviews",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-knowledge",
            import_root="proteomics_knowledge",
            supported_attributes=(
                "EvidenceBundle",
                "EvidenceClaim",
                "EvidenceRecord",
                "KnowledgeDecisionBrief",
                "evaluate_schema_compatibility",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-lab",
            import_root="proteomics_lab",
            supported_attributes=(
                "plan_experiment_batches",
                "build_advisory_assay_plan",
                "build_executable_assay_plan",
            ),
        ),
        PackagePublicSurfaceContract(
            distribution_name="proteomics-runtime",
            import_root="proteomics_runtime",
            supported_attributes=("AppConfig", "create_app", "RunManager", "cli"),
        ),
        PackagePublicSurfaceContract(
            distribution_name="bijux-proteomics-dev",
            import_root="bijux_proteomics_dev",
            supported_modules=(
                "bijux_proteomics_dev.governance.contracts.freeze_contracts",
                "bijux_proteomics_dev.governance.package_shape.public_surfaces",
                "bijux_proteomics_dev.quality.gates.fast_gate",
                "bijux_proteomics_dev.quality.architecture.runtime_boundaries",
            ),
        ),
    )


def validate_public_surface_contracts(
    contracts: tuple[PackagePublicSurfaceContract, ...] | None = None,
) -> list[str]:
    """Validate that every declared public surface is importable and present."""
    contracts = contracts or default_public_surface_contracts()
    failures: list[str] = []
    with workspace_import_path():
        for contract in contracts:
            try:
                root_module = importlib.import_module(contract.import_root)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{contract.distribution_name}: failed to import {contract.import_root} ({exc})"
                )
                continue
            for attribute in contract.supported_attributes:
                if not hasattr(root_module, attribute):
                    failures.append(
                        f"{contract.distribution_name}: missing public attribute {contract.import_root}.{attribute}"
                    )
            for module_name in contract.supported_modules:
                try:
                    importlib.import_module(module_name)
                except Exception as exc:  # noqa: BLE001
                    failures.append(
                        f"{contract.distribution_name}: failed to import supported module {module_name} ({exc})"
                    )
    return failures
