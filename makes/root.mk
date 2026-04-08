ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-env.mk

PROJECT_DIR ?= $(CURDIR)
PROJECT_SLUG ?= bijux-proteomics
PROJECT_ARTIFACTS_DIR ?= artifacts
CONFIG_DIR ?= configs
VENV ?= $(ROOT_VENV)
VENV_PYTHON ?= $(if $(shell test -x "$(VENV)/bin/python" && echo yes),$(VENV)/bin/python,python3)
ACT ?= $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,)
DEV_PYTHONPATH ?= packages/bijux-proteomics-dev/src
DEV_RUN ?= PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)"
COMMA := ,
UV_GROUPS ?= $(if $(strip $(EXTRAS)),$(subst $(COMMA), ,$(EXTRAS)),dev)
UV_SYNC_FLAGS := $(foreach group,$(UV_GROUPS),--group $(group))
UV_SYNC ?= UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --python $(PYTHON) $(UV_SYNC_FLAGS)
MKDOCS_CFG ?= $(PROJECT_DIR)/mkdocs.yml

-include .env
export

include $(ROOT_MAKEFILE_DIR)/gates.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/shared-bijux-py.mk

ROOT_INSTALL_COMMAND := @$(SELF_MAKE) ensure-venv
ROOT_ALL_TARGETS := clean install test lint quality security sbom build docs api
ROOT_CLEAN_COMMAND := @rm -rf "$(PROJECT_ARTIFACTS_DIR)" && \
	find . -name ".DS_Store" -delete && \
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + && \
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete && \
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-lifecycle.mk

.PHONY: \
	install ensure-venv nlenv \
	manage_examples manage_models \
	all help

$(VENV):
	@echo "→ Creating virtualenv at '$(VENV)' with '$$(which $(PYTHON))' ..."
	@$(UV) venv --python "$(PYTHON)" "$(VENV)"

ensure-venv: $(VENV) ## Ensure venv exists and deps are installed
	@set -e; \
	echo "→ Ensuring dependencies in $(VENV) ..."; \
	echo "→ Syncing uv groups: $(UV_GROUPS)"; \
	$(UV_SYNC)

nlenv: ## Print activate command
	@echo "Run: source $(ACT)/activate"

##@ Repository
manage_examples: ## Refresh example assets through the repository helper
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_examples

manage_models: ## Refresh model metadata through the repository helper
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_models

HELP_WIDTH := 22
include $(ROOT_MAKEFILE_DIR)/bijux-py/help.mk

help: ## Show generated repository commands from included make modules
check-shared-bijux-py: ## Verify shared bijux-py make modules match across sibling repositories
