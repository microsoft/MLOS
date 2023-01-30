"""
Setup instructions for the mlos_core package.
"""

from itertools import chain
from setuptools import setup, find_packages

_VERSION = '0.0.4'

extra_requires = {
    'emukit': 'emukit',
    'skopt': 'scikit-optimize<=0.9.0',  # temporarily work around some version mismatch issues (PR 850)
}

# construct special 'full' extra that adds requirements for all built-in
# backend integrations and additional extra features.
extra_requires['full'] = list(set(chain(extra_requires.values())))

# pylint: disable=duplicate-code
setup(
    name='mlos-core',
    version=_VERSION,
    packages=find_packages(),
    install_requires=[
        'scikit-learn<1.2', # temporarily work around some version mismatch issues (PR 850)
        'joblib>=1.1.1',    # CVE-2022-21797: scikit-learn dependency, addressed in 1.2.0dev0, which isn't currently released
        'scipy>=1.3.2',
        'numpy>=1.18.1',
        'pandas>=1.0.3',
        'ConfigSpace>=0.6.1',
    ],
    extras_require=extra_requires,
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Core Python interface for parameter optimization.'),
    license='MIT',
    keywords='',
    python_requires='>=3.8',
)
