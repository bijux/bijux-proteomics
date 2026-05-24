"""Repo-root loader for canonical packages in a clean checkout."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType


def load_checkout_package(
    module_name: str,
    *,
    repository_root: Path,
    package_directory: str,
    import_name: str,
) -> ModuleType:
    """Load one canonical package directly from its owning ``src`` tree."""

    package_root = (
        repository_root
        / "packages"
        / package_directory
        / "src"
        / import_name
    )
    init_path = package_root / "__init__.py"
    if not init_path.is_file():
        raise ModuleNotFoundError(
            f"cannot load {module_name!r} from checkout; missing {init_path}"
        )
    spec = spec_from_file_location(
        module_name,
        init_path,
        submodule_search_locations=[str(package_root)],
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(
            f"cannot create an import specification for {module_name!r}"
        )
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


__all__ = ["load_checkout_package"]
