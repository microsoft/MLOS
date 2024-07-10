# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

CONDA_ENV_NAME ?= mlos
PYTHON_VERSION := $(shell echo "${CONDA_ENV_NAME}" | sed -r -e 's/^mlos[-]?//')
ENV_YML := conda-envs/${CONDA_ENV_NAME}.yml

# Find the non-build python files we should consider as rule dependencies.
PYTHON_FILES := $(shell find ./ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./(mlos_(core|bench|viz)/)?build/' -e '^./doc/source/')
MLOS_CORE_PYTHON_FILES := $(shell find ./mlos_core/ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./mlos_core/build/')
MLOS_BENCH_PYTHON_FILES := $(shell find ./mlos_bench/ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./mlos_bench/build/')
MLOS_VIZ_PYTHON_FILES := $(shell find ./mlos_viz/ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./mlos_viz/build/')
SCRIPT_FILES := $(shell find ./ -name '*.sh' -or -name '*.ps1' -or -name '*.cmd')
SQL_FILES := $(shell find ./ -name '*.sql')
MD_FILES := $(shell find ./ -name '*.md' | grep -v '^./doc/')

DOCKER := $(shell which docker)
# Make sure the build directory exists.
MKDIR_BUILD := $(shell test -d build || mkdir build)

# Allow overriding the default verbosity of conda for CI jobs.
#CONDA_INFO_LEVEL ?= -q

# Run make in parallel by default.
MAKEFLAGS += -j$(shell nproc)
#MAKEFLAGS += -Oline

.PHONY: all
all: format check test dist dist-test doc | conda-env

.PHONY: conda-env
conda-env: build/conda-env.${CONDA_ENV_NAME}.build-stamp

MLOS_CORE_CONF_FILES := mlos_core/pyproject.toml mlos_core/setup.py mlos_core/MANIFEST.in
MLOS_BENCH_CONF_FILES := mlos_bench/pyproject.toml mlos_bench/setup.py mlos_bench/MANIFEST.in
MLOS_VIZ_CONF_FILES := mlos_viz/pyproject.toml mlos_viz/setup.py mlos_viz/MANIFEST.in
MLOS_GLOBAL_CONF_FILES := setup.cfg # pyproject.toml

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


# Since these targets potentially change the files we need to run them in sequence.
# In future versions of make we can do that by marking each as a .NOTPARALLEL psuedo target.
# But with make 4.3 that changes the entire Makefile to be serial.

# Here we make dynamic prereqs to apply to other targets that need to run in sequence.
FORMAT_PREREQS :=

.PHONY: format
format: build/format.${CONDA_ENV_NAME}.build-stamp

ifneq (,$(filter format,$(MAKECMDGOALS)))
    FORMAT_PREREQS += build/format.${CONDA_ENV_NAME}.build-stamp
endif

build/format.${CONDA_ENV_NAME}.build-stamp: build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
# TODO: enable isort and black formatters
#build/format.${CONDA_ENV_NAME}.build-stamp: build/isort.${CONDA_ENV_NAME}.build-stamp
#build/format.${CONDA_ENV_NAME}.build-stamp: build/black.${CONDA_ENV_NAME}.build-stamp
build/format.${CONDA_ENV_NAME}.build-stamp:
	touch $@

.PHONY: licenseheaders
licenseheaders: build/licenseheaders.${CONDA_ENV_NAME}.build-stamp

ifneq (,$(filter licenseheaders,$(MAKECMDGOALS)))
    FORMAT_PREREQS += build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
endif

build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES)
build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: $(SCRIPT_FILES)
build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: $(SQL_FILES) doc/mit-license.tmpl
build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: doc/mit-license.tmpl
build/licenseheaders.${CONDA_ENV_NAME}.build-stamp:
	# Note: to avoid makefile dependency loops, we don't touch the setup.py
	# files as that would force the conda-env to be rebuilt.
	conda run -n ${CONDA_ENV_NAME} licenseheaders -t doc/mit-license.tmpl \
		-E .py .sh .ps1 .sql .cmd \
		-x mlos_bench/setup.py mlos_core/setup.py mlos_viz/setup.py
	touch $@

.PHONY: isort
isort: build/isort.${CONDA_ENV_NAME}.build-stamp

ifneq (,$(filter isort,$(MAKECMDGOALS)))
    FORMAT_PREREQS += build/isort.${CONDA_ENV_NAME}.build-stamp
endif

build/isort.${CONDA_ENV_NAME}.build-stamp: build/isort.mlos_core.${CONDA_ENV_NAME}.build-stamp
build/isort.${CONDA_ENV_NAME}.build-stamp: build/isort.mlos_bench.${CONDA_ENV_NAME}.build-stamp
build/isort.${CONDA_ENV_NAME}.build-stamp: build/isort.mlos_viz.${CONDA_ENV_NAME}.build-stamp
build/isort.${CONDA_ENV_NAME}.build-stamp:
	touch $@

# NOTE: when using pattern rules (involving %) we can only add one line of
# prerequisities, so we use this pattern to compose the list as variables.

# Both isort and licenseheaders alter files, so only run one at a time, by
# making licenseheaders an order-only prerequisite.
ISORT_COMMON_PREREQS :=
ifneq (,$(filter format licenseheaders,$(MAKECMDGOALS)))
ISORT_COMMON_PREREQS += build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
endif
ISORT_COMMON_PREREQS += build/conda-env.${CONDA_ENV_NAME}.build-stamp
ISORT_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/isort.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/isort.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/isort.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/isort.%.${CONDA_ENV_NAME}.build-stamp: $(ISORT_COMMON_PREREQS)
	# Reformat python file imports with isort.
	conda run -n ${CONDA_ENV_NAME} isort --verbose --only-modified --atomic -j0 $(filter %.py,$?)
	touch $@

.PHONY: black
black: build/black.${CONDA_ENV_NAME}.build-stamp

ifneq (,$(filter black,$(MAKECMDGOALS)))
    FORMAT_PREREQS += build/black.${CONDA_ENV_NAME}.build-stamp
endif

build/black.${CONDA_ENV_NAME}.build-stamp: build/black.mlos_core.${CONDA_ENV_NAME}.build-stamp
build/black.${CONDA_ENV_NAME}.build-stamp: build/black.mlos_bench.${CONDA_ENV_NAME}.build-stamp
build/black.${CONDA_ENV_NAME}.build-stamp: build/black.mlos_viz.${CONDA_ENV_NAME}.build-stamp
build/black.${CONDA_ENV_NAME}.build-stamp:
	touch $@

# Both black, licenseheaders, and isort all alter files, so only run one at a time, by
# making licenseheaders and isort an order-only prerequisite.
BLACK_COMMON_PREREQS :=
ifneq (,$(filter format licenseheaders,$(MAKECMDGOALS)))
BLACK_COMMON_PREREQS += build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
endif
ifneq (,$(filter format isort,$(MAKECMDGOALS)))
BLACK_COMMON_PREREQS += build/isort.${CONDA_ENV_NAME}.build-stamp
endif
BLACK_COMMON_PREREQS += build/conda-env.${CONDA_ENV_NAME}.build-stamp
BLACK_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/black.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/black.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/black.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/black.%.${CONDA_ENV_NAME}.build-stamp: $(BLACK_COMMON_PREREQS)
	# Reformat python files with black.
	conda run -n ${CONDA_ENV_NAME} black $(filter %.py,$?)
	touch $@

.PHONY: check
check: pycodestyle pydocstyle pylint mypy # cspell markdown-link-check
# TODO: Enable isort and black checks
#check: isort-check black-check pycodestyle pydocstyle pylint mypy # cspell markdown-link-check

.PHONY: black-check
black-check: build/black-check.mlos_core.${CONDA_ENV_NAME}.build-stamp
black-check: build/black-check.mlos_bench.${CONDA_ENV_NAME}.build-stamp
black-check: build/black-check.mlos_viz.${CONDA_ENV_NAME}.build-stamp

# Make sure black format rules run before black-check rules.
build/black-check.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/black-check.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/black-check.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

BLACK_CHECK_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
BLACK_CHECK_COMMON_PREREQS += $(FORMAT_PREREQS)
BLACK_CHECK_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/black-check.%.${CONDA_ENV_NAME}.build-stamp: $(BLACK_CHECK_COMMON_PREREQS)
	# Check for import sort order.
	# Note: if this fails use "make format" or "make black" to fix it.
	conda run -n ${CONDA_ENV_NAME} black --verbose --check --diff $(filter %.py,$?)
	touch $@

.PHONY: isort-check
isort-check: build/isort-check.mlos_core.${CONDA_ENV_NAME}.build-stamp
isort-check: build/isort-check.mlos_bench.${CONDA_ENV_NAME}.build-stamp
isort-check: build/isort-check.mlos_viz.${CONDA_ENV_NAME}.build-stamp

# Make sure isort format rules run before isort-check rules.
build/isort-check.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/isort-check.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/isort-check.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

ISORT_CHECK_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
ISORT_CHECK_COMMON_PREREQS += $(FORMAT_PREREQS)
ISORT_CHECK_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/isort-check.%.${CONDA_ENV_NAME}.build-stamp: $(ISORT_CHECK_COMMON_PREREQS)
	# Note: if this fails use "make format" or "make isort" to fix it.
	conda run -n ${CONDA_ENV_NAME} isort --only-modified --check --diff -j0 $(filter %.py,$?)
	touch $@

.PHONY: pycodestyle
pycodestyle: build/pycodestyle.mlos_core.${CONDA_ENV_NAME}.build-stamp
pycodestyle: build/pycodestyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pycodestyle: build/pycodestyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp

build/pycodestyle.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pycodestyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pycodestyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

PYCODESTYLE_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
PYCODESTYLE_COMMON_PREREQS += $(FORMAT_PREREQS)
PYCODESTYLE_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/pycodestyle.%.${CONDA_ENV_NAME}.build-stamp: $(PYCODESTYLE_COMMON_PREREQS)
	# Check for decent pep8 code style with pycodestyle.
	# Note: if this fails, try using 'make format' to fix it.
	conda run -n ${CONDA_ENV_NAME} pycodestyle $(filter %.py,$+)
	touch $@

.PHONY: pydocstyle
pydocstyle: build/pydocstyle.mlos_core.${CONDA_ENV_NAME}.build-stamp
pydocstyle: build/pydocstyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pydocstyle: build/pydocstyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp

build/pydocstyle.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pydocstyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pydocstyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

PYDOCSTYLE_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
PYDOCSTYLE_COMMON_PREREQS += $(FORMAT_PREREQS)
PYDOCSTYLE_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/pydocstyle.%.${CONDA_ENV_NAME}.build-stamp: $(PYDOCSTYLE_COMMON_PREREQS)
	# Check for decent pep8 doc style with pydocstyle.
	conda run -n ${CONDA_ENV_NAME} pydocstyle $(filter %.py,$+)
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

.PHONY: pylint
pylint: build/pylint.mlos_core.${CONDA_ENV_NAME}.build-stamp
pylint: build/pylint.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pylint: build/pylint.mlos_viz.${CONDA_ENV_NAME}.build-stamp


build/pylint.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pylint.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pylint.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

PYLINT_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
PYLINT_COMMON_PREREQS += $(FORMAT_PREREQS)
PYLINT_COMMON_PREREQS += .pylintrc

build/pylint.%.${CONDA_ENV_NAME}.build-stamp: $(PYLINT_COMMON_PREREQS)
	conda run -n ${CONDA_ENV_NAME} pylint -j0 $(filter %.py,$+)
	touch $@

.PHONY: flake8
flake8: build/flake8.mlos_core.${CONDA_ENV_NAME}.build-stamp
flake8: build/flake8.mlos_bench.${CONDA_ENV_NAME}.build-stamp
flake8: build/flake8.mlos_viz.${CONDA_ENV_NAME}.build-stamp

build/flake8.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/flake8.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/flake8.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

FLAKE8_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
FLAKE8_COMMON_PREREQS += $(FORMAT_PREREQS)
FLAKE8_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)

build/flake8.%.${CONDA_ENV_NAME}.build-stamp: $(FLAKE8_COMMON_PREREQS)
	conda run -n ${CONDA_ENV_NAME} flake8 -j0 $(filter %.py,$+)
	touch $@

.PHONY: mypy
mypy: build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp
mypy: build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp
mypy: build/mypy.mlos_viz.${CONDA_ENV_NAME}.build-stamp


# Run these in order.
build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES) build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp
build/mypy.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES) build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp

MYPY_COMMON_PREREQS := build/conda-env.${CONDA_ENV_NAME}.build-stamp
MYPY_COMMON_PREREQS += $(FORMAT_PREREQS)
MYPY_COMMON_PREREQS += $(MLOS_GLOBAL_CONF_FILES)
MYPY_COMMON_PREREQS += scripts/dmypy-wrapper.sh

build/mypy.%.${CONDA_ENV_NAME}.build-stamp: $(MYPY_COMMON_PREREQS)
	conda run -n ${CONDA_ENV_NAME} scripts/dmypy-wrapper.sh \
		$(filter %.py,$+)
	touch $@


.PHONY: test
test: pytest

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

# Invividual package test rules (for tight loop dev work).
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
		&& ls $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar.gz | grep -F $$BASE_VERS
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
		&& ls $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -F $$BASE_VERS
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
build/dist-test-env.$(PYTHON_VERSION).build-stamp: PYTHON_VERS_REQ=$(shell conda list -n ${CONDA_ENV_NAME} | egrep '^python\s+' | sed -r -e 's/^python\s+//' | cut -d' ' -f1 | cut -d. -f1-2)
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl
	# Create a clean test environment for checking the wheel files.
	$(MAKE) clean-dist-test-env
	conda create -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) python=$(PYTHON_VERS_REQ)
	# Install some additional dependencies necessary for clean building some of the wheels.
	conda install -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) swig libpq
	# Test a clean install of the mlos_core wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl[full-tests]"
	# Test a clean install of the mlos_bench wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl[full-tests]"
	# Test that the config dir for mlos_bench got distributed.
	test -e `conda env list | grep "mlos-dist-test-$(PYTHON_VERSION) " | awk '{ print $$2 }'`/lib/python$(PYTHON_VERS_REQ)/site-packages/mlos_bench/config/README.md
	# Test a clean install of the mlos_viz wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl[full-tests]"
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
PUBLISH_DEPS += build/dist-test.$(PYTHON_VERSION).build-stamp
PUBLISH_DEPS += build/check-doc.build-stamp
PUBLISH_DEPS += build/linklint-doc.build-stamp

build/publish.${CONDA_ENV_NAME}.%.py.build-stamp: $(PUBLISH_DEPS)
	test `ls -1 mlos_core/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_bench/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_viz/dist/*.tar.gz | wc -l` -eq 1
	test `ls -1 mlos_*/dist/*.tar.gz | wc -l` -eq 3
	repo_name=`echo "$@" | sed -r -e 's|build/publish\.[^.]+\.||' -e 's|\.py\.build-stamp||'` \
		&& conda run -n ${CONDA_ENV_NAME} python3 -m twine upload --repository $$repo_name \
			mlos_*/dist/mlos*-*.tar.gz mlos_*/dist/mlos*-*.whl
	touch $@

publish-pypi: build/publish.${CONDA_ENV_NAME}.pypi.py.build-stamp
publish-test-pypi: build/publish.${CONDA_ENV_NAME}.testpypi.py.build-stamp


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

doc/source/api/mlos_core/modules.rst: $(FORMAT_PREREQS) $(COMMON_DOC_FILES)
doc/source/api/mlos_core/modules.rst: $(MLOS_CORE_PYTHON_FILES)
	rm -rf doc/source/api/mlos_core
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M \
		-o source/api/mlos_core/ \
		../mlos_core/ \
		../mlos_core/setup.py ../mlos_core/mlos_core/tests/

doc/source/api/mlos_bench/modules.rst: $(FORMAT_PREREQS) $(COMMON_DOC_FILES)
doc/source/api/mlos_bench/modules.rst: $(MLOS_BENCH_PYTHON_FILES)
	rm -rf doc/source/api/mlos_bench
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M \
		-o source/api/mlos_bench/ \
		../mlos_bench/ \
		../mlos_bench/setup.py ../mlos_bench/mlos_bench/tests/
	# Save the help output of the mlos_bench scripts to include in the documentation.
	# First make sure that the latest version of mlos_bench is installed (since it uses git based tagging).
	conda run -n ${CONDA_ENV_NAME} pip install -e mlos_core -e mlos_bench -e mlos_viz
	conda run -n ${CONDA_ENV_NAME} mlos_bench --help > doc/source/api/mlos_bench/mlos_bench.run.usage.txt
	echo ".. literalinclude:: mlos_bench.run.usage.txt" >> doc/source/api/mlos_bench/mlos_bench.run.rst
	echo "   :language: none" >> doc/source/api/mlos_bench/mlos_bench.run.rst

doc/source/api/mlos_viz/modules.rst: $(FORMAT_PREREQS) $(COMMON_DOC_FILES)
doc/source/api/mlos_viz/modules.rst: $(MLOS_VIZ_PYTHON_FILES)
	rm -rf doc/source/api/mlos_viz
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M \
		-o source/api/mlos_viz/ \
		../mlos_viz/ \
		../mlos_viz/setup.py ../mlos_viz/mlos_viz/tests/

SPHINX_API_RST_FILES := doc/source/api/mlos_core/modules.rst
SPHINX_API_RST_FILES += doc/source/api/mlos_bench/modules.rst
SPHINX_API_RST_FILES += doc/source/api/mlos_viz/modules.rst

.PHONY: sphinx-apidoc
sphinx-apidoc: $(SPHINX_API_RST_FILES)

ifeq ($(SKIP_COVERAGE),)
doc/build/html/index.html: build/pytest.${CONDA_ENV_NAME}.build-stamp
doc/build/html/htmlcov/index.html: build/pytest.${CONDA_ENV_NAME}.build-stamp
endif

doc/build/html/index.html: $(SPHINX_API_RST_FILES) doc/Makefile doc/copy-source-tree-docs.sh $(MD_FILES)
	@rm -rf doc/build
	@mkdir -p doc/build
	@rm -f doc/build/log.txt

	# Make sure that at least placeholder doc badges are there.
	mkdir -p doc/source/badges/
	touch doc/source/badges/coverage.svg
	touch doc/source/badges/tests.svg

	# Copy some of the source tree markdown docs into place.
	./doc/copy-source-tree-docs.sh

	# Build the rst files into html.
	conda run -n ${CONDA_ENV_NAME} $(MAKE) -C doc/ $(MAKEFLAGS) html \
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
	test -s doc/build/html/generated/mlos_core.optimizers.optimizer.BaseOptimizer.html
	test -s doc/build/html/generated/mlos_bench.environments.Environment.html
	test -s doc/build/html/generated/mlos_viz.plot.html
	test -s doc/build/html/api/mlos_core/mlos_core.html
	test -s doc/build/html/api/mlos_bench/mlos_bench.html
	test -s doc/build/html/api/mlos_viz/mlos_viz.html
	test -s doc/build/html/api/mlos_viz/mlos_viz.dabl.html
	grep -q -e '--config CONFIG' doc/build/html/api/mlos_bench/mlos_bench.run.html
	# Check doc logs for errors (but skip over some known ones) ...
	@cat doc/build/log.txt \
		| egrep -C1 -e WARNING -e CRITICAL -e ERROR \
		| egrep -v \
			-e "warnings.warn\(f'\"{wd.path}\" is shallow and may cause errors'\)" \
			-e "No such file or directory: '.*.examples'.$$" \
			-e 'Problems with "include" directive path:' \
			-e 'duplicate object description' \
			-e "document isn't included in any toctree" \
			-e "more than one target found for cross-reference" \
			-e "toctree contains reference to nonexisting document 'auto_examples/index'" \
			-e "failed to import function 'create' from module '(SpaceAdapter|Optimizer)Factory'" \
			-e "No module named '(SpaceAdapter|Optimizer)Factory'" \
			-e '^make.*resetting jobserver mode' \
		| grep -v '^\s*$$' \
		| if grep .; then echo "Errors found in doc build. Check doc/build/log.txt for details."; exit 1; else exit 0; fi
	touch $@

.PHONY: linklint-doc
ifeq ($(DOCKER),)
linklint-doc:
	@echo "NOTE: linklint-doc target requires docker."
else
linklint-doc: build/linklint-doc.build-stamp
endif

build/linklint-doc.build-stamp: doc/build/html/index.html doc/build/html/htmlcov/index.html build/check-doc.build-stamp
	@echo "Starting nginx docker container for serving docs."
	./doc/nginx-docker.sh restart
	docker port mlos-doc-nginx
	nginx_port=`docker port mlos-doc-nginx | grep 0.0.0.0:8080 | cut -d/ -f1` \
		&& echo nginx_port=$${nginx_port} \
		&& set -x \
		&& docker exec mlos-doc-nginx curl -sSf http://localhost:$${nginx_port}/index.html >/dev/null
	@echo "Running linklint on the docs."
	docker exec mlos-doc-nginx linklint -net -redirect -root /doc/build/html/ /@ -error -warn > doc/build/linklint.out 2>&1
	@if cat doc/build/linklint.out | grep -e ^ERROR -e ^WARN | grep -v 'missing named anchors' | grep -q .; then \
		echo "Found errors in the documentation:"; cat doc/build/linklint.out; exit 1; \
	fi
	@echo "OK"
	touch $@


.PHONY: clean-doc
clean-doc:
	rm -rf doc/build/ doc/global/ doc/source/api/ doc/source/generated
	rm -rf doc/source/source_tree_docs/*

.PHONY: clean-format
clean-format:
	# TODO: add black and isort rules
	rm -f build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
	rm -f build/licenseheaders-prereqs.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-check
clean-check:
	rm -f build/pylint.build-stamp
	rm -f build/pylint.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pylint.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/mypy.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pycodestyle.build-stamp
	rm -f build/pycodestyle.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pycodestyle.mlos_*.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pydocstyle.build-stamp
	rm -f build/pydocstyle.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pydocstyle.mlos_*.${CONDA_ENV_NAME}.build-stamp

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
