from __future__ import annotations

from pathlib import Path


REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "packages").is_dir() and (parent / "configs").is_dir())
FOUNDATION_README = REPO_ROOT / "packages" / "bijux-proteomics-foundation" / "README.md"
RUNTIME_README = REPO_ROOT / "packages" / "bijux-proteomics-runtime" / "README.md"


def test_foundation_readme_stays_on_shared_kernel_examples() -> None:
    text = FOUNDATION_README.read_text(encoding="utf-8")

    assert "shared contract kernel" in text
    assert "runtime-owned examples belong in the package that owns that behavior" in text
    for runtime_owned_example in (
        'created_by="bijux-proteomics-runtime"',
        'package_name="bijux-proteomics-runtime"',
        'operation="mzidentml_ingestion"',
        'operation="hash_manifest"',
        'code="engine_timeout"',
    ):
        assert runtime_owned_example not in text


def test_runtime_readme_hosts_runtime_owned_foundation_examples() -> None:
    text = RUNTIME_README.read_text(encoding="utf-8")

    assert "Foundation-backed runtime contract examples" in text
    for runtime_owned_example in (
        'created_by="bijux-proteomics-runtime"',
        'package_name="bijux-proteomics-runtime"',
        'operation="mzidentml_ingestion"',
        'operation="hash_manifest"',
        'code="engine_timeout"',
    ):
        assert runtime_owned_example in text
