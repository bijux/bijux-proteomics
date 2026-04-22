from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPAT_INTERFACES_DIR = REPO_ROOT / "docs" / "02-agentic-proteins" / "interfaces"


def test_compat_interface_docs_reference_canonical_and_mirror_api_roots() -> None:
    failures: list[str] = []
    for path in sorted(COMPAT_INTERFACES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        has_runtime_root = "apis/bijux-proteomics-runtime/v1" in text
        has_compat_root = "apis/agentic-proteins/v1" in text
        if has_runtime_root and has_compat_root:
            continue
        failures.append(path.relative_to(REPO_ROOT).as_posix())
    assert not failures, (
        "compat interface docs must mention canonical runtime API root and compatibility mirror:\n"
        + "\n".join(failures)
    )
