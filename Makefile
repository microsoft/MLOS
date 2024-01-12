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
all: check test dist dist-test doc licenseheaders

.PHONY: conda-env
conda-env: build/conda-env.${CONDA_ENV_NAME}.build-stamp

build/conda-env.${CONDA_ENV_NAME}.build-stamp: ${ENV_YML} mlos_core/setup.py mlos_bench/setup.py mlos_viz/setup.py
	@echo "CONDA_SOLVER: ${CONDA_SOLVER}"
	@echo "CONDA_EXPERIMENTAL_SOLVER: ${CONDA_EXPERIMENTAL_SOLVER}"
	@echo "CONDA_INFO_LEVEL: ${CONDA_INFO_LEVEL}"
	conda env list -q | grep -q "^${CONDA_ENV_NAME} " || conda env create ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} -f ${ENV_YML}
	conda env update ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} --prune -f ${ENV_YML}
	$(MAKE) clean-check clean-test clean-doc
	touch $@

.PHONY: clean-conda-env
clean-conda-env:
	conda env remove -y ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME}
	rm -f build/conda-env.${CONDA_ENV_NAME}.build-stamp

.PHONY: check
check: pycodestyle pydocstyle pylint mypy # cspell licenseheaders markdown-link-check

.PHONY: pycodestyle
pycodestyle: conda-env
pycodestyle: build/pycodestyle.mlos_core.${CONDA_ENV_NAME}.build-stamp
pycodestyle: build/pycodestyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pycodestyle: build/pycodestyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp


build/pycodestyle.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pycodestyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pycodestyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/pycodestyle.%.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp setup.cfg
	# Check for decent pep8 code style with pycodestyle.
	# Note: if this fails, try using autopep8 to fix it.
	conda run -n ${CONDA_ENV_NAME} pycodestyle $(filter-out setup.cfg,$+)
	touch $@

.PHONY: pydocstyle
pydocstyle: conda-env
pydocstyle: build/pydocstyle.mlos_core.${CONDA_ENV_NAME}.build-stamp
pydocstyle: build/pydocstyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pydocstyle: build/pydocstyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp


build/pydocstyle.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pydocstyle.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pydocstyle.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/pydocstyle.%.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp setup.cfg
	# Check for decent pep8 doc style with pydocstyle.
	conda run -n ${CONDA_ENV_NAME} pydocstyle $(filter-out setup.cfg,$+)
	touch $@

.PHONY: licenseheaders
licenseheaders: build/licenseheaders.${CONDA_ENV_NAME}.build-stamp

build/licenseheaders.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES) $(SCRIPT_FILES) $(SQL_FILES) doc/mit-license.tmpl
	# Note: to avoid makefile dependency loops, we don't touch the setup.py
	# files as that would force the conda-env to be rebuilt.
	conda run -n ${CONDA_ENV_NAME} licenseheaders -t doc/mit-license.tmpl \
		-E .py .sh .ps1 .sql .cmd \
		-x mlos_bench/setup.py mlos_core/setup.py mlos_viz/setup.py
	touch $@

.PHONY: cspell
ifeq ($(DOCKER),)
cspell:
	@echo "NOTE: docker is not available. Skipping cspell check."
else
cspell: build/cspell-container.build-stamp
	./.devcontainer/scripts/run-cspell.sh
endif

build/cspell-container.build-stamp:
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

build/markdown-link-check-container.build-stamp:
	# Build the docker image with markdown-link-check in it.
	$(MAKE) -C .devcontainer/build markdown-link-check
	touch $@

.PHONY: pylint
pylint: conda-env
pylint: build/pylint.mlos_core.${CONDA_ENV_NAME}.build-stamp
pylint: build/pylint.mlos_bench.${CONDA_ENV_NAME}.build-stamp
pylint: build/pylint.mlos_viz.${CONDA_ENV_NAME}.build-stamp


build/pylint.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/pylint.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/pylint.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/pylint.%.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp .pylintrc
	conda run -n ${CONDA_ENV_NAME} pylint -j0 $(filter-out .pylintrc,$+)
	touch $@

.PHONY: flake8
flake8: conda-env
flake8: build/flake8.mlos_core.${CONDA_ENV_NAME}.build-stamp
flake8: build/flake8.mlos_bench.${CONDA_ENV_NAME}.build-stamp
flake8: build/flake8.mlos_viz.${CONDA_ENV_NAME}.build-stamp

build/flake8.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/flake8.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES)
build/flake8.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES)

build/flake8.%.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp setup.cfg
	conda run -n ${CONDA_ENV_NAME} flake8 -j0 $(filter-out setup.cfg,$+)
	touch $@

.PHONY: mypy
mypy: conda-env
mypy: build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp
mypy: build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp
mypy: build/mypy.mlos_viz.${CONDA_ENV_NAME}.build-stamp


build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp: $(MLOS_CORE_PYTHON_FILES)
build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp: $(MLOS_BENCH_PYTHON_FILES) build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp
build/mypy.mlos_viz.${CONDA_ENV_NAME}.build-stamp: $(MLOS_VIZ_PYTHON_FILES) build/mypy.mlos_bench.${CONDA_ENV_NAME}.build-stamp

NON_MYPY_FILES := scripts/dmypy-wrapper.sh build/conda-env.${CONDA_ENV_NAME}.build-stamp build/mypy.mlos_core.${CONDA_ENV_NAME}.build-stamp setup.cfg
build/mypy.%.${CONDA_ENV_NAME}.build-stamp: scripts/dmypy-wrapper.sh build/conda-env.${CONDA_ENV_NAME}.build-stamp setup.cfg
	conda run -n ${CONDA_ENV_NAME} scripts/dmypy-wrapper.sh \
		$(filter-out $(NON_MYPY_FILES),$+)
	touch $@


.PHONY: test
test: pytest

PYTEST_MODULES :=

.PHONY: pytest
pytest: conda-env build/pytest.${CONDA_ENV_NAME}.build-stamp

build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_CORE_PYTHON_FILES) conftest.py setup.cfg
build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp:
	# Update the PYTEST_MODULES list to include mlos_core.
	$(eval PYTEST_MODULES += mlos_core)
	echo "PYTEST_MODULES: $(PYTEST_MODULES)"
	touch $@

# Run the mlos_bench target update after mlos_core target update.
build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp: build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp
build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_BENCH_PYTHON_FILES) conftest.py setup.cfg
build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp:
	# Update the PYTEST_MODULES list to include mlos_bench.
	$(eval PYTEST_MODULES += mlos_bench)
	echo "PYTEST_MODULES: $(PYTEST_MODULES)"
	touch $@

# Run the mlos_viz target update after mlos_bench target update.
build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp: build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp
build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp: $(MLOS_VIZ_PYTHON_FILES) conftest.py setup.cfg
build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp:
	# Update the PYTEST_MODULES list to include mlos_viz.
	$(eval PYTEST_MODULES += mlos_viz)
	echo "PYTEST_MODULES: $(PYTEST_MODULES)"
	touch $@

PYTEST_OPTIONS :=

# Allow optionally skipping coverage calculations during local testing to skip up inner dev loop.
SKIP_COVERAGE := $(shell echo $${SKIP_COVERAGE:-} | grep -i -x -e 1 -e true)

ifeq ($(SKIP_COVERAGE),)
    PYTEST_OPTIONS += --cov=. --cov-append --cov-fail-under=91.5 --cov-report=xml --cov-report=html --junitxml=junit/test-results.xml --local-badge-output-dir=doc/source/badges/
endif

# Run the pytest target on only the modules that have changed recently, but
# make sure the coverage report is for both of them when used in the pipeline.
# NOTE: When run locally, the junit/test-results.xml will only include the
# tests from the latest run, but this file is only used for upstream reporting,
# so probably shouldn't matter.
build/pytest.${CONDA_ENV_NAME}.build-stamp: build/pytest.mlos_core.${CONDA_ENV_NAME}.needs-build-stamp
build/pytest.${CONDA_ENV_NAME}.build-stamp: build/pytest.mlos_bench.${CONDA_ENV_NAME}.needs-build-stamp
build/pytest.${CONDA_ENV_NAME}.build-stamp: build/pytest.mlos_viz.${CONDA_ENV_NAME}.needs-build-stamp
build/pytest.${CONDA_ENV_NAME}.build-stamp:
	# Make sure to update the list of modules needed everytime in case the test fails and we need to rerun it.
	for pytest_module in $(PYTEST_MODULES); do rm -f build/pytest.$${pytest_module}.${CONDA_ENV_NAME}.needs-build-stamp; done
	# Run pytest for the modules: $(PYTEST_MODULES)
	mkdir -p doc/source/badges/
	conda run -n ${CONDA_ENV_NAME} pytest $(PYTEST_OPTIONS) $(PYTEST_EXTRA_OPTIONS) $(PYTEST_MODULES)
	# Mark those as done again.
	for pytest_module in $(PYTEST_MODULES); do touch build/pytest.$${pytest_module}.${CONDA_ENV_NAME}.needs-build-stamp; done
	touch $@


.PHONY: dist
dist: bdist_wheel

.PHONY: bdist_wheel
bdist_wheel: conda-env
bdist_wheel: mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl
bdist_wheel: mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl
bdist_wheel: mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl

mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: mlos_core/dist/tmp/mlos-core-latest.tar
mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: MODULE_NAME := mlos_core
mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl: PACKAGE_NAME := mlos-core
mlos_core/dist/tmp/mlos-core-latest.tar: mlos_core/setup.py mlos_core/MANIFEST.in $(MLOS_CORE_PYTHON_FILES)
mlos_core/dist/tmp/mlos-core-latest.tar: MODULE_NAME := mlos_core
mlos_core/dist/tmp/mlos-core-latest.tar: PACKAGE_NAME := mlos-core

mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: mlos_bench/dist/tmp/mlos-bench-latest.tar
mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: MODULE_NAME := mlos_bench
mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl: PACKAGE_NAME := mlos-bench
mlos_bench/dist/tmp/mlos-bench-latest.tar: mlos_bench/setup.py mlos_bench/MANIFEST.in $(MLOS_BENCH_PYTHON_FILES)
mlos_bench/dist/tmp/mlos-bench-latest.tar: MODULE_NAME := mlos_bench
mlos_bench/dist/tmp/mlos-bench-latest.tar: PACKAGE_NAME := mlos-bench

mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: mlos_viz/dist/tmp/mlos-viz-latest.tar
mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: MODULE_NAME := mlos_viz
mlos_viz/dist/tmp/mlos_viz-latest-py3-none-any.whl: PACKAGE_NAME := mlos-viz
mlos_viz/dist/tmp/mlos-bench-latest.tar: mlos_viz/setup.py mlos_viz/MANIFEST.in $(mlos_viz_PYTHON_FILES)
mlos_viz/dist/tmp/mlos-bench-latest.tar: MODULE_NAME := mlos_viz
mlos_viz/dist/tmp/mlos-bench-latest.tar: PACKAGE_NAME := mlos-viz

%-latest.tar: build/conda-env.${CONDA_ENV_NAME}.build-stamp
%-latest.tar:
	mkdir -p $(MODULE_NAME)/dist/tmp
	rm -f $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar
	rm -f $(MODULE_NAME)/dist/tmp/$(PACKAGE_NAME)-latest.tar
	cd $(MODULE_NAME)/ && conda run -n ${CONDA_ENV_NAME} python3 setup.py sdist --formats tar
	ls $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar
	! ( tar tf $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar | grep -m1 tests/ )
	[ "$(MODULE_NAME)" != "mlos_bench" ] || tar tf $(MODULE_NAME)/dist/$(PACKAGE_NAME)-*.tar | grep -m1 mlos_bench/config/
	cd $(MODULE_NAME)/dist/tmp && ln -s ../$(PACKAGE_NAME)-*.tar $(PACKAGE_NAME)-latest.tar

%-latest-py3-none-any.whl: build/conda-env.${CONDA_ENV_NAME}.build-stamp
%-latest-py3-none-any.whl:
	rm -f $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl
	rm -f $(MODULE_NAME)/dist/tmp/$(MODULE_NAME)-latest-py3-none-any.whl
	cd $(MODULE_NAME)/ && conda run -n ${CONDA_ENV_NAME} pip wheel --no-index --no-deps --wheel-dir dist dist/tmp/$(PACKAGE_NAME)-latest.tar
	ls $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl
	# Check to make sure the tests were excluded from the wheel.
	! ( unzip -t $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -m1 tests/ )
	# Check to make sure the mlos_bench module has the config directory.
	[ "$(MODULE_NAME)" != "mlos_bench" ] || unzip -t $(MODULE_NAME)/dist/$(MODULE_NAME)-*-py3-none-any.whl | grep -m1 mlos_bench/config/
	cd $(MODULE_NAME)/dist/tmp && ln -s ../$(MODULE_NAME)-*-py3-none-any.whl $(MODULE_NAME)-latest-py3-none-any.whl
	# Check to make sure the README contents made it into the package metadata.
	unzip -p $(MODULE_NAME)/dist/tmp/$(MODULE_NAME)-latest-py3-none-any.whl */METADATA | egrep -v '^[A-Z][a-zA-Z-]+:' | grep -q -i '^# mlos'

.PHONY: dist-test-env-clean
dist-test-env-clean:
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
	$(MAKE) dist-test-env-clean
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
#dist-test: dist-clean
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
	# Run a simple test that uses the mlos_viz wheel (full tests can be checked with `make test`).
	conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_viz/mlos_viz/tests/test_dabl_plot.py
	touch $@

dist-test-clean: dist-test-env-clean
	rm -f build/dist-test-env.$(PYTHON_VERSION).build-stamp


.PHONY: publish
publish: publish-pypi

.PHONY:
publish-pypi-deps: build/publish-pypi-deps.build-stamp

build/publish-pypi-deps.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
	conda run -n ${CONDA_ENV_NAME} pip install -U twine
	touch $@

build/publish.%.py.build-stamp: build/publish-pypi-deps.${CONDA_ENV_NAME}.build-stamp build/pytest.${CONDA_ENV_NAME}.build-stamp build/dist-test.$(PYTHON_VERSION).build-stamp build/check-doc.build-stamp build/linklint-doc.build-stamp
	rm -f mlos_*/dist/*.tar.gz
	ls mlos_*/dist/*.tar | xargs -I% gzip -k %
	repo_name=`echo "$@" | sed -e 's|build/publish\.||' -e 's|\.py\.build-stamp||'` \
		&& conda run -n ${CONDA_ENV_NAME} python3 -m twine upload --repository $$repo_name \
			mlos_*/dist/mlos*-*.tar.gz mlos_*/dist/mlos*-*.whl
	touch $@

publish-pypi: build/publish.pypi.py.build-stamp
publish-test-pypi: build/publish.testpypi.py.build-stamp

build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: doc/requirements.txt
	conda run -n ${CONDA_ENV_NAME} pip install -U -r doc/requirements.txt
	touch $@

.PHONY: doc-prereqs
doc-prereqs: build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-doc-env
clean-doc-env:
	rm -f build/doc-prereqs.build-stamp
	rm -f build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp

COMMON_DOC_FILES := build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp doc/source/*.rst doc/source/_templates/*.rst doc/source/conf.py

doc/source/api/mlos_core/modules.rst: $(MLOS_CORE_PYTHON_FILES) $(COMMON_DOC_FILES)
	rm -rf doc/source/api/mlos_core
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M -o source/api/mlos_core/ ../mlos_core/ ../mlos_*/setup.py

doc/source/api/mlos_bench/modules.rst: $(MLOS_BENCH_PYTHON_FILES) $(COMMON_DOC_FILES)
	rm -rf doc/source/api/mlos_bench
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M -o source/api/mlos_bench/ ../mlos_bench/ ../mlos_*/setup.py
	# Save the help output of the mlos_bench scripts to include in the documentation.
	# First make sure that the latest version of mlos_bench is installed (since it uses git based tagging).
	conda run -n ${CONDA_ENV_NAME} pip install -e mlos_core -e mlos_bench
	conda run -n ${CONDA_ENV_NAME} mlos_bench --help > doc/source/api/mlos_bench/mlos_bench.run.usage.txt
	echo ".. literalinclude:: mlos_bench.run.usage.txt" >> doc/source/api/mlos_bench/mlos_bench.run.rst
	echo "   :language: none" >> doc/source/api/mlos_bench/mlos_bench.run.rst

doc/source/api/mlos_viz/modules.rst: $(MLOS_VIZ_PYTHON_FILES) $(COMMON_DOC_FILES)
	rm -rf doc/source/api/mlos_viz
	cd doc/ && conda run -n ${CONDA_ENV_NAME} sphinx-apidoc -f -e -M -o source/api/mlos_viz/ ../mlos_viz/ ../mlos_*/setup.py

SPHINX_API_RST_FILES := doc/source/api/mlos_core/modules.rst doc/source/api/mlos_bench/modules.rst doc/source/api/mlos_viz/modules.rst

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
	test -s doc/build/html/generated/mlos_viz.dabl.html
	test -s doc/build/html/api/mlos_core/mlos_core.html
	test -s doc/build/html/api/mlos_bench/mlos_bench.html
	test -s doc/build/html/api/mlos_viz/mlos_viz.html
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
	rm -f build/licenseheaders.${CONDA_ENV_NAME}.build-stamp
	rm -f build/licenseheaders-prereqs.${CONDA_ENV_NAME}.build-stamp

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

.PHONY: dist-clean
dist-clean:
	rm -rf build dist
	rm -rf mlos_core/build mlos_core/dist
	rm -rf mlos_bench/build mlos_bench/dist
	rm -rf mlos_viz/build mlos_viz/dist

.PHONY: clean
clean: clean-check clean-test dist-clean clean-doc clean-doc-env dist-test-clean
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
