# Documentation Website Generation Documentation

This document has some brief notes about how we turn our in-repo Markdown and in-code documentation into flat html files for hosting via Github Pages.

## Tools

We use [`nbconvert`](https://nbconvert.readthedocs.io/en/latest/) to render the notebooks in [`source/Mlos.Notebooks/`](../source/Mlos.Notebooks/) to markdown.

We use [`hugo`](https://gohugo.io/) to convert the markdown files to html.

We use [`sphinx`](https://www.sphinx-doc.org/en/master/) to generate html documentation from the Python source code comments.

## Layout

Most `.md` files in the repository are copied into the `content/` directory that `hugo` expects, preserving their relative paths to one another.

These are then converted into flat html in the `public/` directory here, which is eventually published to the [`gh-pages`](https://github.com/microsoft/MLOS/tree/gh-pages) branch using a [CI pipeline](../.github/workflows/main.yml) [action](https://github.com/marketplace/actions/deploy-to-github-pages).
The are served from there at <https://microsoft.github.io/MLOS>.

## Link Conversion

By convention we use relative links (e.g. [`../README.md`](../README.md)) within our Markdown so that documentation is browseable when viewed from <https://github.com/microsoft/MLOS>.

However, we need to convert those links using some `sed` rules when publishing to Github Pages so that they still resolve correctly there.

Additionally, some links we want to return back to the repository itself.
For those cases, we add a fake `#mlos-github-tree-view` anchor to the relative Markdown link and use additional `sed` rules to rewrite the URL when creating the hugo `content/` directory.

## Commands

Most of this is managed through a [`Makefile`](./Makefile) in this directory and some shell scripts:

- [`build_site.sh`](./build_site.sh)
  - gets the necessary `pip` requirements and renders the notebooks to Markdown
  - places the repo `.md` files into the `content` directory that `hugo` expects while maintaining their relative hierarchy
    - to do this it also treats `README.md` as "index" files
  - fixes up the links in the in-repo markdown so that they navigate correctly when published as html
- [`sphinx/apidoc.sh`](./sphinx/apidoc.sh)
  - prepares for using `sphinx` to generate documentation for the Python APIs from the code comments in [`source/Mlos.Python/`](../source/Mlos.Python/)
- [`test_site_links.sh`](./test_site_links.sh)
  - temporarily starts a local `nginx` webserver for checking the links generated from those scripts for validity using [`linklint`](http://www.linklint.org/)
  > Note: it does not check the `#anchors` currently.

  A separate [CI pipeline](../.github/workflows/main.yml) [action](https://github.com/marketplace/actions/markdown-link-check) checks the in-repo `.md` files for link validation.

To test locally, simply run `make` within the `website/` directory.
