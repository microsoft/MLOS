#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_core package.
"""

# pylint: disable=duplicate-code

from itertools import chain
from logging import warning
from typing import Dict, List

import os
import re

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


# A simple routine to read and adjust the README.md for this module into a format
# suitable for packaging.
# See Also: copy-source-tree-docs.sh
# Unfortunately we can't use that directly due to the way packaging happens inside a
# temp directory.
# Similarly, we can't use a utility script outside this module, so this code has to
# be duplicated for now.
# Also, to avoid caching issues when calculating dependencies for the devcontainer,
# we return nothing when the file is not available.
def _get_long_desc_from_readme(base_url: str) -> dict:
    pkg_dir = os.path.dirname(__file__)
    readme_path = os.path.join(pkg_dir, 'README.md')
    if not os.path.isfile(readme_path):
        return {}
    jsonc_re = re.compile(r'```jsonc')
    link_re = re.compile(r'\]\(([^:#)]+)(#[a-zA-Z0-9_-]+)?\)')
    with open(readme_path, mode='r', encoding='utf-8') as readme_fh:
        lines = readme_fh.readlines()
        # Tweak the lexers for local expansion by pygments instead of github's.
        lines = [link_re.sub(f"]({base_url}" + r'/\1\2)', line) for line in lines]
        # Tweak source source code links.
        lines = [jsonc_re.sub(r'```json', line) for line in lines]
        return {
            'long_description': ''.join(lines),
            'long_description_content_type': 'text/markdown',
        }


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
    **_get_long_desc_from_readme('https://github.com/microsoft/MLOS/tree/main/mlos_core'),
    description=('MLOS Core Python interface for parameter optimization.'),
    url='https://github.com/microsoft/MLOS',
    project_urls={
        'Documentation': 'https://microsoft.github.io/MLOS',
        'Package Source': 'https://github.com/microsoft/MLOS/tree/main/mlos_core/',
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
