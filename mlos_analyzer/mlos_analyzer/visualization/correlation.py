import plotly.express as px
import pandas as pd


def plot_heatmap(df: pd.DataFrame):
    numeric_df = df.select_dtypes(include=["int64", "float64"])
    config_columns = [col for col in numeric_df.columns if col.startswith("config")]
    result_columns = [col for col in numeric_df.columns if col.startswith("result")]

    combined_data = numeric_df[config_columns + result_columns]
    correlation_matrix = combined_data.corr()

    fig = px.imshow(
        correlation_matrix,
        title="Configuration vs Results Correlation Heatmap",
        color_continuous_scale="RdBu",
    )
    return fig


def plot_correlation_table_target(df: pd.DataFrame, target_col: str):
    numeric_df = df.select_dtypes(include=["int64", "float64"])
    correlations = numeric_df.corrwith(numeric_df[target_col]).sort_values(ascending=False)

    fig = px.bar(
        x=correlations.index, y=correlations.values, title=f"Correlations with {target_col}"
    )
    return fig
