#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from threading import Thread

from mlos.Examples.SmartCache.SmartCache import SmartCache
from mlos.Examples.SmartCache.SmartCacheWorkloadGenerator import SmartCacheWorkloadGenerator
from mlos.Mlos.SDK import mlos_globals, MlosAgent


class SmartCacheWorkloadLauncher:
    """Prepares the mlos infrastructure and launches SmartCacheWorkload.

    Parameters
    ----------
    logger : Logger

    Attributes
    ----------
    mlos_agent : MlosAgent
    """
    def __init__(self, logger):
        mlos_globals.init_mlos_global_context()
        self.mlos_agent = MlosAgent(
            logger=logger,
            communication_channel=mlos_globals.mlos_global_context.communication_channel,
            shared_config=mlos_globals.mlos_global_context.shared_config,
        )
        self._mlos_agent_thread = Thread(target=self.mlos_agent.run)
        self._mlos_agent_thread.start()
        self.mlos_agent.add_allowed_component_type(SmartCache)
        self.mlos_agent.add_allowed_component_type(SmartCacheWorkloadGenerator)

        self._smart_cache_workload = SmartCacheWorkloadGenerator(logger=logger)
        self._smart_cache_workload_thread = None

    def start_workload(self, duration_s=1, block=True):
        self._smart_cache_workload_thread = Thread(target=self._smart_cache_workload.run, args=(duration_s,))
        self._smart_cache_workload_thread.start()
        if block:
            self._smart_cache_workload_thread.join()
