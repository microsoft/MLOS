#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking local exec.
"""

import logging
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, TYPE_CHECKING

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

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None):
        # IMPORTANT: Save the local methods before invoking the base class constructor
        local_methods = [self.local_exec]
        super().__init__(config, global_config, parent)
        self.register(local_methods)

    def local_exec(self, script_lines: Iterable[str],
                   env: Optional[Mapping[str, "TunableValue"]] = None,
                   cwd: Optional[str] = None) -> Tuple[int, str, str]:
        return (0, "", "")
