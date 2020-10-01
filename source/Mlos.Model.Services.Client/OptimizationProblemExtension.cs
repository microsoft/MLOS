// -----------------------------------------------------------------------
// <copyright file="OptimizationProblemExtension.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Linq;

namespace Mlos.Model.Services.Client
{
    /// <summary>
    /// OptimizationProblem extension class.
    /// </summary>
    internal static class OptimizationProblemExtension
    {
        /// <summary>
        /// Convert optimization problem to protobuf instance.
        /// </summary>
        /// <param name="optimizationProblem"></param>
        /// <returns></returns>
        internal static OptimizerService.OptimizationProblem ToOptimizerServiceOptimizationProblem(this OptimizationProblem optimizationProblem)
        {
            var optimizerOptimizationProblem = new OptimizerService.OptimizationProblem
            {
                ParameterSpace = new OptimizerService.Hypergrid
                {
                    HypergridJsonString = optimizationProblem.ParameterSpace.ToJson(),
                },

                ContextSpace = new OptimizerService.Hypergrid
                {
                    HypergridJsonString = optimizationProblem.ContextSpace != null ? optimizationProblem.ContextSpace.ToJson() : string.Empty,
                },

                ObjectiveSpace = new OptimizerService.Hypergrid
                {
                    HypergridJsonString = optimizationProblem.ObjectiveSpace.ToJson(),
                },
            };

            optimizerOptimizationProblem.Objectives.AddRange(optimizationProblem.Objectives.Select(r => r.ToOptimizerServiceObjective()));

            return optimizerOptimizationProblem;
        }
    }
}
