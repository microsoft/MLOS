# A simple Makefile to help build all of the

.PHONY: all
all: hugo-site sphinx-site

.PHONY: hugo-site
hugo-site:
	rm -rf content/*.md || true
	rm -rf content/*.txt || true
	rm -rf content/documentation
	rm -rf content/notebooks
	./build_site.sh
	rm -rf public
	hugo

.PHONY: sphinx-site
sphinx-site:
	rm -rf python_api
	sphinx/apidoc.sh
	$(MAKE) -C sphinx
	cp -a sphinx/_build/html python_api
