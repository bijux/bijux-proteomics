"""Repo-root checkout loader for the canonical knowledge package."""

from __future__ import annotations

from pathlib import Path

from checkout_package_loader import load_checkout_package


load_checkout_package(
    __name__,
    repository_root=Path(__file__).resolve().parent.parent,
    package_directory="bijux-proteomics-knowledge",
    import_name="bijux_proteomics_knowledge",
)
