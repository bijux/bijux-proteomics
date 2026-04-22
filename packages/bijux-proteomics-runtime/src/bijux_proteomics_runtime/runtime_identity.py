"""Canonical runtime identity and ownership constants."""

CANONICAL_RUNTIME_PACKAGE = "bijux-proteomics-runtime"
CANONICAL_RUNTIME_IMPORT = "bijux_proteomics_runtime"


def runtime_banner() -> str:
    """Return a stable runtime banner for CLI and diagnostics surfaces."""
    return f"{CANONICAL_RUNTIME_PACKAGE} canonical runtime surface"
