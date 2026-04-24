"""Compatibility forwarding module for canonical runtime API ownership."""

from bijux_proteomics_runtime.api import errors as _runtime_errors
from bijux_proteomics_runtime.api.errors import *  # noqa: F401,F403

_ERROR_TYPES = _runtime_errors._ERROR_TYPES
_METHOD_NOT_ALLOWED_TYPE = _runtime_errors._METHOD_NOT_ALLOWED_TYPE
_BAD_REQUEST_TYPE = _runtime_errors._BAD_REQUEST_TYPE
