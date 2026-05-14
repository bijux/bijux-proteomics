"""Module entrypoint for the `proteomics-core` CLI alias."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
