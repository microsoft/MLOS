#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Export test fixtures for mlos_viz."""

import os
import sys
from glob import glob
from logging import warning
from pathlib import Path

from mlos_bench.tests import tunable_groups_fixtures
from mlos_bench.tests.storage.sql import fixtures as sql_storage_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.

storage = sql_storage_fixtures.storage
exp_storage = sql_storage_fixtures.exp_storage
exp_data = sql_storage_fixtures.exp_data

tunable_groups_config = tunable_groups_fixtures.tunable_groups_config
tunable_groups = tunable_groups_fixtures.tunable_groups

warning("test")

# Workaround for #1004
# See Also: https://github.com/python/cpython/issues/111754
if sys.platform == "win32":
    # Fix Tcl/Tk folder
    tcl_path_info = {
        "TCL_LIBRARY": ["tcl*", "init.tcl"],
        "TK_LIBRARY": ["tk*", "pkgIndex.tcl"],
        "TIX_LIBRARY": ["tix*", "pkgIndex.tcl"],
    }
    for env_var, (subdir_pattern, file_name) in tcl_path_info.items():
        if env_var not in os.environ:
            try:
                os.environ[env_var] = str(
                    Path(
                        next(
                            iter(
                                glob(
                                    os.path.join(
                                        sys.base_prefix,
                                        "Library",
                                        "lib",
                                        subdir_pattern,
                                        file_name,
                                    )
                                )
                            )
                        )
                    ).parent
                )
                warning(f"""Setting {env_var} to {os.environ[env_var]}""")
            except StopIteration:
                warning(f"{env_var} not found, some Tcl/Tk functionality may be limited.")
