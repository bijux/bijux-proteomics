from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_foundation.testing.generated_file_markers import (
    GeneratedFileMarkerKind,
    detect_generated_file_marker,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "GENERATED_FILE_MARKER_POLICY_PATH",
    "GeneratedFileMarkerPolicy",
    "GeneratedFileMarkerSurface",
    "GeneratedFileMarkerViolation",
    "build_generated_file_marker_violations",
    "load_generated_file_marker_policy",
    "run",
]


GENERATED_FILE_MARKER_POLICY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "generated-file-marker-surfaces.toml"
)
GENERATED_FILE_MARKER_ARTIFACTS_DIR = (
    REPO_ROOT / "artifacts" / "root" / "generated-file-markers"
)


@dataclass(frozen=True)
class GeneratedFileMarkerSurface:
    """One governed family of tracked generated files."""

    path_glob: str
    marker_kind: GeneratedFileMarkerKind
    excluded_paths: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedFileMarkerPolicy:
    """Repository-owned generated-file marker policy."""

    name: str
    surfaces: tuple[GeneratedFileMarkerSurface, ...]


@dataclass(frozen=True)
class GeneratedFileMarkerViolation:
    """One generated-file marker contract failure."""

    relative_path: str
    code: str
    detail: str


def load_generated_file_marker_policy(
    path: Path = GENERATED_FILE_MARKER_POLICY_PATH,
) -> GeneratedFileMarkerPolicy:
    """Load the repository-owned generated-file marker policy."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    policy_table = cast(dict[str, Any], data["policy"])
    surface_tables = cast(list[dict[str, Any]], data["surface"])
    return GeneratedFileMarkerPolicy(
        name=str(policy_table["name"]),
        surfaces=tuple(
            GeneratedFileMarkerSurface(
                path_glob=str(entry["path_glob"]),
                marker_kind=GeneratedFileMarkerKind(str(entry["marker_kind"])),
                excluded_paths=tuple(
                    str(value) for value in cast(list[str], entry["excluded_paths"])
                ),
            )
            for entry in surface_tables
        ),
    )


def build_generated_file_marker_violations(
    policy: GeneratedFileMarkerPolicy | None = None,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[GeneratedFileMarkerViolation, ...]:
    """Return live generated-file marker policy violations."""

    policy = policy or load_generated_file_marker_policy()
    violations: list[GeneratedFileMarkerViolation] = []
    for surface in policy.surfaces:
        excluded_paths = set(surface.excluded_paths)
        for path in sorted(repo_root.glob(surface.path_glob)):
            relative_path = path.relative_to(repo_root).as_posix()
            if relative_path in excluded_paths:
                continue
            marker = detect_generated_file_marker(path)
            if marker is None:
                violations.append(
                    GeneratedFileMarkerViolation(
                        relative_path=relative_path,
                        code="missing-generated-file-marker",
                        detail=(
                            f"{relative_path} matches governed generated surface "
                            f"{surface.path_glob} but is missing the required "
                            f"{surface.marker_kind.value} marker"
                        ),
                    )
                )
                continue
            if marker.kind != surface.marker_kind:
                violations.append(
                    GeneratedFileMarkerViolation(
                        relative_path=relative_path,
                        code="wrong-generated-file-marker-kind",
                        detail=(
                            f"{relative_path} carries {marker.kind.value} but governed "
                            f"surface {surface.path_glob} requires "
                            f"{surface.marker_kind.value}"
                        ),
                    )
                )
                continue
            if (
                surface.marker_kind == GeneratedFileMarkerKind.GENERATED_HEADER
                and marker.regenerate_command is None
            ):
                violations.append(
                    GeneratedFileMarkerViolation(
                        relative_path=relative_path,
                        code="missing-regenerate-command",
                        detail=(
                            f"{relative_path} is marked generated but does not expose "
                            "a regenerate command"
                        ),
                    )
                )
    return tuple(sorted(violations, key=lambda item: (item.code, item.relative_path)))


def run(*, check: bool = False) -> int:
    """Validate the repository-owned generated-file marker policy."""

    violations = build_generated_file_marker_violations()
    GENERATED_FILE_MARKER_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = GENERATED_FILE_MARKER_ARTIFACTS_DIR / "validation.txt"
    if violations:
        artifact_path.write_text(
            "\n".join(violation.detail for violation in violations) + "\n",
            encoding="utf-8",
        )
        for violation in violations:
            print(violation.detail)
        return 1
    artifact_path.write_text(
        "generated file marker policy passed\n",
        encoding="utf-8",
    )
    print("generated file marker policy passed")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Validate that repository-owned generated files carry the governed "
            "marker headers required for intentional quality exclusions."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the repository-owned generated-file marker policy finds violations.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
