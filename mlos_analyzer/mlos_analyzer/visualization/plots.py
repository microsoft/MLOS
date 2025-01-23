import plotly.express as px
import pandas as pd


def plot_whisker_plots(df: pd.DataFrame, target_col: str, n: int = 5):
    if "tunable_config_id" not in df.columns or target_col not in df.columns:
        raise ValueError(f"Required columns missing")

    df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
    df = df.dropna(subset=[target_col])

    config_avg = df.groupby("tunable_config_id")[target_col].mean().reset_index()
    top_n_configs = config_avg.nlargest(n, target_col)["tunable_config_id"]
    top_configs = df[df["tunable_config_id"].isin(top_n_configs)]

    fig = px.box(
        top_configs,
        x="tunable_config_id",
        y=target_col,
        title=f"Top {n} Configurations by {target_col}",
    )
    return fig
