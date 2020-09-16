#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd
from mlos.Spaces import CategoricalDimension, ContinuousDimension, Point, SimpleHypergrid, DefaultConfigMeta
from mlos.SynthethicFunctions.sample_functions import quadratic


class MultilevelQuadratic(metaclass=DefaultConfigMeta):
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
            CategoricalDimension(name="vertex_height", values=["low", 5, 15])
        ]
    ).join(
        subgrid=SimpleHypergrid(
            name="low_quadratic_params",
            dimensions=[
                ContinuousDimension(name="x_1", min=-100, max=100),
                ContinuousDimension(name="x_2", min=-100, max=100),
            ]
        ),
        on_external_dimension=CategoricalDimension(name="vertex_height", values=["low"])
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

    _DEFAULT = Point(
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
        if config_params.vertex_height == "low":
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

    @classmethod
    def evaluate_df(cls, configs_df: pd.DataFrame):
        lows = configs_df[configs_df['vertex_height'] == "low"]
        y_for_lows = lows["low_quadratic_params.x_1"] ** 2 + lows["low_quadratic_params.x_1"] ** 2

        mids = configs_df[configs_df['vertex_height'] == 5]
        y_for_mids = mids["medium_quadratic_params.x_1"] ** 2 + mids["medium_quadratic_params.x_1"] ** 2

        highs = configs_df[configs_df['vertex_height'] == 15]
        y_for_highs = highs["high_quadratic_params.x_1"] ** 2 + highs["high_quadratic_params.x_1"] ** 2

        all_ys = pd.concat([y_for_lows, y_for_mids, y_for_highs])
        ys_df = pd.DataFrame(all_ys, columns=['y']).sort_index()
        return ys_df
