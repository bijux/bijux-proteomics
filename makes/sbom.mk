PROJECT_ARTIFACTS_DIR ?= artifacts
PACKAGE_NAME ?= agentic_proteins
GIT_TAG_EXACT := $(shell git describe --tags --exact-match 2>/dev/null | sed -E 's/^v//')
GIT_TAG_LATEST := $(shell git describe --tags --abbrev=0 2>/dev/null | sed -E 's/^v//')
PYPROJECT_VERSION = $(call read_pyproject_version)
PKG_VERSION ?= $(if $(GIT_TAG_EXACT),$(GIT_TAG_EXACT),$(if $(PYPROJECT_VERSION),$(PYPROJECT_VERSION),$(if $(GIT_TAG_LATEST),$(GIT_TAG_LATEST),0.0.0)))
GIT_DESCRIBE := $(shell git describe --tags --long --dirty --always 2>/dev/null)
PKG_VERSION_FULL := $(if $(GIT_TAG_EXACT),$(PKG_VERSION),$(shell echo "$(GIT_DESCRIBE)" | sed -E 's/^v//; s/-([0-9]+)-g([0-9a-f]+)(-dirty)?$$/+\1.g\2\3/'))
SBOM_VERSION ?= $(if $(PKG_VERSION_FULL),$(PKG_VERSION_FULL),$(PKG_VERSION))
SBOM_DIR ?= $(PROJECT_ARTIFACTS_DIR)/sbom
SBOM_PROD_REQ_INPUT ?= requirements/prod.txt
SBOM_DEV_REQ_INPUT ?= requirements/dev.txt
SBOM_IGNORE_IDS ?= PYSEC-2022-42969
PIP_AUDIT ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/sbom.mk
