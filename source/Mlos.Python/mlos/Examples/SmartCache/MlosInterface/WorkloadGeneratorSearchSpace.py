#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import SimpleHypergrid, CategoricalDimension, DiscreteDimension, Point

_root_smart_cache_workload_generator_config_space = SimpleHypergrid(
    name='smart_cache_workload_generator_config',
    dimensions=[
        CategoricalDimension('workload_type', values=['fibonacci', 'random_key_from_range', 'sequential_key_from_range']),
        DiscreteDimension('reconfiguration_interval', min=10, max=11)
    ]
)

_fibonacci_config_space = SimpleHypergrid(
    name='fibonacci_config',
    dimensions=[
        DiscreteDimension('min', min=0, max=2 ** 10),
        DiscreteDimension('range_width', min=0, max=2 ** 10)
    ]
)

_random_key_from_range_config_space = SimpleHypergrid(
    name='random_key_from_range_config',
    dimensions=[
        DiscreteDimension('min', min=0, max=2 ** 10),
        DiscreteDimension('range_width', min=0, max=2 ** 10)
    ]
)

_sequential_key_from_range_config_space = SimpleHypergrid(
    name='sequential_key_from_range_config',
    dimensions=[
        DiscreteDimension('min', min=0, max=2 ** 10),
        DiscreteDimension('range_width', min=0, max=2 ** 10)
    ]
)


smart_cache_workload_generator_config_space = _root_smart_cache_workload_generator_config_space.join(
    subgrid=_fibonacci_config_space,
    on_external_dimension=CategoricalDimension('workload_type', values=['fibonacci']),
).join(
    subgrid=_random_key_from_range_config_space,
    on_external_dimension=CategoricalDimension('workload_type', values=['random_key_from_range']),
).join(
    subgrid=_sequential_key_from_range_config_space,
    on_external_dimension=CategoricalDimension('workload_type', values=['sequential_key_from_range']),
)

smart_cache_workload_generator_default_config = Point(
    workload_type='fibonacci',
    reconfiguration_interval=10,
    fibonacci_config=Point(
        min=2 ** 10,
        range_width=2 ** 10
    )
)
assert smart_cache_workload_generator_default_config in smart_cache_workload_generator_config_space
