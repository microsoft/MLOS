#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import streamlit as st
from mlos_analyzer.core.storage import storage
from mlos_analyzer.visualization.correlation import (
    plot_correlation_table_target,
    plot_heatmap,
)
from mlos_analyzer.visualization.failure_metrics import (
    plot_failure_rate_by_config,
    plot_success_failure_distribution,
)
from mlos_analyzer.visualization.plots import plot_whisker_plots
from mlos_analyzer.visualization.statistical import (
    compare_score_distributions,
    run_pairwise_stat_tests,
)


def main():
    st.set_page_config(page_title="MLOS Analyzer Dashboard", layout="wide")
    st.title("MLOS Experiment Analysis Dashboard")

    # Sidebar for experiment selection
    st.sidebar.header("Settings")
    experiment_ids = list(storage.experiments.keys())
    selected_experiment = st.sidebar.selectbox("Select Experiment", experiment_ids)

    if selected_experiment:
        df = storage.experiments[selected_experiment].results_df

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "Performance Analysis", "Failure Analysis", "Statistical Analysis"]
        )

        with tab1:
            st.header("Experiment Overview")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Dataset Info")
                st.write(df.describe())

            with col2:
                st.subheader("Configuration Distribution")
                config_counts = df["tunable_config_id"].value_counts()
                st.bar_chart(config_counts)

        with tab2:
            st.header("Performance Analysis")

            # Select metric for analysis
            metrics = [col for col in df.columns if col.startswith("result")]
            selected_metric = st.selectbox("Select Performance Metric", metrics)

            col1, col2 = st.columns(2)
            with col1:
                fig_whisker = plot_whisker_plots(df, selected_metric)
                st.plotly_chart(fig_whisker)

            with col2:
                fig_heatmap = plot_heatmap(df)
                st.plotly_chart(fig_heatmap)

        with tab3:
            st.header("Failure Analysis")

            col1, col2 = st.columns(2)
            with col1:
                fig_dist = plot_success_failure_distribution(df)
                st.plotly_chart(fig_dist)

            with col2:
                fig_rate = plot_failure_rate_by_config(df)
                st.plotly_chart(fig_rate)

        with tab4:
            st.header("Statistical Analysis")

            test_metric = st.selectbox("Select Metric for Statistical Tests", metrics)
            alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05)

            results = run_pairwise_stat_tests(df, test_metric, alpha=alpha)
            st.dataframe(results)

            # Compare configurations
            st.subheader("Configuration Comparison")
            config1 = st.selectbox("Select First Configuration", df["tunable_config_id"].unique())
            config2 = st.selectbox("Select Second Configuration", df["tunable_config_id"].unique())

            if config1 != config2:
                fig_compare = compare_score_distributions(df, test_metric, config1, config2)
                st.plotly_chart(fig_compare)


if __name__ == "__main__":
    main()
