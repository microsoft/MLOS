#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Examples.SmartCache.CacheImplementations.CacheEntry import CacheEntry
from mlos.Examples.SmartCache.CacheImplementations.LruCache import LruCache, LruCacheConfig
from mlos.Examples.SmartCache.CacheImplementations.MruCache import MruCache, MruCacheConfig
from mlos.Examples.SmartCache.MlosInterface import PushRuntimeDecisionContext, ReconfigurationRuntimeDecisionContext
from mlos.Examples.SmartCache.MlosInterface.MlosTelemetryMessages import SmartCacheGet, SmartCachePush, SmartCacheEvict

from mlos.Mlos.Infrastructure.ConfigurationManager import Configuration

from mlos.Spaces import CategoricalDimension, Point, SimpleHypergrid
from mlos.Mlos.SDK import MlosObject, MlosSmartComponentRuntimeAttributes


class SmartCache:
    """ A tunable and observable cache that takes advantage of Mlos.

    The goal here is to provide a bunch of cache implementations that are parameterizable.

    Parameters
    ----------
    logger : Logger
        Logger to use.

    Attributes
    ----------
    RuntimeAttributes : MlosSmartComponentRuntimeAttributes
    parameter_search_space : SimpleHypergrid
    default_config : Point
    telemetry_message_types : list
    runtime_decision_contexts : list
    """

    # Used during registration
    RuntimeAttributes = MlosSmartComponentRuntimeAttributes(
        smart_component_name="SmartCache",
        attribute_names=[]
    )

    parameter_search_space = SimpleHypergrid(
        name='smart_cache_config',
        dimensions=[
            CategoricalDimension(name='implementation', values=['LRU', 'MRU'])
        ]
    ).join(
        subgrid=LruCacheConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name='implementation', values=['LRU'])
    ).join(
        subgrid=MruCacheConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name='implementation', values=['MRU'])
    )

    # Used if no intelligence is hooked up
    default_config = Point(implementation='LRU', lru_cache_config=LruCacheConfig.DEFAULT)

    # Used to inform the Mlos Global Context about all types of telemetry messages that this component can emit
    telemetry_message_types = [
        (SmartCachePush, 0b1),
        (SmartCacheGet, 0b10),
        (SmartCacheEvict, 0b100),
    ]

    # Used to inform the Mlos Global Context about all types of runtime decisions that can be expected
    runtime_decision_contexts = [
        PushRuntimeDecisionContext,
        ReconfigurationRuntimeDecisionContext,
    ]


    def __init__(self, logger):
        self.logger = logger
        self.mlos_object = MlosObject(
            smart_component_type=type(self),
            smart_component_runtime_attributes=self.RuntimeAttributes(component_id=id(self))
        )
        self.current_config = Configuration(component_type=SmartCache, values=self.default_config, id=-1)
        self.cache_implementation = LruCache(max_size=self.current_config.values.lru_cache_config.cache_size, logger=self.logger)
        self.mlos_object.register()

        self.reconfigure()

    def __del__(self):
        self.mlos_object.unregister()

    def __iter__(self):
        return self.cache_implementation.__iter__()

    def __len__(self):
        return len(self.cache_implementation)

    def __contains__(self, item):
        return item in self.cache_implementation

    def push(self, key, value):
        self.reconfigure() # TODO: make this less frequent

        if key in self:
            return

        should_push = self.mlos_object.make_runtime_decision(PushRuntimeDecisionContext(
            mlos_object=self.mlos_object,
            current_config=self.current_config
        ))

        if not should_push:
            return

        if self.mlos_object.is_message_type_enabled(SmartCachePush):
            # Note that we hide this behind an 'is_enabled' check. This is for the cases
            # when assembling the message itself can be expensive.
            self.mlos_object.send_telemetry_message(SmartCachePush(key=key))
        cache_entry = CacheEntry(key, value)

        evicted_cache_entry = self.cache_implementation.push(cache_entry)

        if evicted_cache_entry is not None:
            # Note that here we skip the 'is message type enabled check' since assembling the message is cheap and
            # the check can be done by mlos_object
            self.mlos_object.send_telemetry_message(SmartCacheEvict(key=evicted_cache_entry.key))


    def get(self, key):
        if key not in self.cache_implementation:
            self.mlos_object.send_telemetry_message(SmartCacheGet(key=key, was_hit=False))
            return None
        self.mlos_object.send_telemetry_message(SmartCacheGet(key=key, was_hit=True))
        return self.cache_implementation.get(key)


    def reconfigure(self):
        """ Reconfigures the cache according to the configuration present in self.mlos_object

        :return:
        """
        smart_cache_reconfiguration_decision_runtime_context = ReconfigurationRuntimeDecisionContext(self.mlos_object)
        should_reconfigure = self.mlos_object.make_runtime_decision(smart_cache_reconfiguration_decision_runtime_context)
        if not should_reconfigure or self.current_config == self.mlos_object.config or self.mlos_object.config is None:
            return

        self.current_config = self.mlos_object.config
        self.logger.debug(f"Reconfiguring. New config values: {self.current_config.values.to_json()}")

        if self.current_config.values.implementation == 'LRU':
            self.cache_implementation = LruCache(max_size=self.current_config.values.lru_cache_config.cache_size, logger=self.logger)
        elif self.current_config.values.implementation == 'MRU':
            self.cache_implementation = MruCache(max_size=self.current_config.values.mru_cache_config.cache_size, logger=self.logger)
        else:
            raise RuntimeError("Invalid config")
