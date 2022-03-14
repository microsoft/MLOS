CONDA_DEFAULT_ENV := mlos_core
PYTHON_FILES := $(shell find mlos_core/ -type f -name '*.py' 2>/dev/null)

.PHONY: all
all: check test dist doc

.PHONY: conda-env
conda-env: .conda-env.build-stamp

.conda-env.build-stamp: environment.yml setup.py
	conda env list -q | grep -q "^${CONDA_DEFAULT_ENV} " || conda env create -q -f environment.yml
	conda env update -q -n ${CONDA_DEFAULT_ENV} --prune -f environment.yml
	touch .conda-env.build-stamp

.PHONY: check
check: pylint

.PHONY: pylint
pylint:	conda-env .pylint.build-stamp

.pylint.build-stamp: $(PYTHON_FILES) .pylintrc
	conda run -n ${CONDA_DEFAULT_ENV} pylint -j0 mlos_core
	touch .pylint.build-stamp

.PHONY: test
test: pytest

.PHONY: pytest
pytest: conda-env .pytest.build-stamp

# FIXME: There's an issue with pytest-xdist not reaping children when
# pytest-timeout fails which we're currently using because somehow pytest is
# causing module imports to hang.
#	pytest -n auto --cov=mlos_core --cov-report=xml mlos_core/
.pytest.build-stamp: $(PYTHON_FILES) pytest.ini
	conda run -n ${CONDA_DEFAULT_ENV} pytest --cov=mlos_core --cov-report=xml mlos_core/
	touch .pytest.build-stamp

.PHONY: dist
dist: bdist_wheel

.PHONY: bdist_wheel
bdist_wheel: conda-env dist/mlos_core-*-py3-none-any.whl

dist/mlos_core-*-py3-none-any.whl: setup.py $(PYTHON_FILES)
	conda run -n ${CONDA_DEFAULT_ENV} python3 setup.py bdist_wheel

.PHONY: doc
doc:
	# TODO
	@false

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
clean: clean-check clean-test dist-clean
	rm -f .conda-dev.build-stamp
	#rm -rf mlos_core.egg-info
