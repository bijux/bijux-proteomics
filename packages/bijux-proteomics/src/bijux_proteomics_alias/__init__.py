"""Internal version metadata helper for the `bijux-proteomics` distribution alias."""

from __future__ import annotations

from importlib import metadata

try:
    __version__ = metadata.version("bijux-proteomics")
except metadata.PackageNotFoundError:
    __version__ = "0.3.6"

__all__ = ["__version__"]
