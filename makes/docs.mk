# Docs Configuration

PYTHON ?= $(shell command -v python3 || command -v python)

.PHONY: docs docs-serve docs-deploy docs-clean

docs:
	@$(PYTHON) -m mkdocs build --strict

DOCS_ADDR ?= 127.0.0.1:8001

docs-serve:
	@$(PYTHON) -m mkdocs serve -a $(DOCS_ADDR)

docs-deploy:
	@$(PYTHON) -m mkdocs gh-deploy --force

docs-clean:
	@rm -rf site

##@ Docs
docs: ## Build MkDocs site locally (strict)
docs-serve: ## Serve MkDocs site locally (DOCS_ADDR=127.0.0.1:8001)
docs-deploy: ## Deploy MkDocs site to gh-pages
docs-clean: ## Remove MkDocs output directory
