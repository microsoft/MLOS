#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

from mlos.OptimizerEvaluationTools.SyntheticFunctions.MultiObjectiveEnvelopedWaves import MultiObjectiveEnvelopedWaves, \
    multi_objective_enveloped_waves_config_space
from mlos.OptimizerEvaluationTools.SyntheticFunctions.EnvelopedWaves import EnvelopedWaves, enveloped_waves_config_space
from mlos.Spaces import Point

class TestEnvelopedWaves:

    def test_enveloped_waves(self):
        vertical_shift = 1
        for num_params in range(1, 10):
            function_config = Point(
                num_params=num_params,
                num_periods=1,
                amplitude=1,
                vertical_shift=vertical_shift,
                phase_shift=0,
                period=2 * math.pi,
                envelope_type="none"
            )

            assert function_config in enveloped_waves_config_space
            objective_function = EnvelopedWaves(function_config)
            random_params_df = objective_function.parameter_space.random_dataframe(100)
            objectives_df = objective_function.evaluate_dataframe(random_params_df)
            assert ((objectives_df['y'] <= (num_params + vertical_shift)) & (objectives_df['y'] >= vertical_shift)).all()

    def test_random_configs(self):
        for _ in range(100):
            function_config = enveloped_waves_config_space.random()
            objective_function = EnvelopedWaves(function_config)
            random_params_df = objective_function.parameter_space.random_dataframe(100)
            objectives_df = objective_function.evaluate_dataframe(random_params_df)
            assert objective_function.output_space.get_valid_rows_index(objectives_df).equals(objectives_df.index)

    def test_random_multi_objective_configs(self):
        for i in range(100):
            function_config = multi_objective_enveloped_waves_config_space.random()
            print(f"[{i}] Function config: {function_config}")
            objective_function = MultiObjectiveEnvelopedWaves(function_config)
            random_params_df = objective_function.parameter_space.random_dataframe(100)
            objectives_df = objective_function.evaluate_dataframe(random_params_df)
            assert objective_function.output_space.get_valid_rows_index(objectives_df).equals(objectives_df.index)
