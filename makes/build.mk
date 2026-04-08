PROJECT_ARTIFACTS_DIR ?= artifacts
BUILD_DIR ?= $(PROJECT_ARTIFACTS_DIR)/build
BUILD_CHECK_DISTS ?= $(if $(filter undefined,$(origin CHECK_DISTS)),0,$(CHECK_DISTS))
BUILD_PER_PACKAGE_DIRS ?= 1
ROOT_BUILD_PACKAGE_DIRS ?= packages/agentic-proteins packages/bijux-proteomics-foundation packages/bijux-proteomics-core packages/bijux-proteomics-intelligence packages/bijux-proteomics-knowledge packages/bijux-proteomics-lab
ROOT_BUILD_ALIAS_PACKAGES ?= agentic-proteins bijux-proteomics-foundation bijux-proteomics-core bijux-proteomics-intelligence bijux-proteomics-knowledge bijux-proteomics-lab
BUILD_TOOLS_COMMAND ?= $(BUILD_PYTHON) -m build --version >/dev/null && $(BUILD_PYTHON) -m twine --version >/dev/null
BUILD_TEMP_CLEAN_PATHS ?= build dist packages/*/src/*.egg-info
BUILD_TEMP_CLEAN_PYCACHE ?= 1
BUILD_RELEASE_DRY_RUN_CMD ?= $(VENV_PYTHON) -c 'from packaging.version import Version; import importlib.metadata as m; from pathlib import Path; import sys; version=m.version("agentic-proteins"); base=Version(version).base_version; print(f"version={version} base={base}"); changelog=Path("packages/agentic-proteins/CHANGELOG.md").read_text().splitlines(); header=f"## {base}"; sys.exit(f"Missing changelog header for {base}") if header not in changelog else None; idx=changelog.index(header); section_lines=changelog[idx + 1:]; end_idx=next((i for i, line in enumerate(section_lines) if line.startswith("## ")), None); section="\n".join(section_lines[:end_idx] if end_idx is not None else section_lines); required=["### Added","### Changed","### Fixed"]; missing=[h for h in required if h not in section]; sys.exit(f"Changelog {base} missing sections: {missing}") if missing else None; print("✔ Changelog sections present")'

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/build.mk

clean-temp-build-files: build-clean-temp
.PHONY: clean-temp-build-files
