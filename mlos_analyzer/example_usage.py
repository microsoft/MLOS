# Run as "streamlit run example_usage.py"

import streamlit as st
from mlos_analyzer.core.storage import storage
from mlos_analyzer.visualization.plots import plot_whisker_plots
from mlos_analyzer.visualization.correlation import plot_heatmap, plot_correlation_table_target
from mlos_analyzer.visualization.failure_metrics import (
    plot_success_failure_distribution,
    plot_failure_rate_by_config,
)
from mlos_analyzer.visualization.statistical import (
    run_pairwise_stat_tests,
    compare_score_distributions,
)
from mlos_analyzer.visualization.timeseries import plot_metric_over_time, plot_moving_average
from mlos_analyzer.visualization.distributions import plot_metric_distribution, plot_violin_comparison
from mlos_analyzer.visualization.performance import plot_parallel_coordinates, plot_performance_radar


def main():
    st.set_page_config(page_title="MLOS Analyzer Dashboard", layout="wide")
    st.title("MLOS Experiment Analysis Dashboard")

    st.sidebar.header("Settings")
    experiment_ids = list(storage.experiments.keys())
    selected_experiment = st.sidebar.selectbox("Select Experiment", experiment_ids)

    if selected_experiment:
        df = storage.experiments[selected_experiment].results_df
        metrics = [col for col in df.columns if col.startswith("result")]

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            ["Overview", "Performance", "Time Series", "Distributions", "Failures", "Statistics"]
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
            selected_metric = st.selectbox("Select Metric", metrics, key="perf_metric")
            
            col1, col2 = st.columns(2)
            with col1:
                fig_whisker = plot_whisker_plots(df, selected_metric)
                st.plotly_chart(fig_whisker)
            with col2:
                fig_heatmap = plot_heatmap(df)
                st.plotly_chart(fig_heatmap)

            selected_metrics = st.multiselect("Select Metrics for Advanced Analysis", metrics, default=metrics[:3])
            if selected_metrics:
                col3, col4 = st.columns(2)
                with col3:
                    fig = plot_parallel_coordinates(df, selected_metrics)
                    st.plotly_chart(fig)
                with col4:
                    fig = plot_performance_radar(df, selected_metrics)
                    st.plotly_chart(fig)

        with tab3:
            st.header("Time Series Analysis")
            metric = st.selectbox("Select Metric", metrics, key="ts_metric")
            window = st.slider("Moving Average Window", 2, 20, 5)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = plot_metric_over_time(df, metric)
                st.plotly_chart(fig)
            with col2:
                fig = plot_moving_average(df, metric, window)
                st.plotly_chart(fig)

        with tab4:
            st.header("Distribution Analysis")
            metric = st.selectbox("Select Metric", metrics, key="dist_metric")
            
            col1, col2 = st.columns(2)
            with col1:
                fig = plot_metric_distribution(df, metric)
                st.plotly_chart(fig)
            with col2:
                fig = plot_violin_comparison(df, metric)
                st.plotly_chart(fig)

        with tab5:
            st.header("Failure Analysis")
            col1, col2 = st.columns(2)
            with col1:
                fig_dist = plot_success_failure_distribution(df)
                st.plotly_chart(fig_dist)
            with col2:
                fig_rate = plot_failure_rate_by_config(df)
                st.plotly_chart(fig_rate)

        with tab6:
            st.header("Statistical Analysis")
            test_metric = st.selectbox("Select Test Metric", metrics)
            alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05)

            results = run_pairwise_stat_tests(df, test_metric, alpha=alpha)
            st.dataframe(results)

            st.subheader("Configuration Comparison")
            config1, config2 = st.columns(2)
            with config1:
                cfg1 = st.selectbox("First Configuration", df["tunable_config_id"].unique())
            with config2:
                cfg2 = st.selectbox("Second Configuration", df["tunable_config_id"].unique())

            if cfg1 != cfg2:
                fig_compare = compare_score_distributions(df, test_metric, cfg1, cfg2)
                st.plotly_chart(fig_compare)


if __name__ == "__main__":
    main()
