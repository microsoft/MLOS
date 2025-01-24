# MLOS Analyzer Dashboard

This project provides a comprehensive dashboard components for analyzing experiments conducted using MLOS. The dashboard components enables users to visualize experiment results, analyze performance metrics, and conduct statistical analyses interactively.

The dashboard components can also be used within a notebook, or streamlit, or any platform which supports plotly.

Another use would be to automate the process of running statistical significance tests to analyze and identify meaningful differences between configuration sets. It enables users to streamline performance analysis by automatically detecting which configurations yield compelling performance improvements.

## Features

1. **Experiment Overview**:

   - View dataset statistics and configuration distributions.
   - Inspect the overall performance of your experiments.

1. **Performance Analysis**:

   - Visualize metrics with whisker plots and heatmaps.
   - Perform advanced analysis using parallel coordinates and performance radar plots.

1. **Time Series Analysis**:

   - Analyze metrics over time.
   - Apply moving average filters for better trend visualization.

1. **Distribution Analysis**:

   - View metric distributions with histogram and violin plots.

1. **Failure Analysis**:

   - Visualize success/failure distributions.
   - Analyze failure rates across different configurations.

1. **Statistical Analysis**:

   - Perform pairwise statistical tests for configuration comparison.
   - Compare score distributions between different configurations.

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```
