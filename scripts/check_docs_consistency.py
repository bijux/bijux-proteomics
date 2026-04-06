#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Canonical docs consistency gate for MkDocs navigation and basic page shape."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
MKDOCS_PATH = ROOT / "mkdocs.yml"

MD_REF_RE = re.compile(r"([A-Za-z0-9_./-]+\.md)")


def _nav_refs() -> set[Path]:
    if not MKDOCS_PATH.exists():
        return set()
    text = MKDOCS_PATH.read_text()
    refs: set[Path] = set()
    for match in MD_REF_RE.findall(text):
        refs.add(Path(match))
    return refs


def main() -> int:
    failures: list[str] = []
    if not DOCS_DIR.exists():
        print("docs/ missing")
        return 1

    nav_refs = _nav_refs()
    if not nav_refs:
        failures.append("mkdocs_nav_missing")

    for ref in sorted(nav_refs):
        path = DOCS_DIR / ref
        if not path.exists():
            failures.append(f"missing_nav_ref: {ref}")
        elif path.suffix == ".md":
            text = path.read_text().strip()
            if not text:
                failures.append(f"empty_doc: {ref}")
            if "\n# " not in f"\n{text}":
                failures.append(f"missing_h1: {ref}")

    for doc in sorted(DOCS_DIR.rglob("*.md")):
        rel = doc.relative_to(DOCS_DIR)
        if rel not in nav_refs:
            failures.append(f"orphan_doc: {rel}")

    if failures:
        for failure in failures:
            print(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
