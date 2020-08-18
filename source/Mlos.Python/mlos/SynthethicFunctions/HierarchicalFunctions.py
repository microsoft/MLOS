#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import CategoricalDimension, ContinuousDimension, Point, SimpleHypergrid
from mlos.SynthethicFunctions.sample_functions import quadratic


class MultilevelQuadratic:
    """ A test function to check if the optimizer can handle multilevel functions.

    Functionally, the CONFIG_SPACE is no different from:

    CONFIG_SPACE = SimpleHypergrid(
        name="multilevel_quadratic_config",
        dimensions=[
                 CategoricalDimension(name="vertex_height", values=[0, 5, 15]),
                 ContinuousDimension(name="x_1", min=-100, max=100),
                 ContinuousDimension(name="x_2", min=-100, max=100),
         ]
    )

    But we wanted to stress the hierarchical component here.

    """

    CONFIG_SPACE = SimpleHypergrid(
        name="multilevel_quadratic_config",
        dimensions=[
            CategoricalDimension(name="vertex_height", values=['low', 5, 15])
        ]
    ).join(
        subgrid=SimpleHypergrid(
            name="low_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=['low'])
    ).join(
        subgrid=SimpleHypergrid(
            name="medium_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=[5])
    ).join(
        subgrid=SimpleHypergrid(
            name="high_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=[15])
    )

    DEFAULT = Point(
        vertex_height="high",
        high_quadratic_params=Point(
            x_1=42,
            x_2=79
        )
    )
    _vertical_translations = {
        "low": 0,
        "medium": 5,
        "high": 15
    }

    @classmethod
    def evaluate(cls, config_params):
        assert config_params in cls.CONFIG_SPACE
        if config_params.vertex_height == 'low':
            return quadratic(
                x_1=config_params.low_quadratic_params.x_1,
                x_2=config_params.low_quadratic_params.x_2
            ) + cls._vertical_translations[config_params.vertex_height]
        if config_params.vertex_height == 5:
            return quadratic(
                x_1=config_params.medium_quadratic_params.x_1,
                x_2=config_params.medium_quadratic_params.x_2
            ) + config_params.vertex_height
        return quadratic(
            x_1=config_params.high_quadratic_params.x_1,
            x_2=config_params.high_quadratic_params.x_2
        ) + config_params.vertex_height
