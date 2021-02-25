#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
from sklearn.tree import DecisionTreeRegressor

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.DecisionTreeConfigStore import decision_tree_config_store
from mlos.Spaces import Hypergrid, Point
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter
from mlos.Tracer import trace


class DecisionTreeRegressionModel(RegressionModel):
    """ Wraps sklearn's DecisionTreeRegressor.

    TODO: Beef up the RegressionModel base class and actually enforce a consistent interface.
    TODO: See how much boilerplate we can remove from model creation.
    """


    _PREDICTOR_OUTPUT_COLUMNS = [
        Prediction.LegalColumnNames.IS_VALID_INPUT,
        Prediction.LegalColumnNames.PREDICTED_VALUE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE,
        Prediction.LegalColumnNames.SAMPLE_VARIANCE,
        Prediction.LegalColumnNames.SAMPLE_SIZE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM
    ]

    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        if logger is None:
            logger = create_logger("DecisionTreeRegressionModel")
        self.logger = logger

        assert model_config in decision_tree_config_store.parameter_space
        RegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )

        self._input_space_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.input_space)

        self.input_dimension_names = [dimension.name for dimension in self._input_space_adapter.dimensions]
        self.target_dimension_names = [dimension.name for dimension in self.output_space.dimensions]
        self.logger.debug(f"Input dimensions: {str(self.input_dimension_names)}; Target dimensions: {str(self.target_dimension_names)}.")

        assert len(self.target_dimension_names) == 1, "For now (and perhaps forever) we only support single target per tree."

        self._regressor = DecisionTreeRegressor(
            criterion=self.model_config.criterion,
            splitter=self.model_config.splitter,
            max_depth=self.model_config.max_depth if self.model_config.max_depth != 0 else None,
            min_samples_split=self.model_config.min_samples_split,
            min_samples_leaf=self.model_config.min_samples_leaf,
            min_weight_fraction_leaf=self.model_config.min_weight_fraction_leaf,
            max_features=self.model_config.max_features,
            random_state=self.model_config.get("random_state", None),
            max_leaf_nodes=self.model_config.max_leaf_nodes if self.model_config.max_leaf_nodes not in (0, 1) else None,
            min_impurity_decrease=self.model_config.min_impurity_decrease,
            ccp_alpha=self.model_config.ccp_alpha
        )

        # These are used to compute the variance in predictions
        self._observations_per_leaf = dict()
        self._mean_per_leaf = dict()
        self._mean_variance_per_leaf = dict()
        self._sample_variance_per_leaf = dict()
        self._count_per_leaf = dict()

        self._trained = False

    @property
    def trained(self):
        return self._trained

    @property
    def num_observations_used_to_fit(self):
        return self.last_refit_iteration_number

    def should_fit(self, num_samples):
        """ Returns true if the model should be fitted.

        This model should be fitted under the following conditions:
        1) It has not been fitted yet and num_samples is larger than min_samples_to_fit
        2) The model has been fitted and the number of new samples is larger than n_new_samples_before_refit

        :param num_samples:
        :return:
        """
        if not self.trained:
            return num_samples > self.model_config.min_samples_to_fit
        num_new_samples = num_samples - self.num_observations_used_to_fit
        return num_new_samples >= self.model_config.n_new_samples_before_refit

    @trace()
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number):
        self.logger.debug(f"Fitting a {self.__class__.__name__} with {len(feature_values_pandas_frame.index)} observations.")

        # Let's get the numpy arrays out of the panda frames
        #
        feature_values_pandas_frame = self._input_space_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)

        feature_values = feature_values_pandas_frame[self.input_dimension_names].to_numpy()
        target_values = target_values_pandas_frame[self.target_dimension_names].to_numpy()

        # Clean up state before fitting again
        self._observations_per_leaf = dict()

        self._regressor.fit(feature_values, target_values)

        # Now that we have fit the model we can augment our tree by computing the variance
        # TODO: this code can be easily optimized, but premature optimization is the root of all evil.
        node_indices = self._regressor.apply(feature_values)
        self.logger.debug(f"The resulting three has {len(node_indices)} leaf nodes.")

        for node_index, sample_target_value in zip(node_indices, target_values):
            observations_at_leaf = self._observations_per_leaf.get(node_index, [])
            observations_at_leaf.append(sample_target_value)
            self._observations_per_leaf[node_index] = observations_at_leaf

        # Now let's compute all predictions
        for node_index in self._observations_per_leaf:
            # First convert the observations to a numpy array.
            observations_at_leaf = np.array(self._observations_per_leaf[node_index])
            self._observations_per_leaf[node_index] = observations_at_leaf

            leaf_mean = np.mean(observations_at_leaf)
            leaf_sample_variance = np.var(observations_at_leaf, ddof=1) # ddof = delta degrees of freedom. We want sample variance.
            leaf_mean_variance = leaf_sample_variance / len(observations_at_leaf)

            # TODO: note that if we change the tree to fit a linear regression at each leaf, these predictions would have
            # to be computed in the .predict() function, though the slope and y-intersect could be computed here.
            self._mean_per_leaf[node_index] = leaf_mean
            self._mean_variance_per_leaf[node_index] = leaf_mean_variance
            self._sample_variance_per_leaf[node_index] = leaf_sample_variance
            self._count_per_leaf[node_index] = len(observations_at_leaf)

        self._trained = True
        self.last_refit_iteration_number = iteration_number

    @trace()
    def predict(self, feature_values_pandas_frame, include_only_valid_rows=True):
        self.logger.debug(f"Creating predictions for {len(feature_values_pandas_frame.index)} samples.")

        # dataframe column shortcuts
        is_valid_input_col = Prediction.LegalColumnNames.IS_VALID_INPUT.value
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        sample_var_col = Prediction.LegalColumnNames.SAMPLE_VARIANCE.value
        sample_size_col = Prediction.LegalColumnNames.SAMPLE_SIZE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        valid_rows_index = None
        features_df = None
        if self.trained:
            valid_features_df = self.input_space.filter_out_invalid_rows(original_dataframe=feature_values_pandas_frame, exclude_extra_columns=True)
            features_df = self._input_space_adapter.project_dataframe(valid_features_df, in_place=False)
            valid_rows_index = features_df.index

        predictions = Prediction(
            objective_name=self.target_dimension_names[0],
            predictor_outputs=self._PREDICTOR_OUTPUT_COLUMNS,
            dataframe_index=valid_rows_index
        )
        prediction_dataframe = predictions.get_dataframe()

        if valid_rows_index is not None and not valid_rows_index.empty:
            prediction_dataframe['leaf_node_index'] = self._regressor.apply(features_df.loc[valid_rows_index].to_numpy())
            prediction_dataframe[predicted_value_col] = prediction_dataframe['leaf_node_index'].map(self._mean_per_leaf)
            prediction_dataframe[predicted_value_var_col] = prediction_dataframe['leaf_node_index'].map(self._mean_variance_per_leaf)
            prediction_dataframe[sample_var_col] = prediction_dataframe['leaf_node_index'].map(self._sample_variance_per_leaf)
            prediction_dataframe[sample_size_col] = prediction_dataframe['leaf_node_index'].map(self._count_per_leaf)
            prediction_dataframe[dof_col] = prediction_dataframe[sample_size_col] - 1
            prediction_dataframe[is_valid_input_col] = True
            prediction_dataframe.drop(columns=['leaf_node_index'], inplace=True)

        predictions.validate_dataframe(prediction_dataframe)
        if not include_only_valid_rows:
            predictions.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)
        return predictions
