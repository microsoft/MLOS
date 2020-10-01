// -----------------------------------------------------------------------
// <copyright file="IOptimizerProxy.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    public interface IOptimizerProxy
    {
        /// <summary>
        /// Registers a (config, target) tuple with the optimizer.
        /// </summary>
        /// <param name="paramsJsonString"></param>
        /// <param name="objectiveName"></param>
        /// <param name="objectiveValue"></param>
        void Register(string paramsJsonString, string objectiveName, double objectiveValue);

        /// <summary>
        /// Gets the optimizer current problem.
        /// </summary>
        /// <returns></returns>
        IOptimizationProblem GetOptimizationProblem();

        /// <summary>
        /// Suggests a set of parameters to try.
        ///
        /// Specifically, it submits a remote procedure call request for a remote optimizer to suggest a set of parameters to try.
        /// It then waits for that rpc to complete and returns the result.
        ///
        /// </summary>
        /// <param name="random"></param>
        /// <returns>JSON string with the result. TODO: make it a generic to return a config belonging to a given search space.</returns>
        string Suggest(bool random = false);
    }
}
