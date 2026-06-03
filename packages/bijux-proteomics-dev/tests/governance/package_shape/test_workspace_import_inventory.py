from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    workspace_dependency_edges_for_path,
)


def test_workspace_import_inventory_resolves_imported_submodules(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "consumer.py"
    module_path.write_text(
        "from bijux_proteomics_dev.governance.package_shape import skip_policy\n",
        encoding="utf-8",
    )

    edges = workspace_dependency_edges_for_path(
        "bijux-proteomics-dev",
        module_path,
        source_module_name="bijux_proteomics_dev.synthetic.consumer",
    )

    assert any(
        edge.target_module
        == "bijux_proteomics_dev.governance.package_shape.skip_policy"
        for edge in edges
    )


def test_workspace_import_inventory_resolves_static_lazy_imports(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "consumer.py"
    module_path.write_text(
        "\n".join(
            (
                "from importlib import import_module",
                '_MODULES = ("bijux_proteomics.review.claims",)',
                "",
                "def load() -> None:",
                "    for module_name in _MODULES:",
                "        import_module(module_name)",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    edges = workspace_dependency_edges_for_path(
        "bijux-proteomics-core",
        module_path,
        source_module_name="bijux_proteomics.synthetic.consumer",
    )

    assert any(edge.target_module == "bijux_proteomics.review.claims" for edge in edges)
