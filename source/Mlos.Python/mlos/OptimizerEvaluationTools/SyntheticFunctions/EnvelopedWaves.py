#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import numpy as np
import pandas as pd

from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid, Hypergrid
from mlos.Spaces.Configs import ComponentConfigStore

enveloped_waves_config_space = SimpleHypergrid(
    name="enveloped_waves_config",
    dimensions=[
        DiscreteDimension(name="num_params", min=1, max=100),
        ContinuousDimension(name="num_periods", min=1, max=100),
        ContinuousDimension(name="vertical_shift", min=0, max=10),
        ContinuousDimension(name="phase_shift", min=0, max=10000),
        ContinuousDimension(name="period", min=0, max=10 * math.pi, include_min=False),
        CategoricalDimension(name="envelope_type", values=["linear", "quadratic", "sine", "none"])
    ]
).join(
    subgrid=SimpleHypergrid(
        name="linear_envelope_config",
        dimensions=[
            ContinuousDimension(name="gradient", min=-100, max=100)
        ]
    ),
    on_external_dimension=CategoricalDimension(name="envelope_type", values=["linear"])
).join(
    subgrid=SimpleHypergrid(
        name="quadratic_envelope_config",
        dimensions=[
            ContinuousDimension(name="a", min=-100, max=100),
            ContinuousDimension(name="p", min=-100, max=100),
        ]
    ),
    on_external_dimension=CategoricalDimension(name="envelope_type", values=["quadratic"])
).join(
    subgrid=SimpleHypergrid(
        name="sine_envelope_config",
        dimensions=[
            ContinuousDimension(name="amplitude", min=0, max=10, include_min=False),
            ContinuousDimension(name="phase_shift", min=0, max=2 * math.pi),
            ContinuousDimension(name="period", min=0, max=100 * math.pi, include_min=False),
        ]
    ),
    on_external_dimension=CategoricalDimension(name="envelope_type", values=["sine"])
)

enveloped_waves_config_store = ComponentConfigStore(
    parameter_space=enveloped_waves_config_space,
    default=Point(
        num_params=3,
        num_periods=1,
        vertical_shift=0,
        phase_shift=0,
        period=2 * math.pi,
        envelope_type="none"
    ),
    description="TODO"
)

class EnvelopedWaves(ObjectiveFunctionBase):
    """Sum of sine waves enveloped by another function, either linear, quadratic or another sine wave.
    An enveloped sine wave produces complexity for the optimizer that allows us evaluate its behavior on non-trivial problems.
    Simultaneously, sine waves have the following advantages over polynomials:
        1. They have well known optima - even when we envelop the function with another sine wave, as long as we keep their frequencies
            harmonic, we can know exactly where the optimum is.
        2. They cannot be well approximated by a polynomial (Taylor expansion is accurate only locally).
        3. For multi-objective problems, we can manipulate the phase shift of each objective to control the shape of the pareto frontier.
    How the function works?
    -----------------------
    When creating the function we specify:
    1. Amplitute, vertical_shift, phase-shift and period of the sine wave.
    2. Envelope:
        1. Linear: gradient (no need y_intercept as it's included in the vertical_shift)
        2. Quadratic: a, p, q
        3. Sine: again amplitude, phase shift, and period (no need to specify the vertical shift again.
    The function takes the form:
        y(x) = sum(
            amplitude * sin((x_i - phase_shift) / period) * envelope(x_i) + vertical_shift
            for x_i
            in x
        )
        WHERE:
            envelope(x_i) = envelope.gradient * x_i + envelope.y_intercept
            OR
            envelope(x_i) = a * (x_i - p) ** 2 + q
            OR
            envelope(x_i) = envelope.amplitude * sin((x_i - envelope.phase_shift) / envelope.period)
    """

    def __init__(self, objective_function_config: Point = None):
        assert objective_function_config in enveloped_waves_config_space, f"{objective_function_config} not in {enveloped_waves_config_space}"
        ObjectiveFunctionBase.__init__(self, objective_function_config)
        self._parameter_space = SimpleHypergrid(
            name="domain",
            dimensions=[
                ContinuousDimension(name=f"x_{i}", min=0, max=objective_function_config.num_periods * objective_function_config.period)
                for i in range(self.objective_function_config.num_params)
            ]
        )

        self._output_space = SimpleHypergrid(
            name="range",
            dimensions=[
                ContinuousDimension(name="y", min=-math.inf, max=math.inf)
            ]
        )

        if self.objective_function_config.envelope_type == "linear":
            self._envelope = self._linear_envelope
        elif self.objective_function_config.envelope_type == "quadratic":
            self._envelope = self._quadratic_envelope
        elif self.objective_function_config.envelope_type == "sine":
            self._envelope = self._sine_envelope
        else:
            self._envelope = lambda x: x * 0 + 1

    @property
    def parameter_space(self) -> Hypergrid:
        return self._parameter_space

    @property
    def output_space(self) -> Hypergrid:
        return self._output_space


    def evaluate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        objectives_df = pd.DataFrame(0, index=dataframe.index, columns=['y'], dtype='float')
        for param_name in self._parameter_space.dimension_names:
            objectives_df['y'] += np.sin(
                dataframe[param_name] / self.objective_function_config.period * 2 * math.pi - self.objective_function_config.phase_shift
            ) * self._envelope(dataframe[param_name])
        objectives_df['y'] += self.objective_function_config.vertical_shift

        return objectives_df

    def _linear_envelope(self, x: pd.Series):
        return x * self.objective_function_config.linear_envelope_config.gradient

    def _quadratic_envelope(self, x: pd.Series):
        a = self.objective_function_config.quadratic_envelope_config.a
        p = self.objective_function_config.quadratic_envelope_config.p
        return a * (x - p) ** 2

    def _sine_envelope(self, x: pd.Series):
        amplitude = self.objective_function_config.sine_envelope_config.amplitude
        phase_shift = self.objective_function_config.sine_envelope_config.phase_shift
        period = self.objective_function_config.sine_envelope_config.period
        return amplitude * np.sin(x / period - phase_shift)


    def get_context(self) -> Point:
        return self.objective_function_config
