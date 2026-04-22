ROOT_PACKAGE_PROFILE_DIR ?= $(ROOT_MAKEFILE_DIR)/packages
ROOT_PACKAGE_TARGETS ?= test fmt lint quality security api build sbom clean
ROOT_TARGET_GROUPS_fmt ?= check
ROOT_TARGET_SHARED_ENV_fmt ?= 1

PACKAGE_RECORDS := \
	agentic-proteins|primary,check,buildable,sbom,api|agentic-proteins.mk \
	bijux-proteomics-foundation|primary,check,buildable,sbom,api|bijux-proteomics-foundation.mk \
	bijux-proteomics-core|primary,check,buildable,sbom,api|bijux-proteomics-core.mk \
	bijux-proteomics-runtime|primary,check,buildable,sbom,api|bijux-proteomics-runtime.mk \
	bijux-proteomics-intelligence|primary,check,buildable,sbom,api|bijux-proteomics-intelligence.mk \
	bijux-proteomics-knowledge|primary,check,buildable,sbom,api|bijux-proteomics-knowledge.mk \
	bijux-proteomics-lab|primary,check,buildable,sbom,api|bijux-proteomics-lab.mk \
	bijux-proteomics-dev|check|bijux-proteomics-dev.mk

include $(ROOT_MAKEFILE_DIR)/bijux-py/package-catalog.mk
