#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import codecs
import json
import pickle

from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder, HypergridJsonDecoder

from mlos.MlosOptimizationServices.Distributable import Distributable, remotely_executable
from mlos.MlosOptimizationServices.ModelsDatabase.Relations import Optimizer, SimpleModel

from .OptimizationProblem import OptimizationProblem, objective_from_dict
from .SimpleBayesianOptimizer import SimpleBayesianOptimizer, SimpleBayesianOptimizerConfig


class DistributableSimpleBayesianOptimizer(SimpleBayesianOptimizer, Distributable):
    """ A distributatble simple bayesian optimizer.

    The key idea here is that if the self.execute_remotely flag is set to True, methods decorated with @remotely_executable() will be invoked differently.

    Specifically: the @remotely_executable() wrapper serializes the execution context and the arguments of the function call and submits it over RPC to
    be executed elsewhere (perhaps on a machine that has more suitable hardware). The wrapper then monitors the state of
    the rpc and returns when it is complete.

    """

    @classmethod
    def create_remote_model(
            cls,
            models_database,
            optimization_problem,
            optimizer_config=None
    ):
        """ Factory method to create a remote model.

        :param search_space:
        :param utility_function_name:
        :param kappa:
        :param xi:
        :param minimize:
        :return:
        """
        if optimizer_config is None:
            optimizer_config = SimpleBayesianOptimizerConfig()

        db_optimizer_object = Optimizer(
            optimizer_type="SimpleBayesianOptimizer",
            optimizer_config=json.dumps(optimizer_config.to_dict(), cls=HypergridJsonEncoder),
            optimization_problem=json.dumps(optimization_problem.to_dict(), cls=HypergridJsonEncoder), # TODO: rename this field
        )
        newly_minted_optimizer = models_database.create_optimizer(db_optimizer_object)
        return DistributableSimpleBayesianOptimizer(
            models_database=models_database,
            optimizer_id=newly_minted_optimizer.optimizer_id,
            execute_remotely=True,
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

    def __init__(
            self,
            models_database=None,
            optimizer_id=None,
            model_id=None,
            model_version=0,
            execute_remotely=False,
            optimization_problem: OptimizationProblem = None,
            optimizer_config: SimpleBayesianOptimizerConfig = None
    ):
        Distributable.__init__(self, execute_remotely=execute_remotely)
        if optimizer_config is None:
            optimizer_config = SimpleBayesianOptimizerConfig()  # Default config
        SimpleBayesianOptimizer.__init__(self, optimization_problem, optimizer_config)

        self.models_database = models_database
        self._optimizer_id = optimizer_id
        self._model_id = model_id
        self._model_version = model_version

    @property
    def db_optimimizer_object(self):
        db_simple_model_object = SimpleModel(
            optimizer_id=self._optimizer_id,
            model_type='ScikitGaussianProcessRegressor',
            model_id=self._model_id,
            model_version=self._model_version,
            model_hypergrid=json.dumps(self.optimization_problem.feature_space, cls=HypergridJsonEncoder),
            serialized_model=codecs.encode(pickle.dumps(self._optimizer), "base64").decode()
        )

        db_optimizer_object = Optimizer(
            optimizer_id=self._optimizer_id,
            optimizer_type="SimpleBayesianOptimizer",
            optimizer_config=json.dumps(self._optimizer_config.to_dict(), cls=HypergridJsonEncoder),
            optimization_problem=json.dumps(self.optimization_problem.to_dict(), cls=HypergridJsonEncoder),
            optimizer_focused_hypergrid=json.dumps(self._focused_parameter_space, cls=HypergridJsonEncoder),
            models=[db_simple_model_object],
            registered_params_combos=json.dumps(self._registered_param_combos, cls=HypergridJsonEncoder)
        )
        return db_optimizer_object

    def get_execution_context(self):
        return {
            "optimizer_id": self._optimizer_id,
            "model_versions": [self._model_version]
        }

    @classmethod
    def restore_from_execution_context(cls, execution_context, models_database=None):
        assert models_database is not None

        if not execution_context.get('model_versions', []):
            execution_context['model_versions'] = [0]  # Default to the latest version

        db_optimizer_object = Optimizer(
            optimizer_id=execution_context['optimizer_id'],
            models=[SimpleModel(model_version=model_version) for model_version in execution_context['model_versions']]
        )
        db_optimizer_object = models_database.get_optimizer_state(db_optimizer_object)

        if db_optimizer_object.optimizer_config is not None:
            optimizer_config_dict = json.loads(db_optimizer_object.optimizer_config, cls=HypergridJsonDecoder)
            optimizer_config = SimpleBayesianOptimizerConfig(**optimizer_config_dict)
        else:
            optimizer_config = SimpleBayesianOptimizerConfig()
            db_optimizer_object.optimizer_config = json.dumps(optimizer_config.to_dict(), cls=HypergridJsonEncoder)
            models_database.update_optimizer_config(db_optimizer_object)

        optimization_problem_dict = json.loads(db_optimizer_object.optimization_problem, cls=HypergridJsonDecoder)
        optimization_problem = OptimizationProblem(
            parameter_space=optimization_problem_dict["parameter_space"],
            objective_space=optimization_problem_dict["objective_space"],
            objectives=[objective_from_dict(objective_dict) for objective_dict in optimization_problem_dict["objectives"]],
            context_space=optimization_problem_dict["context_space"]
        )
        optimizer = DistributableSimpleBayesianOptimizer(
            models_database=models_database,
            optimizer_id=db_optimizer_object.optimizer_id,
            model_id=db_optimizer_object.models[0].model_id if db_optimizer_object.models else None,
            model_version=db_optimizer_object.models[0].model_version if db_optimizer_object.models else None,
            execute_remotely=False,
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

        if db_optimizer_object.registered_params_combos is not None:
            # pylint: disable=protected-access
            optimizer._registered_param_combos = json.loads(db_optimizer_object.registered_params_combos, cls=HypergridJsonDecoder)
        if db_optimizer_object.optimizer_focused_hypergrid is not None:
            optimizer.focus(subspace=json.loads(db_optimizer_object.optimizer_focused_hypergrid, cls=HypergridJsonDecoder))
        serialized_model = db_optimizer_object.models[0].serialized_model
        if serialized_model is not None:
            # pylint: disable=protected-access
            optimizer._optimizer = pickle.loads(codecs.decode(serialized_model.encode(), "base64"))
        return optimizer


    @remotely_executable()
    def suggest(self, random=False, context=None): # pylint: disable=redefined-outer-name
        return super().suggest(random=random, context=context)


    @remotely_executable()
    def register(self, params, target_value):
        return super().register(params=params, target_value=target_value)

    @remotely_executable()
    def predict(self, feature_values_pandas_frame, t=None):
        return super().predict(feature_values_pandas_frame=feature_values_pandas_frame, t=t)

    @remotely_executable()
    def optimum(self, stay_focused=False):
        return super().optimum(stay_focused=stay_focused)

    @remotely_executable()
    def focus(self, subspace):
        return super().focus(subspace=subspace)

    @remotely_executable()
    def reset_focus(self):
        return super().reset_focus()
