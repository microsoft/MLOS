#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from setuptools import find_packages, setup

setup(
    name="mlos_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "pandas",
        "plotly",
        "streamlit",
        "seaborn",
        "matplotlib",
        "scikit-learn",
        "scipy",
        "watchdog",
        "uvicorn",
        "azure-identity",
    ],
)
