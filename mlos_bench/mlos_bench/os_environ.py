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

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 9):
    EnvironType: TypeAlias = os._Environ[str]   # pylint: disable=protected-access,disable=unsubscriptable-object
else:
    EnvironType: TypeAlias = os._Environ        # pylint: disable=protected-access

# Handle case sensitivity differences between platforms.
# https://stackoverflow.com/a/19023293
if sys.platform == 'win32':
    import nt   # type: ignore[import-not-found]    # pylint: disable=import-error  # (3.8)
    environ: EnvironType = nt.environ
else:
    environ: EnvironType = os.environ

__all__ = ['environ']
