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

import json
import os
import sys
from typing import Dict

from logging import warning

from intersphinx_registry import get_intersphinx_mapping


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
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "matplotlib.sphinxext.plot_directive",
    "myst_parser",
]
autodoc_typehints = "both"  # signature and description

napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_keyword = True
napoleon_custom_sections = None

_base_path = os.path.abspath(os.path.join(__file__, "../../.."))
_path_cache: Dict[str, bool] = {}


def _check_path(path: str) -> bool:
    """Check if a path exists and cache the result."""
    path = os.path.join(_base_path, path)
    if path in _path_cache:
        result = _path_cache[path]
    else:
        result = os.path.exists(path)
        _path_cache[path] = result
    return result


def linkcode_resolve(domain: str, info: Dict[str, str]):
    """linkcode extension override to link to the source code on GitHub."""
    if domain != "py":
        return None
    if not info["module"]:
        return None
    if not info["module"].startswith("mlos_"):
        return None
    package = info["module"].split(".")[0]
    filename = info["module"].replace(".", "/")
    path = f"{package}/{filename}.py"
    if not _check_path(path):
        path = f"{package}/{filename}/__init__.py"
        if not _check_path(path):
            warning(f"linkcode_resolve failed to find {path}")
            warning(f"linkcode_resolve info: {json.dumps(info, indent=2)}")
    return f"https://github.com/microsoft/MLOS/tree/main/{path}"


# Add mappings to link to external documentation.
intersphinx_mapping = get_intersphinx_mapping(
    packages={
        "asyncssh",
        "azure-core",
        "azure-identity",
        "configspace",
        "matplotlib",
        "numpy",
        "pandas",
        "python",
        "referencing",
        "smac",
        "typing_extensions",
    }
)
intersphinx_mapping.update(
    {
        # "ConfigSpace": ("https://automl.github.io/ConfigSpace/latest/", None),
    }
)

# We recommend adding the following config value.
# Sphinx defaults to automatically resolve *unresolved* labels using all your Intersphinx mappings.
# This behavior has unintended side-effects, namely that documentations local references can
# suddenly resolve to an external location.
# See also:
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#confval-intersphinx_disabled_reftypes
# intersphinx_disabled_reftypes = ["*"]

# Ignore some cross references to external things we can't intersphinx with.
# sphinx has a hard time finding typealiases and typevars instead of classes.
# See Also: https://github.com/sphinx-doc/sphinx/issues/10974
nitpick_ignore = [
    # Internal typevars and aliases:
    ("py:class", "BaseTypeVar"),
    ("py:class", "ConcreteOptimizer"),
    ("py:class", "ConcreteSpaceAdapter"),
    ("py:class", "DistributionName"),
    ("py:class", "EnvironType"),
    ("py:class", "FlamlDomain"),
    ("py:class", "mlos_core.spaces.converters.flaml.FlamlDomain"),
    ("py:class", "TunableValue"),
    ("py:class", "mlos_bench.tunables.tunable.TunableValue"),
    ("py:class", "TunableValueType"),
    ("py:class", "TunableValueTypeName"),
    ("py:class", "T_co"),
    # Literals in base_storage.py
    ("py:class", "min"),
    ("py:class", "max"),
    # Literal in context handlers signatures.
    ("py:class", "False"),
    # External typevars and aliases:
    ("py:class", "CoroReturnType"),
    ("py:class", "FutureReturnType"),
    ("py:class", "typing.Literal"),
    ("py:class", "typing_extensions.Literal"),
    ("py:class", "numpy.typing.NDArray"),
    # External classes that refuse to resolve:
    ("py:class", "contextlib.nullcontext"),
    ("py:class", "sqlalchemy.engine.Engine"),
    ("py:exc", "jsonschema.exceptions.SchemaError"),
    ("py:exc", "jsonschema.exceptions.ValidationError"),
]
nitpick_ignore_regex = [
    # Ignore some external references that don't use sphinx for their docs.
    (r"py:.*", r"flaml\..*"),
]

# Which documents to include in the build.
source_suffix = {
    ".rst": "restructuredtext",
    # '.txt': 'markdown',
    ".md": "markdown",
}

# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

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

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- nbsphinx options for rendering notebooks -------------------------------
# nbsphinx_execute = 'never'   # enable to stop nbsphinx from executing notebooks
nbsphinx_kernel_name = "python3"
# Exclude build directory and Jupyter backup files:
exclude_patterns = ["_build", "**.ipynb_checkpoints"]
