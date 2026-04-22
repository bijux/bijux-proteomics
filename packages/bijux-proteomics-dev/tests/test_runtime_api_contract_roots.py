from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_API_ROOT = REPO_ROOT / "apis" / "bijux-proteomics-runtime" / "v1"
COMPAT_API_ROOT = REPO_ROOT / "apis" / "agentic-proteins" / "v1"
REQUIRED_FILES = ("schema.yaml", "pinned_openapi.json", "schema.hash")


def test_runtime_canonical_api_contract_root_exists() -> None:
    assert RUNTIME_API_ROOT.exists()
    for filename in REQUIRED_FILES:
        assert (RUNTIME_API_ROOT / filename).exists()


def test_agentic_api_contract_root_matches_runtime_mirror() -> None:
    assert COMPAT_API_ROOT.exists()
    for filename in REQUIRED_FILES:
        runtime_path = RUNTIME_API_ROOT / filename
        compat_path = COMPAT_API_ROOT / filename
        assert compat_path.exists(), f"missing compat mirror file: {compat_path}"
        assert runtime_path.read_bytes() == compat_path.read_bytes(), (
            f"compat mirror drifted from canonical runtime API contract: {filename}"
        )
