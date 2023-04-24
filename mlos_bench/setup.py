#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_bench package.
"""

from logging import warning
from itertools import chain

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


extra_requires = {
    # Additional tools for extra functionality.
    'azure': 'azure-storage-file-share',
    'sqlalchemy': 'sqlalchemy',
    # Transitive extra_requires from mlos-core.
    'emukit': 'emukit',
    'skopt': 'scikit-optimize',
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(extra_requires.values())))  # type: ignore[assignment]

# pylint: disable=duplicate-code
setup(
    name='mlos-bench',
    version=_VERSION,
    packages=find_packages(exclude=['*tests*']),
    exclude_package_data={'': ['tests/**/*']},
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
            'mlos_bench-run_bench = mlos_bench.run_bench:main',
            'mlos_bench-run_opt = mlos_bench.run_opt:main',
        ],
    },
    install_requires=[
        'mlos-core==' + _VERSION,
        'requests',
        'json5',
    ],
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Bench Python interface for benchmark automation and optimization.'),
    license='MIT',
    keywords='',
    url='https://aka.ms/mlos-core',
    python_requires='>=3.8',
)
