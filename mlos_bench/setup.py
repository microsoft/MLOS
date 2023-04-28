#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_bench package.
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
        _VERSION = version
except ImportError:
    warning("setuptools_scm not found, using version from _version.py")
except LookupError as e:
    warning(f"setuptools_scm failed to find git version, using version from _version.py: {e}")


extra_requires: Dict[str, List[str]] = {
    # Additional tools for extra functionality.
    'azure': ['azure-storage-file-share'],
    'storage-sql-duckdb': ['sqlalchemy', 'duckdb_engine'],
    'storage-sql-mysql': ['sqlalchemy', 'mysql-connector-python'],
    'storage-sql-postgres': ['sqlalchemy', 'psycopg2'],
    'storage-sql-sqlite': ['sqlalchemy'],   # sqlite3 comes with python, so we don't need to install it.
    # Transitive extra_requires from mlos-core.
    'emukit': ['emukit'],
    'skopt': ['scikit-optimize'],
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
MODULE_BASE_NAME = 'mlos_bench'
setup(
    name='mlos-bench',
    version=_VERSION,
    packages=find_packages(exclude=[f"{MODULE_BASE_NAME}.tests", f"{MODULE_BASE_NAME}.tests.*"]),
    package_data={
        '': ['py.typed', '**/*.pyi'],
    },
    install_requires=[
        'mlos-core==' + _VERSION,
        'requests',
        'json5',
    ] + extra_requires['storage-sql-sqlite'],   # NOTE: For now sqlite is a fallback storage backend, so we always install it.
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Bench Python interface for benchmark automation and optimization.'),
    license='MIT',
    keywords='',
    url='https://aka.ms/mlos-core',
    python_requires='>=3.8',
)
