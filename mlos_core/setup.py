#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Setup instructions for the mlos_core package.
"""

from itertools import chain
from logging import warning

from setuptools import setup, find_packages

from _version import _VERSION   # pylint: disable=import-private-name

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
    'emukit': 'emukit',
    'skopt': 'scikit-optimize<=0.9.0',  # FIXME: temporarily work around some version mismatch issues (PR 850)
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(extra_requires.values())))

# pylint: disable=duplicate-code
setup(
    name='mlos-core',
    version=_VERSION,
    packages=find_packages(),
    package_data={
        'mlos_core': ['py.typed'],
    },
    install_requires=[
        'scikit-learn<1.2', # FIXME: temporarily work around some version mismatch issues (PR 850)
        'joblib>=1.1.1',    # CVE-2022-21797: scikit-learn dependency, addressed in 1.2.0dev0, which isn't currently released
        'scipy>=1.3.2',
        'numpy<1.24',       # FIXME: temporarily work around some version mismatch issues (PR 850)
        'pandas>=1.0.3',
        'ConfigSpace>=0.6.1',
    ],
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Core Python interface for parameter optimization.'),
    license='MIT',
    keywords='',
    url='https://aka.ms/mlos-core',
    python_requires='>=3.8',
)
