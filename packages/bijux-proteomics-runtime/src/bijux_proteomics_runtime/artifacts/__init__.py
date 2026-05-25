"""Artifact-owned runtime step contracts."""

from __future__ import annotations

from bijux_proteomics_runtime.artifacts.steps import StepArtifact, build_step_artifact
from bijux_proteomics_runtime.support.primitives.stability import sealed

__all__ = ["StepArtifact", "build_step_artifact"]

sealed()
