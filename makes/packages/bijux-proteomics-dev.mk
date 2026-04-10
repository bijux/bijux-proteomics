PACKAGE_KIND := python
PACKAGE_IMPORT_NAME := bijux_proteomics_dev
PACKAGE_INSTALL_SPEC := .[dev]
RUFF_CONFIG = $(MONOREPO_ROOT)/configs/ruff.toml
MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
ENABLE_PYDOCSTYLE := 0
TEST_PATHS := tests
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests
SECURITY_PATHS := src
SECURITY_IGNORE_IDS := PYSEC-2022-42969 CVE-2025-68463
SECURITY_BANDIT_SKIP_IDS := B311
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
