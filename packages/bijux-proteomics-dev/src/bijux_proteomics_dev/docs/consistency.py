"""Canonical docs consistency gate for MkDocs navigation and page shape."""

from __future__ import annotations

from pathlib import Path
import re

MD_REF_RE = re.compile(r"([A-Za-z0-9_./-]+\.md)")


def nav_refs(mkdocs_path: Path) -> set[Path]:
    if not mkdocs_path.exists():
        return set()
    text = mkdocs_path.read_text(encoding="utf-8")
    refs: set[Path] = set()
    for match in MD_REF_RE.findall(text):
        refs.add(Path(match))
    return refs


def run(repo_root: Path) -> int:
    docs_dir = repo_root / "docs"
    mkdocs_path = repo_root / "mkdocs.yml"
    failures: list[str] = []

    if not docs_dir.exists():
        print("docs/ missing")
        return 1

    references = nav_refs(mkdocs_path)
    if not references:
        failures.append("mkdocs_nav_missing")

    for ref in sorted(references):
        path = docs_dir / ref
        if not path.exists():
            failures.append(f"missing_nav_ref: {ref}")
        elif path.suffix == ".md":
            text = path.read_text(encoding="utf-8").strip()
            if not text:
                failures.append(f"empty_doc: {ref}")
            if "\n# " not in f"\n{text}":
                failures.append(f"missing_h1: {ref}")

    for doc in sorted(docs_dir.rglob("*.md")):
        rel = doc.relative_to(docs_dir)
        if rel not in references:
            failures.append(f"orphan_doc: {rel}")

    if failures:
        for failure in failures:
            print(failure)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
