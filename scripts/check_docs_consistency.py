#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Documentation consistency gate."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
SRC_DIR = ROOT / "packages" / "agentic-proteins" / "src" / "agentic_proteins"

MODULE_RE = re.compile(r"agentic_proteins\.[A-Za-z0-9_\.]+")
SRC_PATH_RE = re.compile(
    r"packages/(?:agentic-proteins/(?:src/agentic_proteins|tests)|bijux-proteomics-[a-z-]+/tests)/[A-Za-z0-9_\-/\.]+"
)
MKDOCS_RE = re.compile(r"([A-Za-z0-9_./-]+\.md)")
FUTURE_WORDS = re.compile(
    r"\b(will|planned|future|soon|upcoming|later|tbd|eventually)\b", re.IGNORECASE
)
VOICE_FORBIDDEN = re.compile(
    r"\b(maybe|might|could|should|probably|likely|perhaps|amazing|easy|simple|powerful|best)\b",
    re.IGNORECASE,
)
VOICE_PERSON = re.compile(r"\b(i|we|you|our|your|my|me)\b", re.IGNORECASE)
MAX_WORDS_PER_SENTENCE = 20
FRONT_MATTER_FIELDS = ("**Scope:**", "**Audience:**", "**Guarantees:**", "**Non-Goals:**")
ALLOWED_SECTION_ORDER = [
    "Overview",
    "Contracts",
    "Invariants",
    "Failure Modes",
    "Extension Points",
    "Exit Criteria",
]
ALLOWED_SECTIONS = set(ALLOWED_SECTION_ORDER)
CODE_REF_RE = re.compile(
    r"((packages/(?:agentic-proteins/(?:src/agentic_proteins|tests)|bijux-proteomics-[a-z-]+/tests)|scripts)/[A-Za-z0-9_./-]+\.py|api/[A-Za-z0-9_./-]+\.yaml)"
)
SECURITY_WORDS = re.compile(r"\b(security|sandbox|isolation|trust)\b", re.IGNORECASE)
DOC_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
DOC_NAME_RE = re.compile(r"\b[A-Za-z0-9_./-]+\.md\b")
SYMBOL_RE = re.compile(r"(agentic_proteins\.[A-Za-z0-9_\.]+)")



def _module_index() -> set[str]:
    modules: set[str] = {"agentic_proteins"}
    for path in SRC_DIR.rglob("*.py"):
        rel = path.relative_to(SRC_DIR)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        if not parts:
            continue
        modules.add("agentic_proteins." + ".".join(parts))
    return modules


def _path_exists(path_str: str) -> bool:
    return (ROOT / path_str).exists()


def main() -> int:
    if not DOCS_DIR.exists():
        print("docs/ missing")
        return 1

    mkdocs_path = ROOT / "mkdocs.yml"
    nav_refs: set[Path] = set()
    if mkdocs_path.exists():
        mkdocs_text = mkdocs_path.read_text()
        for entry in MKDOCS_RE.findall(mkdocs_text):
            nav_refs.add(Path(entry))

    modules = _module_index()
    failures: list[str] = []
    naming_path = DOCS_DIR / "NAMING.md"
    canonical: list[str] = []
    aliases: list[str] = []
    if naming_path.exists():
        current = None
        for line in naming_path.read_text().splitlines():
            if line.strip() == "Canonical names:":
                current = "canonical"
                continue
            if line.strip() == "Forbidden aliases:":
                current = "aliases"
                continue
            if line.strip().startswith("- "):
                item = line.strip()[2:].strip()
                if current == "canonical":
                    canonical.append(item)
                elif current == "aliases":
                    aliases.append(item)

    if mkdocs_path.exists():
        for ref in sorted(nav_refs):
            if ref.parts and ref.parts[0] == "docs":
                failures.append(f"nav_ref_outside_docs: {ref}")
                continue
            if not (DOCS_DIR / ref).exists():
                failures.append(f"missing_nav_ref: {ref}")

    for path in DOCS_DIR.rglob("*"):
        if path.is_dir() and path.name == "artifacts":
            failures.append(f"forbidden_docs_dir: {path.relative_to(DOCS_DIR)}")
        if path.is_dir():
            md_files = [p.name for p in path.glob("*.md")]
            if path != DOCS_DIR and md_files == ["index.md"]:
                failures.append(
                    f"index_only_dir: {path.relative_to(DOCS_DIR)}"
                )
    allow_non_lowercase = set()
    seen_titles: dict[str, Path] = {}
    for doc in sorted(DOCS_DIR.rglob("*.md")):
        rel = doc.relative_to(DOCS_DIR)
        if rel == Path("index.md"):
            continue
        rel = doc.relative_to(DOCS_DIR)
        if rel not in nav_refs:
            failures.append(f"orphan_doc: {rel}")
        text = doc.read_text()
        if len(text.strip().splitlines()) < 4:
            failures.append(f"empty_doc: {rel}")
        rel_from_root = doc.relative_to(ROOT)
        normalized = re.sub(r"\bPLANNED\b", "PLAN_STATE", text)
        if FUTURE_WORDS.search(normalized):
            failures.append(f"future_language: {rel_from_root}")
        if VOICE_FORBIDDEN.search(text):
            failures.append(f"voice_forbidden: {rel_from_root}")
        if VOICE_PERSON.search(text):
            failures.append(f"voice_person: {rel_from_root}")

        lines = text.splitlines()
        if not lines or not lines[0].startswith("# "):
            failures.append(f"missing_title: {rel_from_root}")
        else:
            title = lines[0][2:].strip()
            if title != rel.stem:
                failures.append(f"title_mismatch: {rel_from_root}")
            if title in seen_titles:
                failures.append(
                    f"duplicate_title: {title} in {rel_from_root} and {seen_titles[title]}"
                )
            else:
                seen_titles[title] = rel_from_root
        for idx, field in enumerate(FRONT_MATTER_FIELDS, start=2):
            if len(lines) <= idx or not lines[idx].strip().startswith(field):
                failures.append(f"missing_front_matter: {rel_from_root}")
                break
        if not any("Why:" in line for line in lines[:50]):
            failures.append(f"missing_why_line: {rel_from_root}")

        for line in lines:
            if line.startswith("###"):
                failures.append(f"section_depth_exceeded: {rel_from_root}")
        for line in lines:
            if line.startswith("## "):
                section = line[3:].strip()
                if section not in ALLOWED_SECTIONS:
                    failures.append(f"unknown_section: {section} in {rel_from_root}")

        sections = [line[3:].strip() for line in lines if line.startswith("## ")]
        if sections and sections != ALLOWED_SECTION_ORDER:
            failures.append(f"section_order_mismatch: {rel_from_root}")
        if not sections or sections[-1] != "Exit Criteria":
            failures.append(f"missing_exit_criteria: {rel_from_root}")
        if len(lines) > 300:
            failures.append(f"doc_too_long: {rel_from_root}")

        if not CODE_REF_RE.search(text):
            failures.append(f"missing_code_ref: {rel_from_root}")
        if rel.parts[0] != "security" and rel.name != "sandbox.md":
            for line in lines:
                if "security/" in line or "sandbox.md" in line:
                    continue
                if SECURITY_WORDS.search(line):
                    failures.append(
                        f"security_word_outside_security_docs: {rel_from_root}"
                    )
                    break

        link_targets = [target for _label, target in DOC_LINK_RE.findall(text)]
        doc_links = [t for t in link_targets if t.endswith(".md")]
        code_links = [t for t in link_targets if t.endswith((".py", ".yaml"))]
        if len(doc_links) < 2:
            failures.append(f"doc_link_density: {rel_from_root}")
        if len(code_links) < 1:
            failures.append(f"code_link_density: {rel_from_root}")

        # Hyperlink-only references for doc names.
        link_spans = [m.span() for m in DOC_LINK_RE.finditer(text)]
        for match in DOC_NAME_RE.finditer(text):
            if not any(start <= match.start() <= end for start, end in link_spans):
                failures.append(f"unlinked_doc_ref: {rel_from_root}")
                break
        for match in SYMBOL_RE.finditer(text):
            if not any(start <= match.start() <= end for start, end in link_spans):
                failures.append(f"unlinked_symbol_ref: {rel_from_root}")
                break
        for match in SRC_PATH_RE.finditer(text):
            if not any(start <= match.start() <= end for start, end in link_spans):
                failures.append(f"unlinked_path_ref: {rel_from_root}")
                break

        # Heading-only section guard.
        section_blocks: dict[str, list[str]] = {}
        current = None
        for line in lines:
            if line.startswith("## "):
                current = line[3:].strip()
                section_blocks[current] = []
                continue
            if current:
                section_blocks[current].append(line)
        for section, block in section_blocks.items():
            block_text = " ".join(block).strip()
            sentence_count = len(re.findall(r"[.!?]", block_text))
            has_table = any("|" in line for line in block)
            if sentence_count < 3 and not has_table:
                failures.append(f"heading_only: {section} in {rel_from_root}")

        # Sentence length rule (ignore list items).
        text_for_sentences = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("- ")
        )
        for sentence in re.split(r"[.!?]", text_for_sentences):
            words = [w for w in sentence.split() if w]
            if words and len(words) > MAX_WORDS_PER_SENTENCE:
                failures.append(f"sentence_too_long: {rel_from_root}")

        word_count = len(re.findall(r"\\b\\w+\\b", text))
        if rel.name == "index.md" and word_count > 100:
            failures.append(f"index_too_long: {rel_from_root}")
        elif rel.name != "index.md" and word_count > 200:
            failures.append(f"reference_too_long: {rel_from_root}")

        module_refs = MODULE_RE.findall(text)

        for ref in module_refs:
            ref = ref.rstrip(".,);:")
            if ref in modules:
                continue
            if any(mod.startswith(ref + ".") for mod in modules):
                continue
            failures.append(f"unknown_module_ref: {ref} in {rel_from_root}")

        for path_ref in SRC_PATH_RE.findall(text):
            if not _path_exists(path_ref):
                failures.append(f"missing_path_ref: {path_ref} in {rel_from_root}")

        for alias in aliases:
            if re.search(rf"\\b{re.escape(alias)}\\b", text, re.IGNORECASE):
                failures.append(f"alias_used: {rel_from_root}")
                break

        text_without_links = re.sub(r"\[[^\]]+\]\([^)]+\)", "", text)
        for name in canonical:
            if name.lower() != name and name.lower() in text_without_links:
                if re.search(rf"\\b{re.escape(name.lower())}\\b", text_without_links):
                    failures.append(f"canonical_casing: {rel_from_root}")
                    break

    test_roots = [
        ROOT / "packages" / "agentic-proteins" / "tests",
        ROOT / "packages" / "bijux-proteomics-core" / "tests",
        ROOT / "packages" / "bijux-proteomics-knowledge" / "tests",
        ROOT / "packages" / "bijux-proteomics-lab" / "tests",
    ]
    test_text = "\n".join(
        path.read_text()
        for test_root in test_roots
        if test_root.exists()
        for path in test_root.rglob("*.py")
    )
    for doc in sorted(DOCS_DIR.rglob("*.md")):
        rel = doc.relative_to(DOCS_DIR)
        if rel == Path("index.md"):
            continue
        text = doc.read_text()
        for match in CODE_REF_RE.finditer(text):
            ref = match.group(1)
            if ref.startswith("packages/agentic-proteins/src/agentic_proteins"):
                module_path = Path(ref)
                module_name = "agentic_proteins." + ".".join(
                    module_path.relative_to(
                        "packages/agentic-proteins/src/agentic_proteins"
                    )
                    .with_suffix("")
                    .parts
                )
                if module_name not in test_text:
                    failures.append(f"doc_without_tests: {doc.relative_to(ROOT)}")

    # README and docs index parity is handled outside this gate.

    if failures:
        for failure in failures:
            print(failure)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
