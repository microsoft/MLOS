"""
Setup instructions for the mlos_core package.
"""

from setuptools import setup, find_packages

_VERSION = '0.0.4'

# pylint: disable=duplicate-code
setup(
    name='mlos-core',
    version=_VERSION,
    packages=find_packages(),
    install_requires=[
        'scikit-learn>=1.1.3',
        'joblib>=1.1.1',    # CVE-2022-21797: scikit-learn dependency, addressed in 1.2.0dev0, which isn't currently released
        'scipy>=1.3.2',
        'numpy>=1.18.1',
        'pandas>=1.0.3',
        'ConfigSpace>=0.4.21',
    ],
    extras_require={
        'emukit': 'emukit',
        'skopt': 'scikit-optimize',
    },
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Core Python interface for parameter optimization.'),
    license='MIT',
    keywords='',
    # python_requires='>=3.7',
)
