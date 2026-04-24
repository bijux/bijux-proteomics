"""Compatibility forwarding module for canonical runtime ownership."""

from bijux_proteomics_runtime.runtime.control import artifacts as _runtime_artifacts
from bijux_proteomics_runtime.runtime.control.artifacts import *  # noqa: F401,F403

_sign_payload = _runtime_artifacts._sign_payload
