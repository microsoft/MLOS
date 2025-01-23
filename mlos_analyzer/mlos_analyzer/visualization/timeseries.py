# src/mlos_analyzer/visualization/timeseries.py
import plotly.express as px
import plotly.graph_objects as go
from typing import List


def plot_metric_over_time(df, metric: str, configs: List[str] = None):
    if configs:
        df = df[df["tunable_config_id"].isin(configs)]

    fig = px.line(
        df,
        x="ts_start",
        y=metric,
        color="tunable_config_id",
        title=f"{metric} Over Time by Configuration",
    )
    return fig


def plot_moving_average(df, metric: str, window: int = 5):
    df = df.sort_values("ts_start")
    df[f"{metric}_ma"] = df[metric].rolling(window=window).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["ts_start"], y=df[metric], mode="markers", name="Raw Data"))
    fig.add_trace(
        go.Scatter(x=df["ts_start"], y=df[f"{metric}_ma"], name=f"{window}-point Moving Average")
    )
    return fig
