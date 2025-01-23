# src/mlos_analyzer/visualization/distributions.py
import plotly.express as px
import plotly.figure_factory as ff


def plot_metric_distribution(df, metric: str):
    fig = ff.create_distplot(
        [df[metric].dropna()], [metric], bin_size=(df[metric].max() - df[metric].min()) / 30
    )
    fig.update_layout(title=f"Distribution of {metric}")
    return fig


def plot_violin_comparison(df, metric: str, group_by: str = "tunable_config_id"):
    fig = px.violin(
        df,
        x=group_by,
        y=metric,
        box=True,
        points="all",
        title=f"{metric} Distribution by {group_by}",
    )
    return fig
