# src/mlos_analyzer/visualization/performance.py
import plotly.express as px
import plotly.graph_objects as go
from typing import List


def plot_parallel_coordinates(df, metrics: List[str]):
    fig = px.parallel_coordinates(
        df,
        dimensions=[col for col in df.columns if col.startswith("config") or col in metrics],
        title="Parameter and Metric Relationships",
    )
    return fig


def plot_performance_radar(df, metrics: List[str], top_n: int = 5):
    # Normalize metrics
    normalized_df = df.copy()
    for metric in metrics:
        normalized_df[metric] = (df[metric] - df[metric].min()) / (
            df[metric].max() - df[metric].min()
        )

    # Get top configurations
    top_configs = (
        normalized_df.groupby("tunable_config_id")[metrics]
        .mean()
        .mean(axis=1)
        .nlargest(top_n)
        .index
    )

    fig = go.Figure()
    for config in top_configs:
        config_data = normalized_df[normalized_df["tunable_config_id"] == config][metrics].mean()
        fig.add_trace(
            go.Scatterpolar(r=config_data.values, theta=metrics, name=f"Config {config}")
        )

    fig.update_layout(title=f"Top {top_n} Configurations Performance")
    return fig  # src/mlos_analyzer/visualization/performance.py


import plotly.express as px
import plotly.graph_objects as go


def plot_parallel_coordinates(df, metrics: List[str]):
    fig = px.parallel_coordinates(
        df,
        dimensions=[col for col in df.columns if col.startswith("config") or col in metrics],
        title="Parameter and Metric Relationships",
    )
    return fig


def plot_performance_radar(df, metrics: List[str], top_n: int = 5):
    # Normalize metrics
    normalized_df = df.copy()
    for metric in metrics:
        normalized_df[metric] = (df[metric] - df[metric].min()) / (
            df[metric].max() - df[metric].min()
        )

    # Get top configurations
    top_configs = (
        normalized_df.groupby("tunable_config_id")[metrics]
        .mean()
        .mean(axis=1)
        .nlargest(top_n)
        .index
    )

    fig = go.Figure()
    for config in top_configs:
        config_data = normalized_df[normalized_df["tunable_config_id"] == config][metrics].mean()
        fig.add_trace(
            go.Scatterpolar(r=config_data.values, theta=metrics, name=f"Config {config}")
        )

    fig.update_layout(title=f"Top {top_n} Configurations Performance")
    return fig
