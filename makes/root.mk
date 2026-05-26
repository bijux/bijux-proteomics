ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/bijux-py/root/env.mk
include $(ROOT_MAKEFILE_DIR)/env.mk
include $(ROOT_MAKEFILE_DIR)/packages.mk

ROOT_DEV_PYTHONPATH := $(CURDIR)/packages/bijux-proteomics-dev/src
BIJUX_PY_SYSTEM_REL ?= .bijux/shared/bijux-makes-py
ROOT_CHECK_VENV := $(ROOT_ARTIFACTS_DIR)/check-venv
ROOT_DOCS_DEV_ADDR ?= 127.0.0.1:8001
COMMA := ,
UV_GROUPS ?= $(if $(strip $(EXTRAS)),$(subst $(COMMA), ,$(EXTRAS)),dev)
UV_SYNC_FLAGS := $(foreach group,$(UV_GROUPS),--group $(group))
UV_SYNC := UV_PROJECT_ENVIRONMENT="$(ROOT_CHECK_VENV)" $(UV) sync --frozen --python "$(PYTHON)" $(UV_SYNC_FLAGS)
ROOT_CHECK_STAMP_SYNC_MESSAGE := @echo "→ Syncing uv groups: $(UV_GROUPS)"
DEV_RUN = PYTHONPATH="$(CURDIR)/packages/bijux-proteomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(ROOT_CHECK_PYTHON)"
DOCS_RENDER_SERVE_CONFIG := 0
ROOT_TARGET_POST_quality = @$(MAKE) bijux-standard-check && $(MAKE) quality-docs-links && $(MAKE) quality-docs-consistency && $(MAKE) quality-runtime-boundaries && $(MAKE) quality-runtime-migration-ledger && $(MAKE) quality-runtime-migration-validation && $(MAKE) quality-artifact-governance && $(MAKE) quality-public-api-types
ROOT_TARGET_POST_security = @$(MAKE) security-dependency-allowlist
ROOT_PACKAGE_TARGETS += test-all test-all-plus-run-time
ROOT_TARGET_GROUPS_test-all ?= check
ROOT_TARGET_GROUPS_test-all-plus-run-time ?= check
ROOT_TARGET_SHARED_ENV_test-all ?= 1
ROOT_TARGET_SHARED_ENV_test-all-plus-run-time ?= 1

-include .env
export

include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/root.mk

include $(ROOT_MAKEFILE_DIR)/bijux-py/root/package-dispatch.mk
ROOT_TARGET_PACKAGES_test-all := $(CHECK_PACKAGES)
ROOT_TARGET_PACKAGES_test-all-plus-run-time := $(CHECK_PACKAGES)
include $(ROOT_MAKEFILE_DIR)/bijux-py/root/docs.mk
include $(ROOT_MAKEFILE_DIR)/bijux-docs.mk
include $(ROOT_MAKEFILE_DIR)/bijux-std.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/config-layout.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/make-layout.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/bijux.mk

DOCS_BUILD_PREPARE_TARGETS := bijux-docs-sync docs-prepare-source
DOCS_CHECK_PREPARE_TARGETS := bijux-docs-sync docs-prepare-source
DOCS_SERVE_PREPARE_TARGETS := bijux-docs-sync docs-render-serve-config

.PHONY: \
	help list list-all install lock lock-check lint quality security test test-all test-all-plus-run-time docs docs-check docs-serve api build sbom clean all \
	ensure-venv nlenv manage_examples manage_models api-freeze openapi-drift architecture-check \
	sync-badges sync-license-assets quality-docs-links quality-docs-consistency quality-artifact-governance release-preflight security-dependency-allowlist test-collection-gate \
	clean-root-artifacts root-check-env check-shared-bijux-py quality-public-api-types

check: lock-check lint test-collection-gate test quality security docs api build sbom ## Run the full repository verification flow

ensure-venv: install ## Ensure the shared root environment exists and is synced

nlenv: ## Print activate command
	@echo "Run: source $(ROOT_CHECK_VENV)/bin/activate"

sync-badges: root-check-env ## Render shared badge blocks into managed README surfaces
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.badge_sync sync

check-badges: root-check-env ## Verify README badge blocks match docs/badges.md
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.badge_sync check

sync-license-assets: root-check-env ## Sync package LICENSE and NOTICE links from root sources
	@$(DEV_RUN) -m bijux_proteomics_dev.release.license_assets sync

quality-docs-links: root-check-env ## Refresh docs link validation evidence
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.markdown_links

quality-docs-consistency: root-check-env ## Refresh docs consistency evidence
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.consistency

quality-artifact-governance: root-check-env ## Enforce artifact roots and repository file ownership
	@$(DEV_RUN) -m bijux_proteomics_dev.quality.artifacts.repository_file_ownership --check
	@$(DEV_RUN) -m bijux_proteomics_dev.quality.artifacts.repository_drift_audit --check
	@$(DEV_RUN) -m bijux_proteomics_dev.quality.artifacts.package_root_hygiene

quality-public-api-types: root-check-env ## Type-check curated public API modules with governed mypy and pyright configs
	@$(DEV_RUN) -m bijux_proteomics_dev.governance.contracts.public_api_typecheck_targets --check

test-collection-gate: root-check-env ## Run workspace import checks and per-package pytest collection before feature tests
	@$(DEV_RUN) -m bijux_proteomics_dev.release.governance.test_collection_gate

release-preflight: root-check-env ## Run the hostile-review release preflight in exact stage order
	@$(DEV_RUN) -m bijux_proteomics_dev.release.governance.final_preflight

quality-runtime-boundaries: root-check-env ## Enforce runtime boundary contracts
	@$(DEV_RUN) -m bijux_proteomics_dev.quality.architecture.runtime_boundaries

quality-runtime-migration-ledger: root-check-env ## Validate agentic migration ledger coverage and freshness
	@$(DEV_RUN) -m bijux_proteomics_dev.release.governance.compatibility_ledger --check

quality-runtime-migration-validation: root-check-env ## Run full runtime migration validation suite
	@$(DEV_RUN) -m bijux_proteomics_dev.release.governance.runtime_compatibility_validation

security-dependency-allowlist: root-check-env ## Validate the dependency allowlist
	@$(DEV_RUN) -m bijux_proteomics_dev.security.dependency_allowlist

api-freeze: root-check-env ## Enforce API schema freeze contracts
	@$(DEV_RUN) -m bijux_proteomics_dev.governance.contracts.freeze_contracts

openapi-drift: root-check-env ## Detect breaking API schema changes without version bumps
	@$(DEV_RUN) -m bijux_proteomics_dev.governance.contracts.openapi_drift

architecture-check: root-check-env ## Run architecture documentation and design-debt guards
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.architecture_docs
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.design_debt

##@ Repository
manage_examples: root-check-env ## Refresh example assets through the repository helper
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_examples

manage_models: root-check-env ## Refresh model metadata through the repository helper
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_models

HELP_WIDTH := 22
include $(ROOT_MAKEFILE_DIR)/bijux-py/ci/help.mk

help: ## Show generated repository commands from included make modules
check-shared-bijux-py: ## Verify shared bijux-py make modules match across sibling repositories
check-config-layout: ## Validate the repository config tree shape and required tool configs
check-make-layout: ## Validate the repository make tree shape and required entrypoints
