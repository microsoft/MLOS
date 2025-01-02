# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

CONDA_ENV_NAME ?= mlos
PYTHON_VERSION := $(shell echo "${CONDA_ENV_NAME}" | sed -r -e 's/^mlos[-]?//')
ENV_YML := conda-envs/${CONDA_ENV_NAME}.yml

# Find the non-build python files we should consider as rule dependencies.
# Do a single find and multiple filters for better performance.
REPO_FILES := $(shell find . -type f 2>/dev/null | egrep -v -e '^./(mlos_(core|bench|viz)/)?build/' -e '^./doc/source/' -e '^./doc/build/')
PYTHON_FILES := $(filter %.py, $(REPO_FILES))
MLOS_CORE_PYTHON_FILES := $(filter ./mlos_core/%, $(PYTHON_FILES))
MLOS_BENCH_PYTHON_FILES := $(filter ./mlos_bench/%, $(PYTHON_FILES))
MLOS_VIZ_PYTHON_FILES := $(filter ./mlos_viz/%, $(PYTHON_FILES))
NOTEBOOK_FILES := $(filter %.ipynb, $(REPO_FILES))
SCRIPT_FILES := $(filter %.sh %.ps1 %.cmd, $(REPO_FILES))
SQL_FILES := $(filter %.sql, $(REPO_FILES))
MD_FILES := $(filter-out ./doc/%, $(filter %.md, $(REPO_FILES)))

DOCKER := $(shell which docker)
# Make sure the build directory exists.
MKDIR_BUILD := $(shell test -d build || mkdir build)

# Allow overriding the default verbosity of conda for CI jobs.
#CONDA_INFO_LEVEL ?= -q

# Run make in parallel by default.
MAKEFLAGS += -j$(shell nproc 2>/dev/null || sysctl -n hw.ncpu)
#MAKEFLAGS += -Oline

.PHONY: all
all: format check test dist dist-test doc | conda-env

.PHONY: conda-env
conda-env: build/conda-env.${CONDA_ENV_NAME}.build-stamp

MLOS_CORE_CONF_FILES := mlos_core/pyproject.toml mlos_core/setup.py mlos_core/MANIFEST.in
MLOS_BENCH_CONF_FILES := mlos_bench/pyproject.toml mlos_bench/setup.py mlos_bench/MANIFEST.in
MLOS_VIZ_CONF_FILES := mlos_viz/pyproject.toml mlos_viz/setup.py mlos_viz/MANIFEST.in
MLOS_GLOBAL_CONF_FILES := setup.cfg pyproject.toml

MLOS_PKGS := mlos_core mlos_bench mlos_viz
MLOS_PKG_CONF_FILES := $(MLOS_CORE_CONF_FILES) $(MLOS_BENCH_CONF_FILES) $(MLOS_VIZ_CONF_FILES) $(MLOS_GLOBAL_CONF_FILES)

build/conda-env.${CONDA_ENV_NAME}.build-stamp: ${ENV_YML} $(MLOS_PKG_CONF_FILES)
	@echo "CONDA_SOLVER: ${CONDA_SOLVER}"
	@echo "CONDA_EXPERIMENTAL_SOLVER: ${CONDA_EXPERIMENTAL_SOLVER}"
	@echo "CONDA_INFO_LEVEL: ${CONDA_INFO_LEVEL}"
	conda env list -q | grep -q "^${CONDA_ENV_NAME} " || conda env create ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} -f ${ENV_YML}
	conda env update ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} --prune -f ${ENV_YML}
	$(MAKE) clean-format clean-check clean-test clean-doc clean-dist
	touch $@

.PHONY: clean-conda-env
clean-conda-env:
	conda env remove -y ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME}
	rm -f build/conda-env.${CONDA_ENV_NAME}.build-stamp


# Here we make dynamic prereqs to apply to other targets that need to run in sequence.
FORMAT_PREREQS :=

.PHONY: format
format: build/format.${CONDA_ENV_NAME}.build-stamp

ifneq (,$(filter format,$(MAKECMDGOALS)))
    FORMAT_PREREQS += build/format.${CONDA_ENV_NAME}.build-stamp
endif

FORMAT_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
FORMAT_COMMON_PREREQS += .pre-commit-config.yaml
FORMAT_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

# Formatting pre-commit hooks are marked with the "manual" stage.
FORMATTERS := $(shell cat .pre-commit-config.yaml | yq -r '.repos[].hooks[] | select((.stages // [])[] | contains("manual")) | .id')

# Provide convenience methods to call individual formatters via `make` as well (e.g., `make black`).
.PHONY: $(FORMATTERS)
.NOTPARALLEL: $(FORMATTERS)
$(FORMATTERS): $(MLOS_CORE_PYTHON_FILES)
$(FORMATTERS): $(MLOS_BENCH_PYTHON_FILES)
$(FORMATTERS): $(MLOS_VIZ_PYTHON_FILES)
$(FORMATTERS): $(FORMAT_COMMON_PREREQS)
	conda run -n ${CONDA_ENV_NAME} pre-commit run -v --all-files $@ || true

build/format.${CONDA_ENV_NAME}.build-stamp:
	conda run -n ${CONDA_ENV_NAME} pre-commit run -v --all-files --hook-stage manual
	touch $@

.PHONY: check
check: build/check.${CONDA_ENV_NAME}.build-stamp

CHECK_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
CHECK_COMMON_PREREQS += .pre-commit-config.yaml
CHECK_COMMON_PREREQS += $(FORMAT_PREREQS)
CHECK_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/check.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/check.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/check.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)
build/check.${CONDA_ENV_NAME}.build-stamp: $(CHECK_COMMON_PREREQS)
	SKIP=`echo '$(FORMATTERS)' | tr ' ' ','` conda run -n ${CONDA_ENV_NAME} pre-commit run -v --all-files
	touch $@

.PHONY: cspell
ifeq ($(DOCKER),)
cspell:
	@echo "NOTE: docker is not available. Skipping cspell check."
else
cspell: build/cspell-container.build-stamp
	./.devcontainer/scripts/run-cspell.sh
endif

build/cspell-container.build-stamp: $(FORMAT_PREREQS)
	# Build the docker image with cspell in it.
	$(MAKE) -C .devcontainer/build cspell
	touch $@

.PHONY: markdown-link-check
ifeq ($(DOCKER),)
markdown-link-check:
	@echo "NOTE: docker is not available. Skipping markdown-link-check check."
else
markdown-link-check: build/markdown-link-check-container.build-stamp
	./.devcontainer/scripts/run-markdown-link-check.sh
endif

build/markdown-link-check-container.build-stamp: $(FORMAT_PREREQS)
	# Build the docker image with markdown-link-check in it.
	$(MAKE) -C .devcontainer/build markdown-link-check
	touch $@

.PHONY: test
test: pytest notebook-exec-test

PYTEST_CONF_FILES := $(MLOS_GLOBAL_CONF_FILES) conftest.py

.PHONY: pytest
pytest: conda-env build/pytest.${CONDA_ENV_NAME}.build-stamp

pytest-mlos-core: build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp
pytest-mlos-bench: build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp
pytest-mlos-viz: build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp

build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_CORE_PYTHON_FILES) $(MLOS_CORE_CONF_FILES)
build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp: PYTEST_MODULE := mlos_core

build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_BENCH_PYTHON_FILES) $(MLOS_BENCH_CONF_FILES)
build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp: PYTEST_MODULE := mlos_bench

build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_VIZ_PYTHON_FILES) $(MLOS_VIZ_CONF_FILES)
build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp: PYTEST_MODULE := mlos_viz

# Individual package test rules (for tight loop dev work).
# Skip code coverage tests for these.
PYTEST_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
PYTEST_COMMON_PREREQS += $(FORMAT_PREREQS)
PYTEST_COMMON_PREREQS += $(PYTEST_CONF_FILES)

build/pytest.%.${CONDA_ENV_NAME}.needs-build-stamp: $(PYTEST_COMMON_PREREQS)
	conda run -n ${CONDA_ENV_NAME} pytest $(PYTEST_EXTRA_OPTIONS) $(PYTEST_MODULE)
	touch $@

PYTEST_OPTIONS :=

# Allow optionally skipping coverage calculations during local testing to skip up inner dev loop.
SKIP_COVERAGE := $(shell echo $${SKIP_COVERAGE:-} | grep -i -x -e 1 -e true)

ifeq ($(SKIP_COVERAGE),)
    PYTEST_OPTIONS += --cov=. --cov-append --cov-fail-under=92 --cov-report=xml --cov-report=html --junitxml=junit/test-results.xml --local-badge-output-dir=doc/source/badges/
endif

# Global pytest rule that also produces code coverage for the pipeline.
# NOTE: When run locally, the junit/test-results.xml will only include the
# tests from the latest run, but this file is only used for upstream reporting,
# so probably shouldn't matter.
build/pytest.${CONDA_ENV_NAME}.build-stamp: $(PYTEST_COMMON_PREREQS)
build/pytest.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES) $(MLOS_CORE_CONF_FILES)
build/pytest.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES) $(MLOS_BENCH_CONF_FILES)
build/pytest.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES) $(MLOS_VIZ_CONF_FILES)
build/pytest.${CONDA_ENV_NAME}.build-stamp:
	# Remove the markers for individual targets (above).
	for pytest_module in $(MLOS_PKGS); do rm -f build/pytest.$${pytest_module}.${CONDA_ENV_NAME}.build-stamp; done
	# Run pytest for the modules: $(MLOS_PKGS)
	mkdir -p doc/source/badges/
	conda run -n ${CONDA_ENV_NAME} pytest $(PYTEST_OPTIONS) $(PYTEST_EXTRA_OPTIONS) $(MLOS_PKGS)
	# Global success.  Mark the individual targets as done again.
	for pytest_module in $(MLOS_PKGS); do touch build/pytest.$${pytest_module}.${CONDA_ENV_NAME}.build-stamp; done
	touch $@


# setuptools-scm needs a longer history than Github CI workers have by default.
.PHONY: unshallow
unshallow: build/unshallow.build-stamp

build/unshallow.build-stamp:
	git rev-parse --is-shallow-repository | grep -x -q false || git fetch --unshallow --quiet
	touch $@

.PHONY: dist
dist: sdist bdist_wheel

.PHONY: sdist
sdist: conda-env unshallow
sdist: mlos_core/dist/tmp/mlos_core-latest.tar.gz
sdist: mlos_bench/dist/tmp/mlos_bench-latest.tar.gz
sdist: mlos_viz/dist/tmp/mlos_viz-latest.tar.gz

.PHONY: bdist_wheel
bdist_wheel: conda-env unshallow
bdist_wheel: mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl
bdist_wheel: mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl
bdist_wheel: mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl

# Make the whl files depend on the .tar.gz files, mostly to prevent conflicts
# with shared use of the their build/ trees.

mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: MODULE_NAME := mlos_core
mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: PACKAGE_NAME := mlos_core
mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: mlos_core/dist/tmp/mlos_core-latest.tar.gz
mlos_core/dist/tmp/mlos_core-latest.tar.gz: $(MLOS_CORE_CONF_FILES) $(MLOS_CORE_PYTHON_FILES)
mlos_core/dist/tmp/mlos_core-latest.tar.gz: MODULE_NAME := mlos_core
mlos_core/dist/tmp/mlos_core-latest.tar.gz: PACKAGE_NAME := mlos_core

mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: MODULE_NAME := mlos_bench
mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: PACKAGE_NAME := mlos_bench
mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: mlos_bench/dist/tmp/mlos_bench-latest.tar.gz
mlos_bench/dist/tmp/mlos_bench-latest.tar.gz: $(MLOS_BENCH_CONF_FILES) $(MLOS_BENCH_PYTHON_FILES)
mlos_bench/dist/tmp/mlos_bench-latest.tar.gz: MODULE_NAME := mlos_bench
mlos_bench/dist/tmp/mlos_bench-latest.tar.gz: PACKAGE_NAME := mlos_bench

mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: MODULE_NAME := mlos_viz
mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: PACKAGE_NAME := mlos_viz
mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: mlos_viz/dist/tmp/mlos_viz-latest.tar.gz
mlos_viz/dist/tmp/mlos_viz-latest.tar.gz: $(MLOS_VIZ_CONF_FILES) $(MLOS_VIZ_PYTHON_FILES)
mlos_viz/dist/tmp/mlos_viz-latest.tar.gz: MODULE_NAME := mlos_viz
mlos_viz/dist/tmp/mlos_viz-latest.tar.gz: PACKAGE_NAME := mlos_viz

%-latest.tar.gz: build/conda-env.${CONDA_ENV_NAME}.build-stamp build/unshallow.build-stamp $(FORMAT_PREREQS)
	mkdir -p $(MODULE_NAME)/dist/tmp
	rm -f $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar{,.gz}
	rm -f $(MODULE_NAME)/dist/tmp/$(PACKAGE_NAME)-latest.tar{,.gz}
	rm -rf $(MODULE_NAME)/build/
	rm -rf $(MODULE_NAME)/$(MODULE_NAME).egg-info/
	cd $(MODULE_NAME)/ && conda run -n ${CONDA_ENV_NAME} python3 -m build --sdist
	# Do some sanity checks on the sdist tarball output.
	BASE_VERS=`conda run -n ${CONDA_ENV_NAME} python3 $(MODULE_NAME)/$(MODULE_NAME)/version.py | cut -d. -f-2 | egrep -x '[0-9.]+' || echo err-unknown-base-version` \
		&& TAG_VERS=`git tag -l --sort=-version:refname | egrep -x '^v[0-9.]+' | head -n1 | sed 's/^v//' | cut -d. -f-2 | egrep -x '[0-9.]+' || echo err-unknown-tag-version` \
		&& ls $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar.gz | grep -F -e $$BASE_VERS -e $$TAG_VERS
	# Make sure tests were excluded.
	! ( tar tzf $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar.gz | grep -m1 tests/ )
	# Make sure the py.typed marker file exists.
	tar tzf $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar.gz | grep -m1 /py.typed
	# Check to make sure the mlos_bench module has the config directory.
	[ "$(MODULE_NAME)" != "mlos_bench" ] || tar tzf $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar.gz | grep -m1 mlos_bench/config/
	cd $(MODULE_NAME)/dist/tmp && ln -s ../$(PACKAGE_NAME)-*.tar.gz $(PACKAGE_NAME)-latest.tar.gz

%-latest-py3-none-any.whl: build/conda-env.${CONDA_ENV_NAME}.build-stamp build/unshallow.build-stamp $(FORMAT_PREREQS)
	mkdir -p $(MODULE_NAME)/dist/tmp
	rm -f $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl
	rm -f $(MODULE_NAME)/dist/tmp/$(MODULE_NAME)-latest-py3-none-any.whl
	rm -rf $(MODULE_NAME)/build/
	rm -rf $(MODULE_NAME)/$(MODULE_NAME).egg-info/
	cd $(MODULE_NAME)/ && conda run -n ${CONDA_ENV_NAME} python3 -m build --wheel
	# Do some sanity checks on the wheel output.
	BASE_VERS=`conda run -n ${CONDA_ENV_NAME} python3 $(MODULE_NAME)/$(MODULE_NAME)/version.py | cut -d. -f-2 | egrep -o '^[0-9.]+' || echo err-unknown-base-version` \
		&& TAG_VERS=`git tag -l --sort=-version:refname | egrep -x '^v[0-9.]+' | head -n1 | sed 's/^v//' | cut -d. -f-2 | egrep -x '[0-9.]+' || echo err-unknown-tag-version` \
		&& ls $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -F -e $$BASE_VERS -e $$TAG_VERS
	# Check to make sure the tests were excluded from the wheel.
	! ( unzip -t $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -m1 tests/ )
	# Make sure the py.typed marker file exists.
	unzip -t $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -m1 /py.typed
	# Check to make sure the mlos_bench module has the config directory.
	[ "$(MODULE_NAME)" != "mlos_bench" ] || unzip -t $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -m1 mlos_bench/config/
	# Check to make sure the README contents made it into the package metadata.
	unzip -p $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl */METADATA | egrep -v '^[A-Z][a-zA-Z-]+:' | grep -q -i '^# mlos'
	# Also check that the they include the URL
	unzip -p $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl */METADATA | grep -q -e '](https://github.com/microsoft/MLOS/'
	# Link it into place
	cd $(MODULE_NAME)/dist/tmp && ln -s ../$(MODULE_NAME)-*-py3-none-any.whl $(MODULE_NAME)-latest-py3-none-any.whl

.PHONY: clean-dist-test-env
clean-dist-test-env:
	# Remove any existing mlos-dist-test environment so we can start clean.
	conda env remove -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) 2>/dev/null || true
	rm -f build/dist-test-env.$(PYTHON_VERSION).build-stamp

.PHONY: dist-test-env
dist-test-env: dist build/dist-test-env.$(PYTHON_VERSION).build-stamp

build/dist-test-env.$(PYTHON_VERSION).build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
# Use the same version of python as the one we used to build the wheels.
build/dist-test-env.$(PYTHON_VERSION).build-stamp: PYTHON_VERS_REQ=$(shell conda list -n ${CONDA_ENV_NAME} | egrep '^python\s+' | sed -r -e 's/^python[ \t]+//' | cut -d' ' -f1 | cut -d. -f1-2)
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl
	# Create a clean test environment for checking the wheel files.
	$(MAKE) clean-dist-test-env
	conda create -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) python=$(PYTHON_VERS_REQ)
	# Install some additional dependencies necessary for clean building some of the wheels.
	conda install -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) swig libpq
	# Test a clean install of the mlos_core wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "`readlink -f mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl`[full-tests]"
	# Test a clean install of the mlos_bench wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "`readlink -f mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl`[full-tests]"
	# Test that the config dir for mlos_bench got distributed.
	test -e `conda env list | grep "mlos-dist-test-$(PYTHON_VERSION) " | awk '{ print $$2 }'`/lib/python$(PYTHON_VERS_REQ)/site-packages/mlos_bench/config/README.md
	# Test a clean install of the mlos_viz wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "`readlink -f mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl`[full-tests]"
	touch $@

.PHONY: dist-test
#dist-test: clean-dist
dist-test: dist-test-env build/dist-test.$(PYTHON_VERSION).build-stamp

# Unnecessary if we invoke it as "python3 -m pytest ..."
build/dist-test.$(PYTHON_VERSION).build-stamp: $(PYTHON_FILES) build/dist-test-env.$(PYTHON_VERSION).build-stamp
	# Make sure we're using the packages from the wheel.
	# Note: this will pick up the local directory and change the output if we're using PYTHONPATH=.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip list --verbose | grep mlos-core | grep ' pip'
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip list --verbose | grep mlos-bench | grep ' pip'
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip list --verbose | grep mlos-viz | grep ' pip'
	# Run a simple test that uses the mlos_core wheel (full tests can be checked with `make test`).
	conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_core/mlos_core/tests/spaces/spaces_test.py
	# Run a simple test that uses the mlos_bench wheel (full tests can be checked with `make test`).
	conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_bench/mlos_bench/tests/environments/mock_env_test.py
	# Run a basic cli tool check.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) mlos_bench --help 2>&1 | grep '^usage: mlos_bench '
	# Run a simple test that uses the mlos_viz wheel (full tests can be checked with `make test`).
	# To do that, we need the fixtures from mlos_bench, so make those available too.
	PYTHONPATH=mlos_bench conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_viz/mlos_viz/tests/test_dabl_plot.py
	touch $@

clean-dist-test: clean-dist-test-env
	rm -f build/dist-test-env.$(PYTHON_VERSION).build-stamp


.PHONY: publish
publish: publish-pypi

.PHONY:
publish-pypi-deps: build/publish-pypi-deps.${CONDA_ENV_NAME}.build-stamp

build/publish-pypi-deps.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
	conda run -n ${CONDA_ENV_NAME} pip install -U twine
	touch $@

PUBLISH_DEPS := build/publish-pypi-deps.${CONDA_ENV_NAME}.build-stamp
PUBLISH_DEPS += build/pytest.${CONDA_ENV_NAME}.build-stamp
PUBLISH_DEPS += mlos_core/dist/tmp/mlos_core-latest.tar.gz
PUBLISH_DEPS += mlos_bench/dist/tmp/mlos_bench-latest.tar.gz
PUBLISH_DEPS += mlos_viz/dist/tmp/mlos_viz-latest.tar.gz
PUBLISH_DEPS += mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl
PUBLISH_DEPS += mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl
PUBLISH_DEPS += mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl
PUBLISH_DEPS += build/dist-test.$(PYTHON_VERSION).build-stamp
PUBLISH_DEPS += build/check-doc.build-stamp
PUBLISH_DEPS += build/linklint-doc.build-stamp

build/publish.${CONDA_ENV_NAME}.%.py.build-stamp: $(PUBLISH_DEPS)
	# Basic sanity checks on files about to be published.
	# Run "make clean-dist && make dist" if these fail.
	# Check the tar count.
	test `ls -1 mlos_core/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_bench/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_viz/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_*/dist/*.tar.gz | wc -l` -eq 3
	# Check the whl count.
	test `ls -1 mlos_core/dist/*.whl | wc -l` -eq 1
	test `ls -1 mlos_bench/dist/*.whl | wc -l` -eq 1
	test `ls -1 mlos_viz/dist/*.whl | wc -l` -eq 1
	test `ls -1 mlos_*/dist/*.whl | wc -l` -eq 3
	# Publish the files to the specified repository.
	repo_name=`echo "$@" | sed -r -e 's|build/publish\.[^.]+\.||' -e 's|\.py\.build-stamp||'` \
		&& conda run -n ${CONDA_ENV_NAME} python3 -m twine upload --repository $$repo_name \
			mlos_*/dist/mlos*-*.tar.gz mlos_*/dist/mlos*-*.whl
	touch $@

publish-pypi: build/publish.${CONDA_ENV_NAME}.pypi.py.build-stamp
publish-test-pypi: build/publish.${CONDA_ENV_NAME}.testpypi.py.build-stamp

notebook-exec-test: build/notebook-exec-test.${CONDA_ENV_NAME}.build-stamp

build/notebook-exec-test.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp $(NOTEBOOK_FILES)
	find . -name '*.ipynb' -not -path '*/build/*' -print0 | xargs -0 -n1 -P0 conda run -n ${CONDA_ENV_NAME} python -m jupyter execute
	touch $@

build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: doc/requirements.txt
	conda run -n ${CONDA_ENV_NAME} pip install -U -r doc/requirements.txt
	touch $@

.PHONY: doc-prereqs
doc-prereqs: build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp build/unshallow.build-stamp

.PHONY: clean-doc-env
clean-doc-env:
	rm -f build/doc-prereqs.build-stamp
	rm -f build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp

COMMON_DOC_FILES := build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp doc/source/*.rst doc/source/_templates/*.rst doc/source/conf.py

SPHINX_API_RST_FILES := doc/source/index.rst doc/source/mlos_bench.run.usage.rst

ifeq ($(SKIP_COVERAGE),)
doc/build/html/index.html: build/pytest.${CONDA_ENV_NAME}.build-stamp
doc/build/html/htmlcov/index.html: build/pytest.${CONDA_ENV_NAME}.build-stamp
endif

# Treat warnings as failures.
SPHINXOPTS ?= # -v # be verbose
SPHINXOPTS += -n -W -w $(CURDIR)/doc/build/sphinx-build.warn.log -j auto

doc/source/generated/mlos_bench.run.usage.txt: build/conda-env.${CONDA_ENV_NAME}.build-stamp
doc/source/generated/mlos_bench.run.usage.txt: $(MLOS_BENCH_PYTHON_FILES)
	# Generate the help output from mlos_bench CLI for the docs.
	mkdir -p doc/source/generated/
	conda run -n ${CONDA_ENV_NAME} mlos_bench --help > doc/source/generated/mlos_bench.run.usage.txt

doc/build/html/index.html: build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp
doc/build/html/index.html: doc/source/generated/mlos_bench.run.usage.txt
doc/build/html/index.html: $(MLOS_CORE_PYTHON_FILES)
doc/build/html/index.html: $(MLOS_BENCH_PYTHON_FILES)
doc/build/html/index.html: $(MLOS_VIZ_PYTHON_FILES)
doc/build/html/index.html: $(SPHINX_API_RST_FILES) doc/Makefile doc/source/conf.py
doc/build/html/index.html: doc/copy-source-tree-docs.sh $(MD_FILES)
	#@rm -rf doc/build	# let us cache things
	@mkdir -p doc/build
	@rm -f doc/build/log.txt

	# Make sure that at least placeholder doc badges are there.
	mkdir -p doc/source/badges/
	touch doc/source/badges/coverage.svg
	touch doc/source/badges/tests.svg

	# Copy some of the source tree markdown docs into place.
	./doc/copy-source-tree-docs.sh

	# Build the rst files into html.
	conda run -n ${CONDA_ENV_NAME} $(MAKE) SPHINXOPTS="$(SPHINXOPTS)" -C doc/ $(MAKEFLAGS) html \
		>> doc/build/log.txt 2>&1 \
		|| { cat doc/build/log.txt; exit 1; }
	# DONE: Add some output filtering for this so we can more easily see what went wrong.
	# (e.g. skip complaints about missing .examples files)
	# See check-doc

.PHONY: doc
doc: doc/build/html/.nojekyll doc-test

.PHONY: doc-test
doc-test: build/check-doc.build-stamp build/linklint-doc.build-stamp

doc/build/html/htmlcov/index.html: doc/build/html/index.html
	# Make the codecov html report available for the site.
	test -d htmlcov && cp -a htmlcov doc/build/html/ || true
	mkdir -p doc/build/html/htmlcov
	touch doc/build/html/htmlcov/index.html

doc/build/html/.nojekyll: doc/build/html/index.html doc/build/html/htmlcov/index.html
	# Make sure that github pages doesn't try to run jekyll on the docs.
	touch doc/build/html/.nojekyll

.PHONY: check-doc
check-doc: build/check-doc.build-stamp

build/check-doc.build-stamp: doc/build/html/index.html doc/build/html/htmlcov/index.html
	# Check for a few files to make sure the docs got generated in a way we want.
	test -s doc/build/html/index.html
	grep -q BaseOptimizer doc/build/html/autoapi/mlos_core/optimizers/optimizer/index.html
	grep -q Environment doc/build/html/autoapi/mlos_bench/environments/base_environment/index.html
	grep -q plot doc/build/html/autoapi/mlos_viz/index.html
	test -s doc/build/html/autoapi/mlos_core/index.html
	test -s doc/build/html/autoapi/mlos_bench/index.html
	test -s doc/build/html/autoapi/mlos_viz/index.html
	test -s doc/build/html/autoapi/mlos_viz/dabl/index.html
	grep -q -e '--config CONFIG' doc/build/html//mlos_bench.run.usage.html
	# Check doc logs for errors (but skip over some known ones) ...
	@cat doc/build/log.txt \
		| egrep -C1 -e WARNING -e CRITICAL -e ERROR \
		| egrep -v \
			-e "warnings.warn\(f'\"{wd.path}\" is shallow and may cause errors'\)" \
			-e "No such file or directory: '.*.examples'.( \[docutils\]\s*)?$$" \
			-e "toctree contains reference to nonexisting document 'auto_examples/index'" \
			-e '^make.*resetting jobserver mode' \
			-e 'from cryptography.hazmat.primitives.ciphers.algorithms import' \
		| grep -v '^\s*$$' \
		| if grep .; then echo "Errors found in doc build. Check doc/build/log.txt for details."; cat doc/build/log.txt; exit 1; else exit 0; fi
	touch $@

.PHONY: linklint-doc
ifeq ($(DOCKER),)
linklint-doc:
	@echo "NOTE: linklint-doc target requires docker."
else
linklint-doc: build/linklint-doc.build-stamp
endif

.PHONY: nginx_port_env
nginx_port_env:
	@echo "Starting nginx docker container for serving docs."
	./doc/nginx-docker.sh restart
	nginx_port=`docker port mlos-doc-nginx | grep 0.0.0.0:8080 | cut -d/ -f1` \
		&& echo nginx_port=$${nginx_port} > doc/build/nginx_port.env

build/linklint-doc.build-stamp: nginx_port=$(shell cat doc/build/nginx_port.env | cut -d= -f2 | egrep -x '[0-9]+')
build/linklint-doc.build-stamp: doc/build/html/index.html doc/build/html/htmlcov/index.html build/check-doc.build-stamp nginx_port_env
	@echo "Running linklint on the docs at http://localhost:${nginx_port}/MLOS/ ..."
	docker exec mlos-doc-nginx curl -sSf http://localhost:${nginx_port}/MLOS/index.html >/dev/null
	docker exec mlos-doc-nginx linklint -root /doc/build/html/ /@ -error -warn > doc/build/linklint.out 2>&1
	docker exec mlos-doc-nginx linklint -net -redirect -host localhost:${nginx_port} /MLOS/@ -http -error -warn > doc/build/linklint.out 2>&1
	@if cat doc/build/linklint.out | grep -e ^ERROR -e ^WARN | grep -v 'missing named anchors' | grep -q .; then \
		echo "Found errors in the documentation:"; cat doc/build/linklint.out; exit 1; \
	fi
	@echo "OK"
	touch $@


.PHONY: clean-doc
clean-doc:
	rm -rf doc/build/ doc/global/ doc/source/api/ doc/source/generated doc/source/autoapi
	rm -rf doc/source/source_tree_docs/*

.PHONY: clean-format
clean-format:
	rm -f build/black.${CONDA_ENV_NAME}.build-stamp
	rm -f build/black.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/docformatter.${CONDA_ENV_NAME}.build-stamp
	rm -f build/docformatter.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/isort.${CONDA_ENV_NAME}.build-stamp
	rm -f build/isort.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
	rm -f build/licenseheaders-prereqs.${CONDA_ENV_NAME}.build-stamp
	rm -f build/format.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-check
clean-check:
	rm -f build/pylint.build-stamp
	rm -f build/pylint.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pylint.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/mypy.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/black-check.build-stamp
	rm -f build/black-check.${CONDA_ENV_NAME}.build-stamp
	rm -f build/black-check.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/docformatter-check.${CONDA_ENV_NAME}.build-stamp
	rm -f build/docformatter-check.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/isort-check.${CONDA_ENV_NAME}.build-stamp
	rm -f build/isort-check.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pycodestyle.build-stamp
	rm -f build/pycodestyle.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pycodestyle.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pydocstyle.build-stamp
	rm -f build/pydocstyle.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pydocstyle.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/check.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-test
clean-test:
	rm -f build/pytest.build-stamp
	rm -f build/pytest.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pytest.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pytest.mlos_*.${CONDA_ENV_NAME}.needs-build-stamp
	rm -rf .pytest_cache/
	rm -f coverage.xml .coverage* build/.converage*
	rm -rf htmlcov/
	rm -rf junit/
	rm -rf test-output.xml

.PHONY: clean-dist
clean-dist:
	rm -rf dist
	rm -rf mlos_core/build mlos_core/dist
	rm -rf mlos_bench/build mlos_bench/dist
	rm -rf mlos_viz/build mlos_viz/dist

.PHONY: clean
clean: clean-format clean-check clean-test clean-dist clean-doc clean-doc-env clean-dist-test
	rm -f build/unshallow.build-stamp
	rm -f .*.build-stamp
	rm -f build/conda-env.build-stamp build/conda-env.*.build-stamp
	rm -rf mlos_core.egg-info
	rm -rf mlos_core/mlos_core.egg-info
	rm -rf mlos_bench.egg-info
	rm -rf mlos_bench/mlos_bench.egg-info
	rm -rf mlos_viz.egg-info
	rm -rf mlos_viz/mlos_viz.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -print0 | xargs -t -r -0 rm -rf
	find . -type f -name '*.pyc' -print0 | xargs -t -r -0 rm -f

.PHONY: devcontainer
devcontainer:
	./.devcontainer/build/build-devcontainer.sh
	@echo
	@echo "Run ./.devcontainer/scripts/run-devcontainer.sh to start the newly built devcontainer."
