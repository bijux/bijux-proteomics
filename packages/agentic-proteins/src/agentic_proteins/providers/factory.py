"""Compatibility forwarding module for canonical runtime provider ownership."""

from bijux_proteomics_runtime.providers import factory as _runtime_factory
from bijux_proteomics_runtime.providers.factory import *  # noqa: F401,F403

_require_module = _runtime_factory._require_module
