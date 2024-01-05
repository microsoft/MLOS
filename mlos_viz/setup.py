#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_viz package.
"""

from logging import warning
from itertools import chain
from typing import Dict, List

from setuptools import setup, find_packages

from _version import _VERSION    # pylint: disable=import-private-name

try:
    from setuptools_scm import get_version
    version = get_version(root='..', relative_to=__file__)
    if version is not None:
        _VERSION = version  # noqa: F811
except ImportError:
    warning("setuptools_scm not found, using version from _version.py")
except LookupError as e:
    warning(f"setuptools_scm failed to find git version, using version from _version.py: {e}")


extra_requires: Dict[str, List[str]] = {}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(*extra_requires.values())))

# pylint: disable=duplicate-code
MODULE_BASE_NAME = 'mlos_viz'
setup(
    name='mlos-viz',
    version=_VERSION,
    packages=find_packages(exclude=[f"{MODULE_BASE_NAME}.tests", f"{MODULE_BASE_NAME}.tests.*"]),
    package_data={
        '': ['py.typed', '**/*.pyi'],
    },
    install_requires=[
        'mlos-bench==' + _VERSION,
        'dabl @ git+https://github.com/dabl/dabl@0.2.6',    # TODO: Remove in favor of latest pypi release >= 0.2.6
    ],
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Visualization Python interface for benchmark automation and optimization results.'),
    license='MIT',
    keywords='',
    url='https://aka.ms/MLOS',
    python_requires='>=3.8',
)
