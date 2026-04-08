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

.PHONY: \
	install ensure-venv nlenv \
	clean clean-soft clean-venv \
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

install: ensure-venv ## Sync repository dependencies into the shared uv environment
	@true

nlenv: ## Print activate command
	@echo "Run: source $(ACT)/activate"

clean-soft: ## Remove build artifacts but keep venv
	@echo "→ Cleaning (no .venv removal) ..."
	@$(RM) \
	  .pytest_cache htmlcov coverage.xml dist build *.egg-info .tox demo .tmp_home \
	  .ruff_cache .mypy_cache .pytype .hypothesis .coverage.* .coverage .benchmarks \
	  artifacts .cache || true
	@if [ "$(OS)" != "Windows_NT" ]; then \
	  find . -type d -name '__pycache__' -exec $(RM) {} +; \
	fi

clean-venv:
	@echo "→ Cleaning ($(VENV)) ..."
	@$(RM) "$(VENV)"

clean: clean-soft clean-venv ## Remove the uv environment and generated artifacts

all: clean install test lint quality security sbom build docs api ## Full repository pipeline
	@echo "✔ All targets completed"

manage_examples:
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_examples

manage_models:
	@$(DEV_RUN) -m bijux_proteomics_dev.tools.manage_models

help: ## Show this help
	@awk 'BEGIN{FS=":.*##"; OFS="";} \
	  /^[a-zA-Z0-9_.-]+:.*##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
	  $(MAKEFILE_LIST)
