# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate store with deterministic IDs and versioned artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agentic_proteins.core.fingerprints import hash_payload
from agentic_proteins.domain.candidates.schema import Candidate


@dataclass(frozen=True)
class CandidateVersion:
    """CandidateVersion."""

    candidate_id: str
    version_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ArtifactRecord:
    """ArtifactRecord."""

    candidate_id: str
    version_id: str
    artifact_id: str
    name: str
    payload: dict[str, Any]


class CandidateStore:
    """CandidateStore."""

    def __init__(self, base_dir: Path) -> None:
        """__init__."""
        self._root = base_dir
        self._candidates_dir = self._root / "candidates"
        self._versions_dir = self._root / "versions"
        self._artifacts_dir = self._root / "artifacts"
        self._candidates_dir.mkdir(parents=True, exist_ok=True)
        self._versions_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def candidate_id_for(
        sequence: str, provenance: dict[str, Any] | None = None
    ) -> str:
        """candidate_id_for."""
        payload = {"sequence": sequence, "provenance": provenance or {}}
        return hash_payload(payload)

    @staticmethod
    def version_id_for(candidate: Candidate) -> str:
        """version_id_for."""
        payload = candidate.model_dump(mode="json")
        return hash_payload(payload)

    def create_candidate(self, candidate: Candidate) -> Candidate:
        """create_candidate."""
        candidate_id = candidate.candidate_id or self.candidate_id_for(
            candidate.sequence, candidate.provenance
        )
        stored = candidate.model_copy(update={"candidate_id": candidate_id})
        self._write_json(
            self._candidate_path(candidate_id), stored.model_dump(mode="json")
        )
        self.create_version(stored)
        return stored

    def get_candidate(self, candidate_id: str) -> Candidate:
        """get_candidate."""
        data = self._read_json(self._candidate_path(candidate_id))
        return Candidate.model_validate(data)

    def update_candidate(self, candidate: Candidate) -> Candidate:
        """update_candidate."""
        if not candidate.candidate_id:
            raise ValueError("candidate_id required for update")
        self._write_json(
            self._candidate_path(candidate.candidate_id),
            candidate.model_dump(mode="json"),
        )
        self.create_version(candidate)
        return candidate

    def delete_candidate(self, candidate_id: str) -> None:
        """delete_candidate."""
        path = self._candidate_path(candidate_id)
        if path.exists():
            path.unlink()

    def list_candidates(self) -> list[str]:
        """list_candidates."""
        return sorted(p.stem for p in self._candidates_dir.glob("*.json"))

    def create_version(self, candidate: Candidate) -> CandidateVersion:
        """create_version."""
        version_id = self.version_id_for(candidate)
        payload = candidate.model_dump(mode="json")
        version_path = self._version_path(candidate.candidate_id, version_id)
        self._write_json(version_path, payload)
        return CandidateVersion(
            candidate_id=candidate.candidate_id, version_id=version_id, payload=payload
        )

    def get_version(self, candidate_id: str, version_id: str) -> CandidateVersion:
        """get_version."""
        payload = self._read_json(self._version_path(candidate_id, version_id))
        return CandidateVersion(
            candidate_id=candidate_id, version_id=version_id, payload=payload
        )

    def list_versions(self, candidate_id: str) -> list[str]:
        """list_versions."""
        version_dir = self._versions_dir / candidate_id
        if not version_dir.exists():
            return []
        return sorted(p.stem for p in version_dir.glob("*.json"))

    def create_artifact(
        self,
        candidate_id: str,
        version_id: str,
        name: str,
        payload: dict[str, Any],
    ) -> ArtifactRecord:
        """create_artifact."""
        artifact_id = _hash_payload({"name": name, "payload": payload})
        path = self._artifact_path(candidate_id, version_id, artifact_id)
        self._write_json(path, {"name": name, "payload": payload})
        return ArtifactRecord(
            candidate_id=candidate_id,
            version_id=version_id,
            artifact_id=artifact_id,
            name=name,
            payload=payload,
        )

    def get_artifact(
        self, candidate_id: str, version_id: str, artifact_id: str
    ) -> ArtifactRecord:
        """get_artifact."""
        data = self._read_json(
            self._artifact_path(candidate_id, version_id, artifact_id)
        )
        return ArtifactRecord(
            candidate_id=candidate_id,
            version_id=version_id,
            artifact_id=artifact_id,
            name=data.get("name", ""),
            payload=data.get("payload", {}),
        )

    def list_artifacts(self, candidate_id: str, version_id: str) -> list[str]:
        """list_artifacts."""
        artifact_dir = self._artifacts_dir / candidate_id / version_id
        if not artifact_dir.exists():
            return []
        return sorted(p.stem for p in artifact_dir.glob("*.json"))

    def _candidate_path(self, candidate_id: str) -> Path:
        """_candidate_path."""
        self._ensure_safe_id(candidate_id, "candidate_id")
        return self._candidates_dir / f"{candidate_id}.json"

    def _version_path(self, candidate_id: str, version_id: str) -> Path:
        """_version_path."""
        self._ensure_safe_id(candidate_id, "candidate_id")
        self._ensure_safe_id(version_id, "version_id")
        version_dir = self._versions_dir / candidate_id
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir / f"{version_id}.json"

    def _artifact_path(
        self, candidate_id: str, version_id: str, artifact_id: str
    ) -> Path:
        """_artifact_path."""
        self._ensure_safe_id(candidate_id, "candidate_id")
        self._ensure_safe_id(version_id, "version_id")
        self._ensure_safe_id(artifact_id, "artifact_id")
        artifact_dir = self._artifacts_dir / candidate_id / version_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir / f"{artifact_id}.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        """_write_json."""
        path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        """_read_json."""
        return json.loads(path.read_text())

    @staticmethod
    def _ensure_safe_id(value: str, label: str) -> None:
        """_ensure_safe_id."""
        if not value or any(token in value for token in ("/", "\\", "..")):
            raise ValueError(f"Unsafe {label}: {value}")


def _hash_payload(payload: dict[str, Any]) -> str:
    """_hash_payload."""
    return hash_payload(payload)
