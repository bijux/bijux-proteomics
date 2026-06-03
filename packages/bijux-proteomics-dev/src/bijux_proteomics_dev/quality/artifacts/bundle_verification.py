from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bijux_proteomics_dev.quality.artifacts.artifact_schemas import (
    load_high_value_artifact_schemas,
)

__all__ = [
    "BundleVerificationIssue",
    "BundleVerificationProfile",
    "BundleVerificationReport",
    "bundle_verification_profile_manifest_path",
    "load_bundle_verification_profiles",
    "validate_bundle_verification_profiles",
    "verify_bundle_payload",
]


@dataclass(frozen=True)
class BundleVerificationProfile:
    """One documented verification profile for a durable bundle kind."""

    document_kind: str
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class BundleVerificationIssue:
    """One issue found while verifying a durable bundle payload."""

    code: str
    detail: str


@dataclass(frozen=True)
class BundleVerificationReport:
    """Verification report for one durable bundle payload."""

    document_kind: str
    valid: bool
    verified_fields: tuple[str, ...]
    issues: tuple[BundleVerificationIssue, ...]


def bundle_verification_profile_manifest_path(repo_root: Path) -> Path:
    """Return the bundle verification profile manifest path."""
    return (
        repo_root
        / "configs"
        / "package-governance"
        / "bundle-verification-profiles.toml"
    )


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_bundle_verification_profiles(
    repo_root: Path,
) -> tuple[BundleVerificationProfile, ...]:
    """Load the durable bundle verification profiles."""
    raw = _load_toml(bundle_verification_profile_manifest_path(repo_root))
    return tuple(
        BundleVerificationProfile(
            document_kind=str(item["document_kind"]),
            required_fields=tuple(str(value) for value in item["required_fields"]),
        )
        for item in raw["bundle_profile"]
    )


def validate_bundle_verification_profiles(
    repo_root: Path,
) -> tuple[BundleVerificationIssue, ...]:
    """Validate bundle verification profiles against the high-value artifact registry."""
    profiles = load_bundle_verification_profiles(repo_root)
    known_document_kinds = {
        schema.document_kind for schema in load_high_value_artifact_schemas(repo_root)
    }
    allowed_non_registry_kinds = {
        "quant_artifact_bundle",
        "review_ready_evidence_bundle",
    }
    issues: list[BundleVerificationIssue] = []
    seen: set[str] = set()

    for profile in profiles:
        if profile.document_kind in seen:
            issues.append(
                BundleVerificationIssue(
                    code="duplicate-document-kind",
                    detail=f"duplicate bundle verification profile for {profile.document_kind}",
                )
            )
        seen.add(profile.document_kind)
        if (
            profile.document_kind not in known_document_kinds
            and profile.document_kind not in allowed_non_registry_kinds
        ):
            issues.append(
                BundleVerificationIssue(
                    code="unknown-document-kind",
                    detail=f"bundle verification profile references unknown document kind {profile.document_kind}",
                )
            )
        if not profile.required_fields:
            issues.append(
                BundleVerificationIssue(
                    code="missing-required-fields",
                    detail=f"bundle verification profile has no required fields for {profile.document_kind}",
                )
            )
    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def verify_bundle_payload(
    payload: dict[str, Any],
    *,
    document_kind: str,
    repo_root: Path,
) -> BundleVerificationReport:
    """Verify one durable bundle payload against the declared profile and schema version."""
    profiles = {
        profile.document_kind: profile
        for profile in load_bundle_verification_profiles(repo_root)
    }
    profile = profiles.get(document_kind)
    if profile is None:
        raise ValueError(f"no verification profile for {document_kind}")

    schema_by_kind = {
        schema.document_kind: schema
        for schema in load_high_value_artifact_schemas(repo_root)
    }
    issues: list[BundleVerificationIssue] = []
    verified_fields: list[str] = []
    observed_schema = payload.get("document_schema")
    if not isinstance(observed_schema, dict):
        issues.append(
            BundleVerificationIssue(
                code="missing-document-schema",
                detail="bundle payload is missing a document_schema object",
            )
        )
    else:
        if observed_schema.get("document_kind") != document_kind:
            issues.append(
                BundleVerificationIssue(
                    code="document-kind-mismatch",
                    detail=(
                        f"bundle payload declares {observed_schema.get('document_kind')} "
                        f"but verifier expected {document_kind}"
                    ),
                )
            )
        declared_schema = schema_by_kind.get(document_kind)
        if declared_schema is not None:
            if observed_schema.get("schema_version") != declared_schema.schema_version:
                issues.append(
                    BundleVerificationIssue(
                        code="schema-version-mismatch",
                        detail=(
                            f"bundle payload uses schema version {observed_schema.get('schema_version')} "
                            f"but registry expects {declared_schema.schema_version}"
                        ),
                    )
                )
            else:
                verified_fields.append("document_schema.schema_version")

    for field_name in profile.required_fields:
        if field_name not in payload:
            issues.append(
                BundleVerificationIssue(
                    code="missing-required-field",
                    detail=f"bundle payload is missing required field {field_name}",
                )
            )
        else:
            verified_fields.append(field_name)

    return BundleVerificationReport(
        document_kind=document_kind,
        valid=not issues,
        verified_fields=tuple(sorted(set(verified_fields))),
        issues=tuple(issues),
    )
