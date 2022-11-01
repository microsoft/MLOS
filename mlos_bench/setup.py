"""
Setup instructions for the mlos_bench package.
"""

from setuptools import setup, find_packages

_VERSION = '0.0.4'

# pylint: disable=duplicate-code
setup(
    name='mlos-bench',
    version=_VERSION,
    packages=find_packages(),
    install_requires=[
        'mlos-core==' + _VERSION,
        'requests',
    ],
    # Transitive extra_requires from mlos-core.
    extras_require={
        'emukit': 'emukit',
        'skopt': 'scikit-optimize',
        'azure': 'azure-storage-file-share',
    },
    author='Microsoft',
    author_email='mlos-maintainers@service.microsoft.com',
    description=('MLOS Core Python interface for parameter optimization.'),
    license='MIT',
    keywords='',
    # python_requires='>=3.7',
)
