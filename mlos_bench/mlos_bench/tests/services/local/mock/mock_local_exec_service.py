#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for mocking local exec."""

import logging
from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Any

from mlos_bench.services.base_service import Service
from mlos_bench.services.local.temp_dir_context import TempDirContextService
from mlos_bench.services.types.local_exec_type import SupportsLocalExec

if TYPE_CHECKING:
    from mlos_bench.tunables.tunable import TunableValue

_LOG = logging.getLogger(__name__)


class MockLocalExecService(TempDirContextService, SupportsLocalExec):
    """Mock methods for LocalExecService testing."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
        methods: dict[str, Callable] | list[Callable] | None = None,
    ):
        super().__init__(
            config, global_config, parent, self.merge_methods(methods, [self.local_exec])
        )

    def local_exec(
        self,
        script_lines: Iterable[str],
        env: Mapping[str, "TunableValue"] | None = None,
        cwd: str | None = None,
    ) -> tuple[int, str, str]:
        return (0, "", "")
