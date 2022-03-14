"""
Contains classes related to experiment exectution runners.
These classes contain the policies for managing things like retries and failed
configs when interacting with the optimizer(s).
"""

# TODO: Implement retry/failure handling logic.

class ExperimentRunner:
    """Manages pending observations for parallel & asynchronous optimization."""
    def __init__(self, optimizer):
        self.optimizer = optimizer

    def register(self, configurations, scores, context=None):
        """Registers the given configurations and scores with the optimizer associated with this ExperimentRunner.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        self.optimizer.register(configurations, scores, context)

    def suggest(self, configurations, context=None):
        """Gets a new configuration suggestion from the optimizer associated
        with this ExperimentRunner and automatically registers it as "pending",
        under the assumption that it will be executed as an experiment trial.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row. Column names are the parameter names.
        """
        configurations = self.optimizer.suggest(context)
        self.optimizer.register_pending(configurations, context)
