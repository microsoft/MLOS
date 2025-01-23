import plotly.express as px
import pandas as pd


def plot_success_failure_distribution(df: pd.DataFrame):
    status_counts = df["status"].value_counts()
    return px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Success/Failure Distribution",
    )


def plot_failure_rate_by_config(df: pd.DataFrame):
    failure_rate = (
        df.groupby("tunable_config_id")["status"]
        .apply(lambda x: (x == "FAILED").mean())
        .reset_index()
    )
    failure_rate.columns = ["tunable_config_id", "failure_rate"]
    return px.bar(
        failure_rate,
        x="tunable_config_id",
        y="failure_rate",
        title="Failure Rate by Configuration",
    )
