CONDA_ENV_NAME ?= mlos_core
PYTHON_VERSION := $(shell echo "${CONDA_ENV_NAME}" | sed -r -e 's/^mlos_core[-]?//')
ENV_YML := conda-envs/${CONDA_ENV_NAME}.yml

# Find the non-build python files we should consider as rule dependencies.
PYTHON_FILES := $(shell find ./ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./((mlos_core|mlos_bench)/)?build/' -e '^./doc/source/')
MLOS_CORE_PYTHON_FILES := $(shell find ./mlos_core/ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./mlos_core/build/')
MLOS_BENCH_PYTHON_FILES := $(shell find ./mlos_bench/ -type f -name '*.py' 2>/dev/null | egrep -v -e '^./mlos_bench/build/')

## If available, and not already set to something else, use the mamba solver to speed things up.
#CONDA_SOLVER ?= $(shell conda list -n base | grep -q '^conda-libmamba-solver\s' && echo libmamba || echo classic)
## To handle multiple versions of conda, make sure we only have one of the environment variables set.
#ifneq ($(shell conda config --show | grep '^experimental_solver:'),)
#    export CONDA_EXPERIMENTAL_SOLVER := ${CONDA_SOLVER}
#    export EXPERIMENTAL_SOLVER := ${CONDA_SOLVER}
#    undefine CONDA_SOLVER
#    unexport CONDA_SOLVER
#else
#    export CONDA_SOLVER := ${CONDA_SOLVER}
#    undefine CONDA_EXPERIMENTAL_SOLVER
#    unexport CONDA_EXPERIMENTAL_SOLVER
#    undefine EXPERIMENTAL_SOLVER
#    unexport EXPERIMENTAL_SOLVER
#endif

DOCKER := $(shell which docker)
# Make sure the build directory exists.
MKDIR_BUILD := $(shell mkdir -p build)

# Allow overriding the default verbosity of conda for CI jobs.
#CONDA_INFO_LEVEL ?= -q

# Run make in parallel by default.
MAKEFLAGS += -j$(shell nproc)

.PHONY: all
all: check test dist dist-test # doc

.PHONY: conda-env
conda-env: build/conda-env.${CONDA_ENV_NAME}.build-stamp

build/conda-env.${CONDA_ENV_NAME}.build-stamp: ${ENV_YML} mlos_core/setup.py mlos_bench/setup.py
	@echo "CONDA_SOLVER: ${CONDA_SOLVER}"
	@echo "CONDA_EXPERIMENTAL_SOLVER: ${CONDA_EXPERIMENTAL_SOLVER}"
	@echo "CONDA_INFO_LEVEL: ${CONDA_INFO_LEVEL}"
	conda env list -q | grep -q "^${CONDA_ENV_NAME} " || conda env create ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} -f ${ENV_YML}
	conda env update ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME} --prune -f ${ENV_YML}
	$(MAKE) clean-check clean-test clean-doc
	touch build/conda-env.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-conda-env
clean-conda-env:
	conda env remove -y ${CONDA_INFO_LEVEL} -n ${CONDA_ENV_NAME}
	rm -f build/conda-env.${CONDA_ENV_NAME}.build-stamp

.PHONY: check
check: pycodestyle pydocstyle pylint # cspell

.PHONY: pycodestyle
pycodestyle: conda-env build/pycodestyle.${CONDA_ENV_NAME}.build-stamp

build/pycodestyle.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pycodestyle.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES) setup.cfg
	# Check for decent pep8 code style with pycodestyle.
	# Note: if this fails, try using autopep8 to fix it.
	conda run -n ${CONDA_ENV_NAME} pycodestyle $(PYTHON_FILES)
	touch build/pycodestyle.${CONDA_ENV_NAME}.build-stamp

.PHONY: pydocstyle
pydocstyle: conda-env build/pydocstyle.${CONDA_ENV_NAME}.build-stamp

build/pydocstyle.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pydocstyle.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES) setup.cfg
	# Check for decent pep8 doc style with pydocstyle.
	conda run -n ${CONDA_ENV_NAME} pydocstyle $(PYTHON_FILES)
	touch build/pydocstyle.${CONDA_ENV_NAME}.build-stamp

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
	touch build/cspell-container.build-stamp

.PHONY: pylint
pylint: conda-env build/pylint.${CONDA_ENV_NAME}.build-stamp

build/pylint.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pylint.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES) .pylintrc
	conda run -n ${CONDA_ENV_NAME} pylint -j0 $(PYTHON_FILES)
	touch build/pylint.${CONDA_ENV_NAME}.build-stamp

.PHONY: test
test: pytest

.PHONY: pytest
pytest: conda-env build/pytest.${CONDA_ENV_NAME}.build-stamp

build/pytest.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/pytest.${CONDA_ENV_NAME}.build-stamp: $(PYTHON_FILES) pytest.ini
	#conda run -n ${CONDA_ENV_NAME} pytest -n auto --cov=mlos_core --cov-report=xml mlos_core/ mlos_bench/
	conda run -n ${CONDA_ENV_NAME} pytest --cov --cov-report=xml mlos_core/ mlos_bench/ --junitxml=junit/test-results.xml
	touch build/pytest.${CONDA_ENV_NAME}.build-stamp

.PHONY: dist
dist: bdist_wheel

.PHONY: bdist_wheel
bdist_wheel: conda-env mlos_core/dist/mlos_core-*-py3-none-any.whl mlos_bench/dist/mlos_bench-*-py3-none-any.whl

mlos_core/dist/mlos_core-*-py3-none-any.whl: build/conda-env.${CONDA_ENV_NAME}.build-stamp
mlos_core/dist/mlos_core-*-py3-none-any.whl: mlos_core/setup.py $(MLOS_CORE_PYTHON_FILES)
	rm -f mlos_core/dist/mlos_core-*-py3-none-any.whl \
	    && cd mlos_core/ \
	    && conda run -n ${CONDA_ENV_NAME} python3 setup.py bdist_wheel \
	    && cd .. \
	    && ls mlos_core/dist/mlos_core-*-py3-none-any.whl

mlos_bench/dist/mlos_bench-*-py3-none-any.whl: build/conda-env.${CONDA_ENV_NAME}.build-stamp
mlos_bench/dist/mlos_bench-*-py3-none-any.whl: mlos_bench/setup.py $(MLOS_BENCH_PYTHON_FILES)
	rm -f mlos_bench/dist/mlos_bench-*-py3-none-any.whl \
	    && cd mlos_bench/ \
	    && conda run -n ${CONDA_ENV_NAME} python3 setup.py bdist_wheel \
	    && cd .. \
	    && ls mlos_bench/dist/mlos_bench-*-py3-none-any.whl

.PHONY: dist-test-env-clean
dist-test-env-clean:
	# Remove any existing mlos-dist-test environment so we can start clean.
	conda env remove -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) 2>/dev/null || true
	rm -f build/dist-test-env.$(PYTHON_VERSION).build-stamp

.PHONY: dist-test-env
dist-test-env: dist build/dist-test-env.$(PYTHON_VERSION).build-stamp

build/dist-test-env.$(PYTHON_VERSION).build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
# Use the same version of python as the one we used to build the wheels.
build/dist-test-env.$(PYTHON_VERSION).build-stamp: PYTHON_VERS_REQ=$(shell conda list -n ${CONDA_ENV_NAME} | egrep '^python\s+' | sed -r -e 's/^python\s+//' | cut -d' ' -f1)
build/dist-test-env.$(PYTHON_VERSION).build-stamp: mlos_core/dist/mlos_core-*-py3-none-any.whl mlos_bench/dist/mlos_bench-*-py3-none-any.whl
	# Check to make sure we only have a single wheel version availble.
	# Else, run `make dist-clean` to remove prior versions.
	ls mlos_core/dist/mlos_core-*-py3-none-any.whl | wc -l | grep -q -x 1
	ls mlos_bench/dist/mlos_bench-*-py3-none-any.whl | wc -l | grep -q -x 1
	# Symlink them to make the install step easier.
	rm -rf mlos_core/dist/tmp && mkdir -p mlos_core/dist/tmp
	cd mlos_core/dist/tmp && ln -s ../mlos_core-*-py3-none-any.whl mlos_core-latest-py3-none-any.whl
	rm -rf mlos_bench/dist/tmp && mkdir -p mlos_bench/dist/tmp
	cd mlos_bench/dist/tmp && ln -s ../mlos_bench-*-py3-none-any.whl mlos_bench-latest-py3-none-any.whl
	# Create a clean test environment for checking the wheel files.
	$(MAKE) dist-test-env-clean
	conda create -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) python=$(PYTHON_VERS_REQ)
	conda install -y ${CONDA_INFO_LEVEL} -n mlos-dist-test-$(PYTHON_VERSION) pytest pytest-timeout pytest-forked pytest-xdist
	# Test a clean install of the mlos_core wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "mlos_core/dist/tmp/mlos_core-latest-py3-none-any.whl[full]"
	# Test a clean install of the mlos_bench wheel.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip install "mlos_bench/dist/tmp/mlos_bench-latest-py3-none-any.whl[full]"
	touch build/dist-test-env.$(PYTHON_VERSION).build-stamp

.PHONY: dist-test
#dist-test: dist-clean
dist-test: dist-test-env build/dist-test.$(PYTHON_VERSION).build-stamp

# Unnecessary if we invoke it as "python3 -m pytest ..."
build/dist-test.$(PYTHON_VERSION).build-stamp: $(PYTHON_FILES) build/dist-test-env.$(PYTHON_VERSION).build-stamp
	# Make sure we're using the packages from the wheel.
	# Note: this will pick up the local directory and change the output if we're using PYTHONPATH=.
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip list --verbose | grep mlos-core | grep ' pip'
	conda run -n mlos-dist-test-$(PYTHON_VERSION) pip list --verbose | grep mlos-bench | grep ' pip'
	# Run a simple test that uses the mlos_core wheel (full tests can be checked with `make test`).
	conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_core/mlos_core/spaces/tests/spaces_test.py
	# Run a simple test that uses the mlos_bench wheel (full tests can be checked with `make test`).
	conda run -n mlos-dist-test-$(PYTHON_VERSION) python3 -m pytest mlos_bench/mlos_bench/environment/azure/tests/azure_services_test.py
	touch build/dist-test.$(PYTHON_VERSION).build-stamp

dist-test-clean: dist-test-env-clean
	rm -f build/dist-test-env.$(PYTHON_VERSION).build-stamp

build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: build/conda-env.${CONDA_ENV_NAME}.build-stamp
build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp: doc/requirements.txt
	conda run -n ${CONDA_ENV_NAME} pip install -U -r doc/requirements.txt
	touch build/doc-prereqs.${CONDA_ENV_NAME}.build-stamp

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
	conda run -n ${CONDA_ENV_NAME} mlos_bench/mlos_bench/run_opt.py --help > doc/source/api/mlos_bench/mlos_bench.run_opt.usage.txt
	echo ".. literalinclude:: mlos_bench.run_opt.usage.txt" >> doc/source/api/mlos_bench/mlos_bench.run_opt.rst
	echo "   :language: none" >> doc/source/api/mlos_bench/mlos_bench.run_opt.rst
	conda run -n ${CONDA_ENV_NAME} mlos_bench/mlos_bench/run_bench.py --help > doc/source/api/mlos_bench/mlos_bench.run_bench.usage.txt
	echo ".. literalinclude:: mlos_bench.run_bench.usage.txt" >> doc/source/api/mlos_bench/mlos_bench.run_bench.rst
	echo "   :language: none" >> doc/source/api/mlos_bench/mlos_bench.run_bench.rst

SPHINX_API_RST_FILES := doc/source/api/mlos_core/modules.rst doc/source/api/mlos_bench/modules.rst

.PHONY: sphinx-apidoc
sphinx-apidoc: $(SPHINX_API_RST_FILES)

doc/build/html/index.html: $(SPHINX_API_RST_FILES) doc/Makefile
	@rm -rf doc/build
	@mkdir -p doc/build
	@rm -f doc/build/log.txt
	# Build the rst files into html.
	conda run -n ${CONDA_ENV_NAME} $(MAKE) -C doc/ $(MAKEFLAGS) html \
		>> doc/build/log.txt 2>&1 \
		|| { cat doc/build/log.txt; exit 1; }
	# DONE: Add some output filtering for this so we can more easily see what went wrong.
	# (e.g. skip complaints about missing .examples files)
	# See check-doc

.PHONY: doc
doc: doc/build/html/staticwebapp.config.json build/check-doc.build-stamp build/linklint-doc.build-stamp

doc/build/html/staticwebapp.config.json: doc/build/html/index.html doc/staticwebapp.config.json
	# Copy the azure static web app config file to the doc build directory.
	cp doc/staticwebapp.config.json doc/build/html/

.PHONY: check-doc
check-doc: build/check-doc.build-stamp

build/check-doc.build-stamp: doc/build/html/index.html
	# Check for a few files to make sure the docs got generated in a way we want.
	test -s doc/build/html/index.html
	test -s doc/build/html/generated/mlos_core.optimizers.optimizer.BaseOptimizer.html
	test -s doc/build/html/generated/mlos_bench.environment.Environment.html
	test -s doc/build/html/api/mlos_core/mlos_core.html
	test -s doc/build/html/api/mlos_bench/mlos_bench.html
	grep -q options: doc/build/html/api/mlos_bench/mlos_bench.run_opt.html
	grep -q options: doc/build/html/api/mlos_bench/mlos_bench.run_bench.html
	# Check doc logs for errors (but skip over some known ones) ...
	@cat doc/build/log.txt \
		| egrep -C1 -e WARNING -e CRITICAL -e ERROR \
		| egrep -v \
			-e "No such file or directory: '.*.examples'.$$" \
			-e 'Problems with "include" directive path:' \
			-e 'duplicate object description' \
			-e "document isn't included in any toctree" \
			-e "toctree contains reference to nonexisting document 'auto_examples/index'" \
			-e "failed to import function 'create' from module '(SpaceAdapter|Optimizer)Factory'" \
			-e "No module named '(SpaceAdapter|Optimizer)Factory'" \
			-e '^make.*resetting jobserver mode' \
		| grep -v '^\s*$$' \
		| if grep .; then echo "Errors found in doc build. Check doc/build/log.txt for details."; exit 1; else exit 0; fi
	touch build/check-doc.build-stamp

.PHONY: linklint-doc
ifeq ($(DOCKER),)
linklint-doc:
	@echo "NOTE: linklint-doc target requires docker."
else
linklint-doc: build/linklint-doc.build-stamp
endif

build/linklint-doc.build-stamp: doc/build/html/index.html build/check-doc.build-stamp
	@echo "Starting nginx docker container for serving docs."
	./doc/nginx-docker.sh restart
	docker exec mlos-doc-nginx curl -sSf http://localhost/index.html >/dev/null
	@echo "Running linklint on the docs."
	docker exec mlos-doc-nginx linklint -net -redirect -root /doc/build/html/ /@ -error -warn > doc/build/linklint.out 2>&1
	@if cat doc/build/linklint.out | grep -e ^ERROR -e ^WARN | grep -v 'missing named anchors' | grep -q .; then \
		echo "Found errors in the documentation:"; cat doc/build/linklint.out; exit 1; \
	fi
	@echo "OK"
	touch build/linklint-doc.build-stamp

.PHONY: clean-doc
clean-doc:
	rm -rf doc/build/ doc/global/ doc/source/api/ doc/source/generated

.PHONY: clean-check
clean-check:
	rm -f build/pylint.build-stamp
	rm -f build/pylint.${CONDA_ENV_NAME}.build-stamp
	rm -f build/pycodestyle.build-stamp
	rm -f build/pycodestyle.${CONDA_ENV_NAME}.build-stamp

.PHONY: clean-test
clean-test:
	rm -f build/pytest.build-stamp
	rm -f build/pytest.${CONDA_ENV_NAME}.build-stamp
	rm -rf .pytest_cache/
	rm -f coverage.xml .coverage*
	rm -rf junit/test-results.xml

.PHONY: dist-clean
dist-clean:
	rm -rf build dist
	rm -rf mlos_core/build mlos_core/dist
	rm -rf mlos_bench/build mlos_bench/dist

.PHONY: clean
clean: clean-check clean-test dist-clean clean-doc clean-doc-env dist-test-clean
	rm -f .*.build-stamp
	rm -f build/conda-env.build-stamp build/conda-env.*.build-stamp
	rm -rf mlos_core.egg-info
	rm -rf mlos_core/mlos_core.egg-info
	rm -rf mlos_bench.egg-info
	rm -rf mlos_bench/mlos_bench.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -print0 | xargs -t -r -0 rm -rf
	find . -type f -name '*.pyc' -print0 | xargs -t -r -0 rm -f

.PHONY: devcontainer
devcontainer:
	./.devcontainer/build/build-devcontainer.sh
	@echo
	@echo "Run ./.devcontainer/scripts/run-devcontainer.sh to start the newly build devcontainer."
