"""Compatibility forwarding module for canonical runtime validation ownership."""

from bijux_proteomics_runtime.validation import agents as _runtime_agents
from bijux_proteomics_runtime.validation.agents import *  # noqa: F401,F403

_minimal_payload = _runtime_agents._minimal_payload
_placeholder_for_type = _runtime_agents._placeholder_for_type
