# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

include $(ROOT_MAKEFILE_DIR)/test.mk
include $(ROOT_MAKEFILE_DIR)/lint.mk
include $(ROOT_MAKEFILE_DIR)/quality.mk
include $(ROOT_MAKEFILE_DIR)/security.mk
include $(ROOT_MAKEFILE_DIR)/build.mk
include $(ROOT_MAKEFILE_DIR)/sbom.mk
include $(ROOT_MAKEFILE_DIR)/docs.mk
include $(ROOT_MAKEFILE_DIR)/api.mk
include $(ROOT_MAKEFILE_DIR)/architecture.mk

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

manage_examples:
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_examples

manage_models:
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_models

help: ## Show this help
	@awk 'BEGIN{FS=":.*##"; OFS="";} \
	  /^[a-zA-Z0-9_.-]+:.*##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
	  $(MAKEFILE_LIST)
