// -----------------------------------------------------------------------
// <copyright file="OptimizationObjectiveExtension.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Model.Services.Client
{
    /// <summary>
    /// OptimizationObjective extension class.
    /// </summary>
    internal static class OptimizationObjectiveExtension
    {
        /// <summary>
        /// Convert optimization objective to protobuf instance.
        /// </summary>
        /// <param name="optimizationObjective"></param>
        /// <returns></returns>
        internal static OptimizerService.Objective ToOptimizerServiceObjective(this OptimizationObjective optimizationObjective)
        {
            return new OptimizerService.Objective
            {
                Minimize = optimizationObjective.Minimize,
                Name = optimizationObjective.Name,
            };
        }
    }
}
