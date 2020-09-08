# A simple Makefile to help build all of the web page documentation from the
# source code and repo markdown docs.

.PHONY:
all: hugo-site sphinx-site test

.PHONY:
.NOTPARALLEL:
test: link-check

.PHONY:
clean-hugo-site:
	rm -rf content/*.md || true
	rm -rf content/*.txt || true
	rm -rf content/documentation
	rm -rf content/notebooks
	rm -rf public

.PHONY:
hugo-site: clean-hugo-site
	./build_site.sh
	hugo

.PHONY:
clean-sphinx-site:
	rm -rf python_api
	rm -rf sphinx/_build
	rm -rf sphinx/api

.PHONY:
sphinx-site: clean-sphinx-site
	sphinx/apidoc.sh
	$(MAKE) -C sphinx
	cp -a sphinx/_build/html public/python_api

.PHONY:
.NOTPARALLEL:
link-check:
	./test_site_links.sh
