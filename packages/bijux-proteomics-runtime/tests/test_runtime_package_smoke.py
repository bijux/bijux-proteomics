import bijux_proteomics_runtime


def test_runtime_package_imports() -> None:
    assert bijux_proteomics_runtime is not None


def test_runtime_package_exports_only_runtime_owned_entrypoints() -> None:
    assert tuple(bijux_proteomics_runtime.__all__) == (
        "AppConfig",
        "RunManager",
        "cli",
        "create_app",
    )
