PROJECT_ARTIFACTS_DIR ?= artifacts
LINT_DIRS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
RUFF_CONFIG ?= $(CONFIG_DIR)/ruff.toml
MYPY_CONFIG ?= $(CONFIG_DIR)/mypy.ini
PYDOCSTYLE_ARGS ?= --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107
ENABLE_PYDOCSTYLE ?= 1

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/lint.mk
