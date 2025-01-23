import plotly.graph_objects as go
import pandas as pd
from scipy import stats

def run_pairwise_stat_tests(df: pd.DataFrame, metric: str, alpha: float = 0.05):
   configs = df["tunable_config_id"].unique()
   results = []

   for i in range(len(configs)):
       for j in range(i+1, len(configs)):
           group1 = df[df["tunable_config_id"] == configs[i]][metric]
           group2 = df[df["tunable_config_id"] == configs[j]][metric]

           stat, pval = stats.ttest_ind(group1, group2)
           results.append({
               "Config1": configs[i],
               "Config2": configs[j],
               "p-value": pval,
               "Significant": pval < alpha
           })

   return pd.DataFrame(results)

def compare_score_distributions(df: pd.DataFrame, metric: str, config1: str, config2: str):
   group1 = df[df["tunable_config_id"] == config1][metric]
   group2 = df[df["tunable_config_id"] == config2][metric]
   
   fig = go.Figure()
   fig.add_trace(go.Histogram(x=group1, name=f"Config {config1}", opacity=0.7))
   fig.add_trace(go.Histogram(x=group2, name=f"Config {config2}", opacity=0.7))

   fig.update_layout(barmode="overlay",
                    title=f"Score Distribution Comparison: Config {config1} vs {config2}")
   return fig
