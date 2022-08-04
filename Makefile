CONDA_DEFAULT_ENV := mlos_core

ENV_YML := conda-envs/${CONDA_DEFAULT_ENV}.yml
MLOS_CORE_PYTHON_FILES := $(shell find mlos_core/ -type f -name '*.py' 2>/dev/null)
MLOS_BENCH_PYTHON_FILES := $(shell find mlos_bench/ -type f -name '*.py' 2>/dev/null)

.PHONY: all
all: check test dist # doc

.PHONY: conda-env
conda-env: .conda-env.${CONDA_DEFAULT_ENV}.build-stamp

.conda-env.${CONDA_DEFAULT_ENV}.build-stamp: ${ENV_YML} mlos_core/setup.py mlos_bench/setup.py
	conda env list -q | grep -q "^${CONDA_DEFAULT_ENV} " || conda env create -q -n ${CONDA_DEFAULT_ENV} -f ${ENV_YML}
	conda env update -q -n ${CONDA_DEFAULT_ENV} --prune -f ${ENV_YML}
	$(MAKE) clean-check clean-test clean-doc
	touch .conda-env.${CONDA_DEFAULT_ENV}.build-stamp

.PHONY: check
check: pylint

.PHONY: pylint
pylint: conda-env .pylint.build-stamp

.pylint.build-stamp: $(PYTHON_FILES) .pylintrc
	conda run -n ${CONDA_DEFAULT_ENV} pylint -j0 mlos_core/mlos_core mlos_bench/mlos_bench
	touch .pylint.build-stamp

.PHONY: test
test: pytest

.PHONY: pytest
pytest: conda-env .pytest.build-stamp

.pytest.build-stamp: export PYTHONPATH := $(PWD):$(PYTHONPATH)
.pytest.build-stamp: $(PYTHON_FILES) pytest.ini
	#conda run -n ${CONDA_DEFAULT_ENV} pytest -n auto --cov=mlos_core --cov-report=xml mlos_core/ mlos_bench/
	conda run -n ${CONDA_DEFAULT_ENV} pytest --cov --cov-report=xml mlos_core/ mlos_bench/ --junitxml=junit/test-results.xml
	touch .pytest.build-stamp

.PHONY: dist
dist: bdist_wheel

.PHONY: bdist_wheel
bdist_wheel: conda-env dist/mlos_core-*-py3-none-any.whl dist/mlos_bench-*-py3-none-any.whl

dist/mlos_core-*-py3-none-any.whl: mlos_core/setup.py $(MLOS_CORE_PYTHON_FILES)
	conda run -n ${CONDA_DEFAULT_ENV} python3 mlos_core/setup.py bdist_wheel

dist/mlos_bench-*-py3-none-any.whl: mlos_bench/setup.py $(MLOS_BENCH_PYTHON_FILES)
	conda run -n ${CONDA_DEFAULT_ENV} python3 mlos_bench/setup.py bdist_wheel

.doc-prereqs.build-stamp: doc/requirements.txt
	conda run -n ${CONDA_DEFAULT_ENV} pip install -r doc/requirements.txt
	touch .doc-prereqs.build-stamp

.PHONY: doc-prereqs
doc-prereqs: .doc-prereqs.build-stamp

.PHONY: clean-doc-env
clean-doc-env:
	rm -f .doc-prereqs.build-stamp

.PHONY: doc
doc: conda-env doc-prereqs clean-doc
	cd doc/ && conda run -n ${CONDA_DEFAULT_ENV} sphinx-apidoc -f -e -M -o source/api/mlos_core/ ../mlos_core/ ../mlos_*/setup.py ../pytest_configure.py
	cd doc/ && conda run -n ${CONDA_DEFAULT_ENV} sphinx-apidoc -f -e -M -o source/api/mlos_bench/ ../mlos_bench/ ../mlos_*/setup.py ../pytest_configure.py
	conda run -n ${CONDA_DEFAULT_ENV} make -j -C doc/ html
	test -s doc/build/html/index.html
	test -s doc/build/html/generated/mlos_core.optimizers.BaseOptimizer.html
	test -s doc/build/html/generated/mlos_bench.main.optimize.html
	test -s doc/build/html/api/mlos_core/mlos_core.html
	test -s doc/build/html/api/mlos_bench/mlos_bench.html
	cp doc/staticwebapp.config.json doc/build/html/

.PHONY: clean-doc
clean-doc:
	rm -rf doc/build/ doc/global/ doc/source/api/ doc/source/generated

.PHONY: clean-check
clean-check:
	rm -f .pylint.build-stamp

.PHONY: clean-test
clean-test:
	rm -f .pytest.build-stamp
	rm -rf .pytest_cache/
	rm -f coverage.xml .coverage
	rm -rf junit/test-results.xml

.PHONY: dist-clean
dist-clean:
	rm -rf build dist

.PHONY: clean
clean: clean-check clean-test dist-clean clean-doc clean-doc-env
	rm -f .conda-env.build-stamp .conda-env.*.build-stamp
	rm -rf mlos_core.egg-info
	rm -rf mlos_core/mlos_core.egg-info
	rm -rf mlos_bench.egg-info
	rm -rf mlos_bench/mlos_bench.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -print0 | xargs -t -r -0 rm -rf
	find . -type f -name '*.pyc' -print0 | xargs -t -r -0 rm -f
