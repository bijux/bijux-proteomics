include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := bijux_proteomics_runtime
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]"
TEST_PATHS_UNIT := tests
TEST_PATHS_E2E :=
TEST_PATHS_REGRESSION :=
TEST_PATHS_EVALUATION :=
TEST_REAL_LOCAL_PATH :=
TEST_MAIN_ARGS :=
TEST_CI_TARGETS := test-unit
TEST_COVERAGE_FAIL_UNDER := 60
CODESPELL := $(if $(ACT),$(ACT)/codespell,codespell) -L SER

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
