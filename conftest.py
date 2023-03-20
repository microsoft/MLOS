#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Provides some pytest configuration overrides for both modules.
"""

# Note: This file is named conftest.py so that pytest picks it up automatically
# without the need to adjust PYTHONPATH or sys.path as much.

import os
from warnings import warn


def pytest_configure(config):   # pylint: disable=unused-argument
    """
    Add some additional (global) configuration steps for pytest.
    """
    # Workaround some issues loading emukit in certain environments.
    if os.environ.get('DISPLAY', None):
        import matplotlib   # pylint: disable=import-outside-toplevel
        matplotlib.rcParams['backend'] = 'agg'
        warn(UserWarning('DISPLAY environment variable is set, which can cause problems in some setups (e.g. WSL). '
            + f'Adjusting matplotlib backend to "{matplotlib.rcParams["backend"]}" to compensate.'))
