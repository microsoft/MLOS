// -----------------------------------------------------------------------
// <copyright file="ISimpleBayesianOptimizerFactory.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    public interface ISimpleBayesianOptimizerFactory
    {
        /// <summary>
        /// A factory to create SimpleBayesianOptimizers.
        /// </summary>
        /// <typeparam name="TOptimizationProblem"> Optimization problem type. </typeparam>
        /// <param name="optimizationProblem"> Optimization problem. </param>
        /// <returns></returns>
        public ISimpleBayesianOptimizerProxy CreateRemoteOptimizer<TOptimizationProblem>(TOptimizationProblem optimizationProblem)
            where TOptimizationProblem : IOptimizationProblem;
    }
}