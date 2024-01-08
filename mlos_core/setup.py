#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_core package.
"""

from itertools import chain
from logging import warning
from typing import Dict, List

import os

from setuptools import setup, find_packages

from _version import _VERSION   # pylint: disable=import-private-name

try:
    from setuptools_scm import get_version
    version = get_version(root='..', relative_to=__file__)
    if version is not None:
        _VERSION = version  # noqa: F811
except ImportError:
    warning("setuptools_scm not found, using version from _version.py")
except LookupError as e:
    warning(f"setuptools_scm failed to find git version, using version from _version.py: {e}")


def _get_long_desc_from_readme() -> str:
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_path, mode='r', encoding='utf-8') as fh:
        return ''.join(fh.readlines())


extra_requires: Dict[str, List[str]] = {  # pylint: disable=consider-using-namedtuple-or-dataclass
    'flaml': ['flaml[blendsearch]'],
    'smac': ['smac>=2.0.0'],  # NOTE: Major refactoring on SMAC starting from v2.0.0
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(*extra_requires.values())))

extra_requires['full-tests'] = extra_requires['full'] + [
    'pytest',
    'pytest-forked',
    'pytest-xdist',
    'pytest-cov',
    'pytest-local-badge',
]

# pylint: disable=duplicate-code
MODULE_BASE_NAME = 'mlos_core'
setup(
    name='mlos-core',
    version=_VERSION,
    packages=find_packages(exclude=[f"{MODULE_BASE_NAME}.tests", f"{MODULE_BASE_NAME}.tests.*"]),
    package_data={
        '': ['py.typed', '**/*.pyi'],
    },
    install_requires=[
        'scikit-learn>=1.2',
        'joblib>=1.1.1',        # CVE-2022-21797: scikit-learn dependency, addressed in 1.2.0dev0, which isn't currently released
        'scipy>=1.3.2',
        'numpy>=1.24',
        'pandas>=1.0.3',
        'ConfigSpace>=0.7.1',
    ],
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    license='MIT',
    long_description=_get_long_desc_from_readme(),
    long_description_content_type='text/markdown',
    description=('MLOS Core Python interface for parameter optimization.'),
    url='https://github.com/microsoft/MLOS',
    project_urls={
        'docs': 'https://microsoft.github.io/MLOS',
        'package_source': 'https://github.com/microsoft/MLOS/tree/main/mlos_core/',
    },
    python_requires='>=3.8',
    keywords=[
        'autotuning',
        'optimization',
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)
