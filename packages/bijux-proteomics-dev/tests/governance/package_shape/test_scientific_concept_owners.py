from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.package_shape.scientific_concept_owners import (
    ScientificConceptOwner,
    build_scientific_concept_symbol_inventory,
    load_scientific_concept_owners,
    validate_scientific_concept_ownership,
)


def _write_module(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_scientific_concept_owner_registry_covers_required_backlog_surface() -> None:
    owners = load_scientific_concept_owners()

    assert {owner.name for owner in owners} == {
        "target_decoy_label",
        "rejected_evidence",
        "sample_design",
        "peptide_identity",
        "protein_group",
        "ptm_site_group",
    }
    assert any(
        owner.name == "ptm_site_group"
        and owner.owner_module == "bijux_proteomics.ptm.sites.site_groups"
        and "build_ptm_site_group_evidence" in owner.owned_symbols
        for owner in owners
    )


def test_scientific_concept_ownership_is_clean_for_current_repo() -> None:
    assert validate_scientific_concept_ownership() == ()

    inventory = build_scientific_concept_symbol_inventory()
    ptm_site_group_definitions = [
        definition
        for definition in inventory
        if definition.concept_name == "ptm_site_group"
        and definition.symbol_name == "build_ptm_site_group_evidence"
    ]
    assert [
        definition.module_name for definition in ptm_site_group_definitions
    ] == ["bijux_proteomics.ptm.sites.site_groups"]


def test_scientific_concept_ownership_rejects_unexpected_duplicate_definitions(
    tmp_path: Path,
) -> None:
    core_src_root = tmp_path / "bijux_proteomics"
    _write_module(
        core_src_root,
        "domain/records.py",
        "class ProteinGroup:\n    pass\n",
    )
    _write_module(
        core_src_root,
        "identification/grouping.py",
        "class ProteinGroup:\n    pass\n",
    )

    owners = (
        ScientificConceptOwner(
            name="protein_group",
            owner_module="bijux_proteomics.domain.records",
            owned_symbols=("ProteinGroup",),
            allowed_facade_modules=(),
        ),
    )

    issues = validate_scientific_concept_ownership(
        core_src_root=core_src_root,
        concept_owners=owners,
    )

    assert len(issues) == 1
    assert issues[0].code == "duplicate-scientific-concept-owner"
    assert "bijux_proteomics.identification.grouping" in issues[0].detail
