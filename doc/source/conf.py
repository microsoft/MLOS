#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import sys

from logging import warning

import sphinx_rtd_theme


sys.path.insert(0, os.path.abspath('../../mlos_core/mlos_core'))
sys.path.insert(1, os.path.abspath('../../mlos_bench/mlos_bench'))
sys.path.insert(1, os.path.abspath('../../mlos_viz/mlos_viz'))


# -- Project information -----------------------------------------------------

project = 'MLOS'
copyright = '2024, Microsoft GSL'
author = 'Microsoft GSL'

# The full version, including alpha/beta/rc tags
try:
    from version import VERSION
except ImportError:
    VERSION = '0.0.1-dev'
    warning(f"version.py not found, using dummy VERSION={VERSION}")

try:
    from setuptools_scm import get_version
    version = get_version(root='../..', relative_to=__file__, fallback_version=VERSION)
    if version is not None:
        VERSION = version
except ImportError:
    warning("setuptools_scm not found, using VERSION {VERSION}")
except LookupError as e:
    warning(f"setuptools_scm failed to find git version, using VERSION {VERSION}: {e}")
release = VERSION


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'nbsphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    # 'sphinx.ext.intersphinx',
    # 'sphinx.ext.linkcode',
    'numpydoc',
    'matplotlib.sphinxext.plot_directive',
    'myst_parser',
]

source_suffix = {
    '.rst': 'restructuredtext',
    # '.txt': 'markdown',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# generate autosummary even if no references
autosummary_generate = True
# but don't complain about missing stub files
# See Also: <https://stackoverflow.com/a/73294408>
numpydoc_class_members_toctree = False

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    # Don't generate documentation for some (non-private) functions that are more for internal implementation use.
    'exclude-members': 'mlos_bench.util.check_required_params'
}

# Generate the plots for the gallery
# plot_gallery = True

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', '_templates']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- nbsphinx options for rendering notebooks -------------------------------
# nbsphinx_execute = 'never'   # enable to stop nbsphinx from executing notebooks
nbsphinx_kernel_name = 'python3'
# Exclude build directory and Jupyter backup files:
exclude_patterns = ['_build', '**.ipynb_checkpoints']
