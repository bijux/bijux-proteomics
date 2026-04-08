PROJECT_ARTIFACTS_DIR ?= artifacts
INTERROGATE_PATHS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
QUALITY_PATHS ?= $(INTERROGATE_PATHS)
QUALITY_MYPY_CONFIG ?= $(CONFIG_DIR)/mypy.ini
QUALITY_MYPY_TARGETS ?= $(QUALITY_PATHS)
QUALITY_VULTURE_MIN_CONFIDENCE ?= 90
QUALITY_POST_TARGETS ?= quality-docs-links quality-docs-consistency
QUALITY_RUN_MKDOCS ?= 1
SKIP_MYPY ?= 0

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/quality.mk

quality-docs-links:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.markdown_links
.PHONY: quality-docs-links

quality-docs-consistency:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.consistency
.PHONY: quality-docs-consistency
