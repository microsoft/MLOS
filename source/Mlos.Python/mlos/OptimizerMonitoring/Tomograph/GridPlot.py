#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List

from bokeh.io import output_notebook, show
from bokeh.layouts import gridplot
from bokeh.models import CategoricalTicker, ColorBar, ColumnDataSource, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import factor_mark

import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter





