"""
Setup instructions for the mlos_bench package.
"""

from setuptools import setup, find_packages

version='0.0.4'

setup(
    name='mlos-bench',
    version=version,
    packages=find_packages(),
    install_requires=[
        'mlos-core=='+version,
    ],
    # Transitive extra_requires from mlos-core.
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
