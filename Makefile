CONDA_DEFAULT_ENV := mlos_core

ENV_YML := conda-envs/${CONDA_DEFAULT_ENV}.yml
PYTHON_FILES := $(shell find mlos_core/ -type f -name '*.py' 2>/dev/null)

.PHONY: all
all: check test dist # doc

.PHONY: conda-env
conda-env: .conda-env.${CONDA_DEFAULT_ENV}.build-stamp

.conda-env.${CONDA_DEFAULT_ENV}.build-stamp: ${ENV_YML} setup.py
	conda env list -q | grep -q "^${CONDA_DEFAULT_ENV} " || conda env create -q -n ${CONDA_DEFAULT_ENV} -f ${ENV_YML}
	conda env update -q -n ${CONDA_DEFAULT_ENV} --prune -f ${ENV_YML}
	$(MAKE) clean-check clean-test clean-doc
	touch .conda-env.${CONDA_DEFAULT_ENV}.build-stamp

.PHONY: check
check: pylint

.PHONY: pylint
pylint: conda-env .pylint.build-stamp

.pylint.build-stamp: $(PYTHON_FILES) .pylintrc
	conda run -n ${CONDA_DEFAULT_ENV} pylint -j0 mlos_core mlos_bench
	touch .pylint.build-stamp

.PHONY: test
test: pytest

.PHONY: pytest
pytest: conda-env .pytest.build-stamp

.pytest.build-stamp: $(PYTHON_FILES) pytest.ini
	#conda run -n ${CONDA_DEFAULT_ENV} pytest -n auto --cov=mlos_core --cov-report=xml mlos_core/ mlos_bench/
	conda run -n ${CONDA_DEFAULT_ENV} pytest --cov --cov-report=xml mlos_core/ mlos_bench/ --junitxml=junit/test-results.xml
	touch .pytest.build-stamp

.PHONY: dist
dist: bdist_wheel

.PHONY: bdist_wheel
bdist_wheel: conda-env dist/mlos_core-*-py3-none-any.whl dist/mlos_bench-*-py3-none-any.whl

dist/mlos_bench-*-py3-none-any.whl dist/mlos_core-*-py3-none-any.whl: setup.py $(PYTHON_FILES)
	conda run -n ${CONDA_DEFAULT_ENV} python3 setup.py bdist_wheel

.doc-prereqs.build-stamp: doc/requirements.txt
	conda run -n ${CONDA_DEFAULT_ENV} pip install -r doc/requirements.txt
	touch .doc-prereqs.build-stamp

.PHONY: doc-prereqs
doc-prereqs: .doc-prereqs.build-stamp

.PHONY: doc
doc: conda-env doc-prereqs
	rm -f doc/build/html/index.html
	cd doc/ && conda run -n ${CONDA_DEFAULT_ENV} sphinx-apidoc -f -e -M -o source/api .. ../setup.py ../pytest_configure.py
	conda run -n ${CONDA_DEFAULT_ENV} make -j -C doc/ html
	test -s doc/build/html/index.html
	cp doc/staticwebapp.config.json doc/build/html/

.PHONY: clean-doc
clean-doc:
	rm -f .doc-prereqs.build-stamp
	rm -rf doc/build/ doc/global/

.PHONY: clean-check
clean-check:
	rm -f .pylint.build-stamp

.PHONY: clean-test
clean-test:
	rm -f .pytest.build-stamp

.PHONY: dist-clean
dist-clean:
	rm -rf build dist

.PHONY: clean
clean: clean-check clean-test dist-clean clean-doc
	rm -f .conda-env.build-stamp .conda-env.*.build-stamp
	rm -rf mlos_core.egg-info
	rm -rf mlos_bench.egg-info
