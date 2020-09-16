#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from setuptools import setup, find_packages

setup(
    name="mlos",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        'bayesian-optimization>=1.0.1',
        'scikit-learn>=0.22.1',
        'scipy>=1.3.2',
        'numpy>=1.18.1',
        'pandas>=1.0.3',
        'pylint>=2.3.1',
        'pyodbc',
        'grpcio-tools>=1.30.0',
        'tensorboardX>=2.1'
    ],
    author="Microsoft",
    author_email="mlos-maintainers@service.microsoft.com",
    description=("MLOS Python service and client for optimizing code constants"),
    license="MIT",
    keywords="",
    url="https://github.com/microsoft/mlos",
    entry_points={'console_scripts': ['start_mlos_optimization_runtime=mlos.start_mlos_optimization_runtime:main',
                                      'start_optimizer_microservice=mlos.start_optimizer_microservice:main']},

)
