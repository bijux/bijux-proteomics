from __future__ import annotations

from pathlib import Path

INTELLIGENCE_DOMAIN_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "bijux_proteomics_intelligence"
    / "domain"
)


def test_removed_intelligence_domain_forwarder_files_stay_absent() -> None:
    assert not (INTELLIGENCE_DOMAIN_ROOT / "__init__.py").exists()
    assert not (INTELLIGENCE_DOMAIN_ROOT / "sequence" / "__init__.py").exists()
    assert not (INTELLIGENCE_DOMAIN_ROOT / "sequence" / "summary.py").exists()
    assert not (INTELLIGENCE_DOMAIN_ROOT / "sequence" / "validation.py").exists()
    assert not (INTELLIGENCE_DOMAIN_ROOT / "structure" / "__init__.py").exists()
    assert not (INTELLIGENCE_DOMAIN_ROOT / "structure" / "structure.py").exists()
