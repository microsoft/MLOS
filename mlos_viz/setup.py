#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_viz package.
"""

# pylint: disable=duplicate-code

from logging import warning
from itertools import chain
from typing import Dict, List

import os
import re

from setuptools import setup, find_packages

from _version import _VERSION    # pylint: disable=import-private-name


# A simple routine to read and adjust the README.md for this module into a format
# suitable for packaging.
# See Also: copy-source-tree-docs.sh
# Unfortunately we can't use that directly due to the way packaging happens inside a
# temp directory.
# Similarly, we can't use a utility script outside this module, so this code has to
# be duplicated for now.
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

extra_requires['full-tests'] = extra_requires['full'] + [
    'pytest',
    'pytest-forked',
    'pytest-xdist',
    'pytest-cov',
    'pytest-local-badge',
]

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
        'dabl>=0.2.6',
    ],
    extras_require=extra_requires,
    author='Microsoft',
    license='MIT',
    **_get_long_desc_from_readme('https://github.com/microsoft/MLOS/tree/main/mlos_viz'),
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Visualization Python interface for benchmark automation and optimization results.'),
    url='https://github.com/microsoft/MLOS',
    project_urls={
        'Documentation': 'https://microsoft.github.io/MLOS',
        'Package Source': 'https://github.com/microsoft/MLOS/tree/main/mlos_viz/',
    },
    python_requires='>=3.8',
    keywords=[
        'autotuning',
        'benchmarking',
        'optimization',
        'systems',
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
