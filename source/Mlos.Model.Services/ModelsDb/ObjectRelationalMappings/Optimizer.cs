// -----------------------------------------------------------------------
// <copyright file="Optimizer.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;

namespace Mlos.Model.Services.ModelsDb.ObjectRelationalMappings
{
    /// <summary>
    /// Maps the optimizer object to its representation in the ModelsDatabase.
    /// </summary>
    public class Optimizer
    {
        public enum RemoteOptimizerType
        {
            SimpleBayesianOptimizer,
        }

        /// <summary>
        /// Indicates the type of the remote optimizer. As we add more optimizers and evolve them
        /// this will have to become more complex: include versioning information, etc..
        /// </summary>
        public RemoteOptimizerType OptimizerType { get; set; }

        /// <summary>
        /// Optimization problem represented as a JsonString.
        /// </summary>
        public string OptimizationProblemJsonString { get; set; }

        public Guid? OptimizerId { get; set; }
    }
}
