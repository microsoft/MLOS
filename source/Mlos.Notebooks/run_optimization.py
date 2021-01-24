from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory

def run_optimization(optimization_problem, optimizer_config, objective_function, run_id, num_iterations):
    optimizer = BayesianOptimizerFactory().create_local_optimizer(
        optimization_problem=optimization_problem,
        optimizer_config=optimizer_config
    )
    
    for i in range(num_iterations):
        print(f"[{run_id}][{i+1}/{num_iterations}]")
        suggestion = optimizer.suggest()
        values = objective_function.evaluate_point(suggestion)
        optimizer.register(suggestion.to_dataframe(), values.to_dataframe())
    return optimizer