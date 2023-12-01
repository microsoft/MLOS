#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Simple abstraction for the OS environment variables.
"""

import os
import sys


if sys.platform == 'win32':
    import nt


# Handle case sensitivity differences between platforms.
# https://stackoverflow.com/a/19023293
environ: os._Environ[str] = nt.environ if sys.platform == 'win32' else os.environ
# alias
os_environ = environ

__all__ = ['environ', 'os_environ']
