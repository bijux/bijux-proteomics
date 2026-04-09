"""Markdown link checker for repository documentation."""

from __future__ import annotations

from pathlib import Path
import re
import sys

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def iter_markdown_files(root: Path) -> list[Path]:
    docs_dir = root / "docs"
    files: list[Path] = []
    if docs_dir.exists():
        for path in sorted(docs_dir.rglob("*.md")):
            if "_legacy" in path.parts:
                continue
            if path.name == "index.md" and path.parent == docs_dir:
                continue
            files.append(path)
    readme = root / "README.md"
    if readme.exists():
        files.append(readme)
    return files


def is_external_link(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:"))


def normalize_target(target: str) -> str:
    return target.split("#", 1)[0].strip()


def resolve_target(source: Path, target: str, repo_root: Path) -> Path:
    if target.startswith("/"):
        return repo_root / target.lstrip("/")
    return (source.parent / target).resolve()


def run(repo_root: Path) -> int:
    broken: list[str] = []
    for path in iter_markdown_files(repo_root):
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.findall(text):
            target = match.strip()
            if not target or target.startswith("#"):
                continue
            if is_external_link(target):
                continue
            target = normalize_target(target)
            if not target:
                continue
            target_path = resolve_target(path, target, repo_root)
            if not target_path.exists():
                broken.append(f"{path}: {match}")
    if broken:
        print("Broken Markdown links detected:", file=sys.stderr)
        for entry in broken:
            print(f"- {entry}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return run(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
