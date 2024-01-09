#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_bench package.
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


extra_requires: Dict[str, List[str]] = {    # pylint: disable=consider-using-namedtuple-or-dataclass
    # Additional tools for extra functionality.
    'azure': ['azure-storage-file-share', 'azure-identity', 'azure-keyvault'],
    'ssh': ['asyncssh'],
    'storage-sql-duckdb': ['sqlalchemy', 'duckdb_engine'],
    'storage-sql-mysql': ['sqlalchemy', 'mysql-connector-python'],
    'storage-sql-postgres': ['sqlalchemy', 'psycopg2'],
    'storage-sql-sqlite': ['sqlalchemy'],   # sqlite3 comes with python, so we don't need to install it.
    # Transitive extra_requires from mlos-core.
    'flaml': ['flaml[blendsearch]'],
    'smac': ['smac'],
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
    'pytest-lazy-fixture',
    'pytest-docker',
    'fasteners',
]

# pylint: disable=duplicate-code
MODULE_BASE_NAME = 'mlos_bench'
setup(
    name='mlos-bench',
    version=_VERSION,
    packages=find_packages(exclude=[f"{MODULE_BASE_NAME}.tests", f"{MODULE_BASE_NAME}.tests.*"]),
    package_data={
        '': ['py.typed', '**/*.pyi'],
        'mlos_bench': [
            'config/**/*.md',
            'config/**/*.jsonc',
            'config/**/*.json',
            'config/**/*.py',
            'config/**/*.sh',
            'config/**/*.cmd',
            'config/**/*.ps1',
        ],
    },
    entry_points={
        'console_scripts': [
            'mlos_bench = mlos_bench.run:_main',
        ],
    },
    install_requires=[
        'mlos-core==' + _VERSION,
        'requests',
        'json5',
        'jsonschema>=4.18.0', 'referencing>=0.29.1',
        'importlib_resources;python_version<"3.10"',
    ] + extra_requires['storage-sql-sqlite'],   # NOTE: For now sqlite is a fallback storage backend, so we always install it.
    extras_require=extra_requires,
    author='Microsoft',
    license='MIT',
    **_get_long_desc_from_readme('https://github.com/microsoft/MLOS/tree/main/mlos_bench'),
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Bench Python interface for benchmark automation and optimization.'),
    url='https://github.com/microsoft/MLOS',
    project_urls={
        'Documentation': 'https://microsoft.github.io/MLOS',
        'Package Source': 'https://github.com/microsoft/MLOS/tree/main/mlos_bench/',
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
