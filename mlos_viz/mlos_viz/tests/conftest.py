#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Export test fixtures for mlos_viz."""

from logging import warning
from pathlib import Path
import glob
import os
import sys

from mlos_bench.tests import tunable_groups_fixtures
from mlos_bench.tests.storage.sql import fixtures as sql_storage_fixtures

# Expose some of those as local names so they can be picked up as fixtures by pytest.

storage = sql_storage_fixtures.storage
exp_storage = sql_storage_fixtures.exp_storage
exp_data = sql_storage_fixtures.exp_data

tunable_groups_config = tunable_groups_fixtures.tunable_groups_config
tunable_groups = tunable_groups_fixtures.tunable_groups

# Workaround for #1004
# See Also: https://github.com/python/cpython/issues/111754
if sys.platform == "win32":
    # Fix Tcl/Tk folder
    if "TK_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = str(
            Path(glob.glob(os.path.join(sys.base_prefix, "tcl", "tcl*", "init.tcl"))[0]).parent
        )
        warning(f"""Setting TCL_LIBRARY to {os.environ["TCL_LIBRARY"]}""")
    if "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = str(
            Path(glob.glob(os.path.join(sys.base_prefix, "tcl", "tk*", "pkgIndex.tcl"))[0]).parent
        )
        warning(f"""Setting TK_LIBRARY to {os.environ["TK_LIBRARY"]}""")
    if "TIX_LIBRARY" not in os.environ:
        os.environ["TIX_LIBRARY"] = str(
            Path(glob.glob(os.path.join(sys.base_prefix, "tcl", "tix*", "pkgIndex.tcl"))[0]).parent
        )
        warning(f"""Setting TIX_LIBRARY to {os.environ["TIX_LIBRARY"]}""")
