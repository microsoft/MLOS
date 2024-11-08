#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Sphinx configuration for MLOS documentation."""
# pylint: disable=invalid-name

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

import sphinx_rtd_theme  # pylint: disable=unused-import


sys.path.insert(0, os.path.abspath("../../mlos_core/mlos_core"))
sys.path.insert(1, os.path.abspath("../../mlos_bench/mlos_bench"))
sys.path.insert(1, os.path.abspath("../../mlos_viz/mlos_viz"))


# -- Project information -----------------------------------------------------

project = "MLOS"
copyright = "2024, Microsoft GSL"  # pylint: disable=redefined-builtin
author = "Microsoft GSL"

# The full version, including alpha/beta/rc tags
try:
    from version import VERSION
except ImportError:
    VERSION = "0.0.1-dev"
    warning(f"version.py not found, using dummy VERSION={VERSION}")

try:
    from setuptools_scm import get_version

    version = get_version(root="../..", relative_to=__file__, fallback_version=VERSION)
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
    "sphinx.ext.autodoc",
    "autoapi.extension",
    "nbsphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    # 'sphinx.ext.linkcode',
    "numpydoc",
    "matplotlib.sphinxext.plot_directive",
    "myst_parser",
]
autodoc_typehints = "both"

# Add mappings to link to external documentation.
intersphinx_mapping = {  # pylint: disable=consider-using-namedtuple-or-dataclass
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/reference/", None),
}

# Ignore some cross references to external things we can't intersphinx with.
nitpick_ignore = [
    # FIXME: sphinx has a hard time finding typealiases instead of classes.
    ("py:class", "ConcreteOptimizer"),
    ("py:class", "ConcreteSpaceAdapater"),
    ("py:class", "mlos_core.spaces.converters.flaml.FlamlDomain"),
]
nitpick_ignore_regex = [
    (r"py:.*", r"ConfigSpace\..*"),
    (r"py:.*", r"flaml\..*"),
    (r"py:.*", r"smac\..*"),
]

source_suffix = {
    ".rst": "restructuredtext",
    # '.txt': 'markdown',
    ".md": "markdown",
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Generate the plots for the gallery
# plot_gallery = True

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "_templates"]

autoapi_dirs = [
    # Don't index setup.py or other utility scripts.
    "../../mlos_core/mlos_core/",
    "../../mlos_bench/mlos_bench/",
    "../../mlos_viz/mlos_viz/",
]
autoapi_ignore = [
    "*/tests/*",
    # Don't document internal environment scripts that aren't part of a module.
    "*/mlos_bench/config/environments/*/*.py",
    "*/mlos_bench/config/services/*/*.py",
]
autoapi_options = [
    "members",
    # Can't document externally inherited members due to broken references.
    # "inherited-members",
    "undoc-members",
    # Don't document private members.
    # "private-members",
    "show-inheritance",
    # Causes issues when base class is a typing protocol.
    # "show-inheritance-diagram",
    "show-module-summary",
    "special-members",
    # Causes duplicate reference issues. For instance:
    # - mlos_bench.environments.LocalEnv
    # - mlos_bench.environments.local.LocalEnv
    # - mlos_bench.environments.local.local_env.LocalEnv
    # "imported-members",
]
autoapi_add_toctree_entry = False
autoapi_keep_files = True  # for testing

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- nbsphinx options for rendering notebooks -------------------------------
# nbsphinx_execute = 'never'   # enable to stop nbsphinx from executing notebooks
nbsphinx_kernel_name = "python3"
# Exclude build directory and Jupyter backup files:
exclude_patterns = ["_build", "**.ipynb_checkpoints"]
