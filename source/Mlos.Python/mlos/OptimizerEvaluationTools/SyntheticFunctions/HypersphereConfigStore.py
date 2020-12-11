#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs import ComponentConfigStore

hypersphere_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="hypersphere_config",
        dimensions=[
            DiscreteDimension(name="num_objectives", min=1, max=100),
            CategoricalDimension(name="minimize", values=["all", "none", "some"]),
            ContinuousDimension(name="radius", min=0, max=100, include_min=False)
        ]
    ),
    default=Point(
        num_objectives=3,
        minimize="all",
        radius=10
    )
)

for num_objectives in [2, 10]:
    for minimize in ["all", "none", "some"]:
        hypersphere_config_store.add_config_by_name(
            config_name=f"{num_objectives}d_hypersphere_minimize_{minimize}",
            config_point=Point(
                num_objectives=num_objectives,
                minimize=minimize,
                radius=10
            ),
            description=f"An objective function with {num_objectives + 1} parameters and {num_objectives} objectives to maximize."
        )
