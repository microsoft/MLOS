#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking local exec.
"""

import logging
from typing import Iterable, Mapping, Optional, Tuple, TYPE_CHECKING

from mlos_bench.services.base_service import Service
from mlos_bench.services.local.temp_dir_context import TempDirContextService
from mlos_bench.services.types.local_exec_type import SupportsLocalExec

if TYPE_CHECKING:
    from mlos_bench.tunables.tunable import TunableValue

_LOG = logging.getLogger(__name__)


class MockLocalExecService(TempDirContextService, SupportsLocalExec):
    """
    Mock methods for LocalExecService testing.
    """

    def __init__(self, config: Optional[dict] = None,
                 global_config: Optional[dict] = None,
                 parent: Optional[Service] = None):
        super().__init__(config, global_config, parent)
        self.register([self.local_exec])

    def local_exec(self, script_lines: Iterable[str],
                   env: Optional[Mapping[str, "TunableValue"]] = None,
                   cwd: Optional[str] = None,
                   return_on_error: bool = False) -> Tuple[int, str, str]:
        return (0, "", "")
