from __future__ import annotations

from bijux_proteomics_dev.governance.package_shape.package_tree_layout import (
    CANONICAL_PACKAGE_TREE_LAYOUT_PATH,
    PackageTreeLayoutEntry,
    PackageTreeLayoutPolicy,
    build_package_tree_layout_report,
    load_package_tree_layout_policy,
    run,
    validate_package_tree_layout,
)


def test_package_tree_layout_manifest_is_repository_owned() -> None:
    assert CANONICAL_PACKAGE_TREE_LAYOUT_PATH.as_posix().endswith(
        "configs/package-governance/canonical-package-tree-layout.toml"
    )


def test_package_tree_layout_manifest_covers_workspace_packages() -> None:
    policy = load_package_tree_layout_policy()

    assert policy.name == "canonical-package-tree-layout"
    assert [entry.distribution_name for entry in policy.packages] == [
        "agentic-proteins",
        "bijux-proteomics",
        "bijux-proteomics-core",
        "bijux-proteomics-dev",
        "bijux-proteomics-foundation",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
        "proteomics",
        "proteomics-core",
        "proteomics-foundation",
        "proteomics-intelligence",
        "proteomics-knowledge",
        "proteomics-lab",
        "proteomics-runtime",
    ]


def test_live_package_tree_layout_matches_canonical_manifest() -> None:
    assert validate_package_tree_layout() == ()
    assert run(check=True) == 0

    report = build_package_tree_layout_report()
    entries = {entry.distribution_name: entry for entry in report.packages}
    assert entries["bijux-proteomics-core"] == PackageTreeLayoutEntry(
        distribution_name="bijux-proteomics-core",
        import_roots=("bijux_proteomics",),
        top_level_families=(
            "benchmarks",
            "biology",
            "chemistry",
            "dia",
            "domain",
            "governance",
            "identification",
            "interfaces",
            "interpretation",
            "io",
            "isotope_labeling",
            "lab",
            "multiplex",
            "panels",
            "proteoforms",
            "ptm",
            "quantification",
            "review",
            "sequences",
            "study",
            "targeted",
            "workflow",
        ),
        root_module_files=(
            "_atomic_files.py",
            "_output_tables.py",
            "_scientific_tables.py",
            "_tabular.py",
            "programs.py",
            "public_api.py",
            "scientific_tables.py",
            "tabular.py",
        ),
    )


def test_package_tree_layout_validator_rejects_drifted_family_layout() -> None:
    policy = PackageTreeLayoutPolicy(
        name="canonical-package-tree-layout",
        packages=(
            PackageTreeLayoutEntry(
                distribution_name="bijux-proteomics-core",
                import_roots=("bijux_proteomics",),
                top_level_families=("workflow",),
                root_module_files=("public_api.py",),
            ),
        ),
    )
    report = PackageTreeLayoutPolicy(
        name="canonical-package-tree-layout",
        packages=(
            PackageTreeLayoutEntry(
                distribution_name="bijux-proteomics-core",
                import_roots=("bijux_proteomics",),
                top_level_families=("benchmarks", "workflow"),
                root_module_files=("public_api.py",),
            ),
        ),
    )

    failures = validate_package_tree_layout(report, policy)

    assert failures == (
        "bijux-proteomics-core top-level families ('benchmarks', 'workflow') do not match the canonical layout ('workflow',)",
    )
