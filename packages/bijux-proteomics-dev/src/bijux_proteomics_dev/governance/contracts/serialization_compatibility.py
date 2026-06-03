from __future__ import annotations

from dataclasses import dataclass

from bijux_proteomics_foundation import (
    DocumentSchema,
    hash_model,
)
from bijux_proteomics_foundation import (
    fingerprint_model as fingerprint_knowledge_model,
)
from bijux_proteomics_foundation import (
    fingerprint_model as fingerprint_lab_model,
)
from bijux_proteomics_foundation import (
    to_canonical_json as knowledge_to_canonical_json,
)
from bijux_proteomics_foundation import (
    to_canonical_json as lab_to_canonical_json,
)
from bijux_proteomics_foundation.compatibility import (
    SchemaCompatibility,
    assess_schema_compatibility,
)
from bijux_proteomics_knowledge.contracts.schema import evaluate_schema_compatibility
from bijux_proteomics_knowledge.memory.models.evidence import EvidenceBundle
from bijux_proteomics_lab.handoffs.artifacts import (
    build_lab_artifact_upgrade_advisory,
    evaluate_lab_artifact_with_registry,
)
from bijux_proteomics_lab.handoffs.serialization import (
    build_canonical_artifact_envelope,
    verify_canonical_artifact_envelope,
)
from bijux_proteomics_lab.planning.assays import ExperimentPlan

__all__ = [
    "PackageSerializationCompatibilityResult",
    "build_package_serialization_compatibility_matrix",
]


@dataclass(frozen=True)
class PackageSerializationCompatibilityResult:
    """Stable cross-version serialization result for one package artifact."""

    case_id: str
    package_name: str
    artifact_kind: str
    schema_version: str
    compatibility_status: str
    compatible: bool
    roundtrip_stable: bool
    content_fingerprint: str
    notes: tuple[str, ...]


def _foundation_result(schema_version: str) -> PackageSerializationCompatibilityResult:
    schema = DocumentSchema(
        schema_version=schema_version,
        created_by="bijux-proteomics-foundation",
        document_kind="compatibility_probe",
        package_name="bijux-proteomics-foundation",
    )
    serialized = schema.to_stable_json()
    reparsed = DocumentSchema.model_validate_json(serialized)
    compatibility = assess_schema_compatibility(schema_version, "1.0.0")
    return PackageSerializationCompatibilityResult(
        case_id=f"foundation-document-schema-{schema_version}",
        package_name="bijux-proteomics-foundation",
        artifact_kind="document_schema",
        schema_version=schema_version,
        compatibility_status=compatibility.value,
        compatible=compatibility is SchemaCompatibility.COMPATIBLE,
        roundtrip_stable=reparsed.to_stable_json() == serialized,
        content_fingerprint=hash_model(schema),
        notes=(
            "foundation schema metadata remains parseable across supported minor revisions",
        ),
    )


def _knowledge_result(schema_version: str) -> PackageSerializationCompatibilityResult:
    bundle = EvidenceBundle(
        bundle_id=f"bundle-{schema_version}",
        target_id="target-serialization-compatibility",
        document_schema=DocumentSchema(
            schema_version=schema_version,
            created_by="bijux-proteomics-knowledge",
            document_kind="evidence_bundle",
            package_name="bijux-proteomics-knowledge",
        ),
    )
    serialized = knowledge_to_canonical_json(bundle)
    reparsed = EvidenceBundle.model_validate_json(serialized)
    compatibility = evaluate_schema_compatibility(bundle.document_schema)
    return PackageSerializationCompatibilityResult(
        case_id=f"knowledge-evidence-bundle-{schema_version}",
        package_name="bijux-proteomics-knowledge",
        artifact_kind="evidence_bundle",
        schema_version=schema_version,
        compatibility_status="compatible"
        if compatibility.compatible
        else "incompatible",
        compatible=compatibility.compatible,
        roundtrip_stable=knowledge_to_canonical_json(reparsed) == serialized,
        content_fingerprint=fingerprint_knowledge_model(bundle),
        notes=tuple(compatibility.notes),
    )


def _lab_result(schema_version: str) -> PackageSerializationCompatibilityResult:
    plan = ExperimentPlan(
        program_id=f"plan-{schema_version}",
        document_schema=DocumentSchema(
            schema_version=schema_version,
            created_by="bijux-proteomics-lab",
            document_kind="plan",
            package_name="bijux-proteomics-lab",
        ),
        evidence_gaps=["structure"],
    )
    envelope = build_canonical_artifact_envelope(
        plan,
        artifact_kind="plan",
        schema=plan.document_schema,
    )
    reparsed = ExperimentPlan.model_validate(envelope.payload_raw_json)
    compatibility = evaluate_lab_artifact_with_registry(
        plan.document_schema, artifact_kind="plan"
    )
    advisory = build_lab_artifact_upgrade_advisory(plan.document_schema)
    notes = [*compatibility.notes, *advisory.notes]
    return PackageSerializationCompatibilityResult(
        case_id=f"lab-experiment-plan-{schema_version}",
        package_name="bijux-proteomics-lab",
        artifact_kind="plan",
        schema_version=schema_version,
        compatibility_status="compatible"
        if compatibility.compatible
        else "incompatible",
        compatible=compatibility.compatible,
        roundtrip_stable=(
            lab_to_canonical_json(reparsed) == lab_to_canonical_json(plan)
            and verify_canonical_artifact_envelope(envelope)
        ),
        content_fingerprint=fingerprint_lab_model(plan),
        notes=tuple(notes),
    )


def build_package_serialization_compatibility_matrix() -> tuple[
    PackageSerializationCompatibilityResult, ...
]:
    """Build the cross-version package serialization compatibility matrix."""
    versions = ("1.0.0", "1.1.0")
    rows = [
        *(_foundation_result(version) for version in versions),
        *(_knowledge_result(version) for version in versions),
        *(_lab_result(version) for version in versions),
    ]
    return tuple(sorted(rows, key=lambda row: row.case_id))
