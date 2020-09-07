// -----------------------------------------------------------------------
// <copyright file="IOptimizerFactory.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    public interface IOptimizerFactory
    {
        /// <summary>
        /// A factory to create SimpleBayesianOptimizers.
        /// </summary>
        /// <typeparam name="TOptimizationProblem">Optimization problem type.</typeparam>
        /// <param name="optimizationProblem">Instance of optimization problem. </param>
        /// <returns>Instance of optimizer proxy.</returns>
        public IOptimizerProxy CreateRemoteOptimizer<TOptimizationProblem>(TOptimizationProblem optimizationProblem)
            where TOptimizationProblem : IOptimizationProblem;
    }
}
