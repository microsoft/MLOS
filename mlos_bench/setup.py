#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_bench package.
"""

from itertools import chain
from setuptools import setup, find_packages

from setuptools_scm import get_version

from _version import _VERSION    # pylint: disable=import-private-name

version = get_version(root='..', relative_to=__file__)
if version is not None:
    _VERSION = version

extra_requires = {
    # Additional tools for extra functionality.
    'azure': 'azure-storage-file-share',
    # Transitive extra_requires from mlos-core.
    'emukit': 'emukit',
    'skopt': 'scikit-optimize',
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(extra_requires.values())))

# pylint: disable=duplicate-code
setup(
    name='mlos-bench',
    version=_VERSION,
    packages=find_packages(),
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
