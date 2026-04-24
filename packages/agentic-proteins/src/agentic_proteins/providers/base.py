"""Compatibility forwarding module for canonical runtime provider ownership."""

from bijux_proteomics_runtime.providers import base as _runtime_base
from bijux_proteomics_runtime.providers.base import *  # noqa: F401,F403

_time_left = _runtime_base._time_left
