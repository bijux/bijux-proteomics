"""Canonical runtime identity and ownership constants."""

CANONICAL_RUNTIME_PACKAGE = "bijux-proteomics-runtime"
CANONICAL_RUNTIME_IMPORT = "bijux_proteomics_runtime"
CANONICAL_RUNTIME_DESCRIPTION = (
    "HTTP API exposing the same capabilities as the CLI, nothing more."
)


def runtime_title() -> str:
    """Return the stable runtime title for CLI, API, and diagnostics surfaces."""

    return CANONICAL_RUNTIME_PACKAGE


def runtime_description() -> str:
    """Return the stable runtime description for public app surfaces."""

    return CANONICAL_RUNTIME_DESCRIPTION


def runtime_banner() -> str:
    """Return a stable runtime banner for CLI and diagnostics surfaces."""

    return f"{runtime_title()} canonical runtime surface"
