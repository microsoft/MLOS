#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple
import datetime
import random

from mlos.Mlos.SDK import MlosObject, MlosSmartComponentRuntimeAttributes

from .SmartCache import SmartCache
from .MlosInterface import smart_cache_workload_generator_default_config, smart_cache_workload_generator_config_space


# Let's define telemetry events emitted by this component
SmartCacheWorkloadGeneratorReconfigure = namedtuple(
    typename="SmartCacheWorkloadGeneratorReconfigure",
    field_names=['old_config_id', 'new_config_id']
)


class SmartCacheWorkloadGenerator:
    """Instantiates one (or many) SmartCaches and subjects them to various workloads.

    The main idea here is to exercise all use-cases demanded of Mlos.

    Parameters
    ----------
    logger : Logger
        Logger.

    Attributes
    ----------
    RuntimeAttributes : MlosSmartComponentRuntimeAttributes
    default_config : Point
    telemetry_message_types : list
    mlos_object : MlosObject

    """
    RuntimeAttributes = MlosSmartComponentRuntimeAttributes(
        smart_component_name="SmartCacheWorkloadGenerator",
        attribute_names=[]
    )

    default_config = smart_cache_workload_generator_default_config
    parameter_search_space = smart_cache_workload_generator_config_space
    telemetry_message_types = []

    def __init__(self, logger):
        self.logger = logger
        self.current_config = None

        # Let's use an mlos_object to drive the runtime configuration of the cache
        self.mlos_object = MlosObject(
            smart_component_type=type(self),
            smart_component_runtime_attributes=self.RuntimeAttributes(component_id=id(self))
        )
        self.mlos_object.register()
        self.reconfigure()

    def __del__(self):
        self.mlos_object.unregister()

    def reconfigure(self):
        new_config = self.mlos_object.config
        if new_config == self.current_config:
            return False

        self.mlos_object.send_telemetry_message(SmartCacheWorkloadGeneratorReconfigure(
            old_config_id=self.current_config.id if self.current_config is not None else 0,
            new_config_id=new_config.id
        ))
        self.current_config = new_config
        return True

    def run(self, timeout_s=1):
        self.logger.debug(f"Started the SmartCacheWorkloadGenerator. Duration={timeout_s}")
        self.reconfigure()
        smart_cache = SmartCache(logger=self.logger)

        start_time = datetime.datetime.utcnow()
        end_time = start_time + datetime.timedelta(seconds=timeout_s)

        while datetime.datetime.utcnow() < end_time:
            if self.current_config.values.workload_type == 'fibonacci':
                self.fibonacci_workload(end_time, smart_cache)
            elif self.current_config.values.workload_type == 'random_key_from_range':
                self.random_key_from_range(end_time, smart_cache)
            elif self.current_config.values.workload_type == 'cyclical_key_from_range':
                self.cyclical_key_from_range(end_time, smart_cache)
            else:
                raise RuntimeError(f"Unknown workload type: {self.current_config.values.workload_type}")
        self.logger.debug("Exiting the SmartCacheWorkloadGenerator.")

    def fibonacci_workload(self, end_time, smart_cache):
        range_min = self.current_config.values.fibonacci_config.min
        range_max = range_min + self.current_config.values.fibonacci_config.range_width

        while datetime.datetime.utcnow() < end_time:
            sequence_number = random.randint(range_min, range_max)
            self.logger.debug(f"\tfib({sequence_number}) = ?")
            result = self.fibonacci(sequence_number, smart_cache)
            self.logger.debug(f"\tfib({sequence_number}) = {result}")

    def random_key_from_range(self, end_time, smart_cache):
        range_min = self.current_config.values.random_key_from_range_config.min
        range_max = range_min + self.current_config.values.random_key_from_range_config.range_width
        while datetime.datetime.utcnow() < end_time:
            key = random.randint(range_min, range_max)
            value = smart_cache.get(key)
            if value is None:
                value = str(key)
                smart_cache.push(key, value)

    def cyclical_key_from_range(self, end_time, smart_cache):
        range_min = self.current_config.values.cyclical_key_from_range_config.min
        range_width = self.current_config.values.cyclical_key_from_range_config.range_width
        i = 0
        while datetime.datetime.utcnow() < end_time:
            key = range_min + (i % range_width)
            value = smart_cache.get(key)
            if value is None:
                value = str(key)
                smart_cache.push(key, value)
            i += 1

    class _FibonacciValue:
        def __init__(self, sequence_number, value, previous):
            self.sequence_number = sequence_number
            self.value = value
            self.previous = previous

    def fibonacci(self, sequence_number, smart_cache):
        existing_result = smart_cache.get(sequence_number)

        max_key_up_to = None
        if existing_result is None:
            all_cached_smaller_keys = [element.key for element in smart_cache if element.key < sequence_number]
            if all_cached_smaller_keys:
                max_key_up_to = max(all_cached_smaller_keys)

        start = 1
        previous = 1
        current = 1

        if max_key_up_to is not None:
            cached_value = smart_cache.get(max_key_up_to)
            if cached_value is not None:
                previous = cached_value.previous
                current = cached_value.value
                start = cached_value.sequence_number

        for i in range(start + 1, sequence_number):
            previous, current = current, previous + current
            smart_cache.push(key=i, value=self._FibonacciValue(sequence_number=i, value=current, previous=previous))

        return current
