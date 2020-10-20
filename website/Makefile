# A simple Makefile to help build all of the web page documentation from the
# source code and repo markdown docs.

# Make sure to check the usual pip install location for commands.
PATH := $(PATH):${HOME}/.local/bin
export PATH

.PHONY:
all: public/python_api public/index.html test

.PHONY:
.NOTPARALLEL:
test: link-check

.PHONY:
clean: clean-hugo-site clean-sphinx-site

.PHONY:
clean-hugo-site:
	rm -rf content/*.md || true
	rm -rf content/*.md.bak || true
	rm -rf content/*.txt || true
	rm -rf content/build
	rm -rf content/documentation
	rm -rf content/scripts
	rm -rf content/source
	rm -rf content/test
	rm -rf content/notebooks
	rm -rf public

.PHONY:
hugo-site: clean-hugo-site
	./build_site.sh
	find content/ -name '*.md.bak' -delete
	hugo
	@ # If the sphinx site was already built, just copy it over.
	@ # This let's us run "make hugo-site link-check" a bit more quickly.
	$(MAKE) public/python_api

public/index.html:
	$(MAKE) hugo-site

.PHONY:
clean-sphinx-site:
	rm -rf sphinx/_build
	rm -rf sphinx/api
	git restore sphinx/api/mlos.rst
	rm -rf public/python_api

# Note: this is an expensive target.
.PHONY:
sphinx-site: clean-sphinx-site
	sphinx/apidoc.sh
	$(MAKE) -C sphinx
	$(MAKE) copy-python-apis

sphinx/_build/html:
	$(MAKE) sphinx-site

.PHONY:
copy-python-apis: sphinx/_build/html
	mkdir -p public
	rm -rf public/python_api
	cp -a sphinx/_build/html public/python_api

public/python_api:
	$(MAKE) copy-python-apis

.PHONY:
.NOTPARALLEL:
link-check: public/index.html public/python_api
	./test_site_links.sh
