#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Simple platform agnostic abstraction for the OS environment variables.
Meant as a replacement for os.environ vs nt.environ.

Example
-------
from mlos_bench.os_env import environ
environ['FOO'] = 'bar'
environ.get('PWD')
"""

import os
import sys


if sys.platform == 'win32':
    import nt   # type: ignore[import-not-found]

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 9):
    ENVIRON_TYPE: TypeAlias = os._Environ[str]
else:
    ENVIRON_TYPE: TypeAlias = os._Environ

# Handle case sensitivity differences between platforms.
# https://stackoverflow.com/a/19023293
environ: ENVIRON_TYPE = nt.environ if sys.platform == 'win32' else os.environ

__all__ = ['environ']
