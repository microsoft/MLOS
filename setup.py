"""
Setup instructions for the mlos_core package.
"""

from setuptools import setup, find_packages

setup(
    name="mlos-core",
    version="0.0.3",
    packages=find_packages(),
    install_requires=[
        'scikit-learn>=0.22.1',
        'scipy>=1.3.2',
        'numpy>=1.18.1',
        'pandas>=1.0.3',
        'ConfigSpace>=0.4.21',
    ],
    extras_require={
        'emukit': 'emukit',
        'skopt': 'scikit-optimize',
    },
    author="Microsoft",
    author_email="amueller@microsoft.com",
    description=("MLOS Core Python interface for parameter optimization."),
    license="",
    keywords="",
    #python_requires='>=3.7',
)
