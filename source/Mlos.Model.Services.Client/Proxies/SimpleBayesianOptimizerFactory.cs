// -----------------------------------------------------------------------
// <copyright file="SimpleBayesianOptimizerFactory.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Mlos.Core;
using Mlos.Model.Services.ModelsDb;
using Mlos.Model.Services.ModelsDb.ObjectRelationalMappings;
using Mlos.Model.Services.Spaces;
using Mlos.Model.Services.Spaces.JsonConverters;

namespace Mlos.Model.Services.Client.Proxies
{
    /// <summary>
    /// Produces SimpleBayesianOptimizerProxy objects.
    ///
    /// This factory can later be generalized to produce proxies to other types of optimizers.
    ///
    /// </summary>
    public class SimpleBayesianOptimizerFactory : ISimpleBayesianOptimizerFactory
    {
        private static readonly JsonSerializerOptions JsonOptions = new JsonSerializerOptions
        {
            Converters =
            {
                new JsonStringEnumConverter(),
                new DimensionJsonConverter(),
                new SimpleHypergridJsonConverter(),
            },
        };

        private readonly ModelsDatabase modelsDatabase;

        public SimpleBayesianOptimizerFactory(ModelsDatabase modelsDatabase)
        {
            this.modelsDatabase = modelsDatabase;
        }

        /// <summary>
        /// Creates an instance of a SimpleBayesianOptimizer and registers it with the models database.
        /// </summary>
        /// <param name="optimizationProblem"></param>
        /// <typeparam name="TOptimizationProblem"> . </typeparam>
        /// <returns></returns>
        public ISimpleBayesianOptimizerProxy CreateRemoteOptimizer<TOptimizationProblem>(TOptimizationProblem optimizationProblem)
            where TOptimizationProblem : IOptimizationProblem
        {
            Optimizer optimizer = new Optimizer
            {
                OptimizerType = Optimizer.RemoteOptimizerType.SimpleBayesianOptimizer,
                OptimizationProblemJsonString = JsonSerializer.Serialize(optimizationProblem, JsonOptions),
            };

            modelsDatabase.CreateNewOptimizer(optimizer);
            if (optimizer.OptimizerId is null)
            {
                // Failed to create a new optimizer.
                //
                return null;
            }

            return new SimpleBayesianOptimizerProxy(modelsDatabase, (OptimizationProblem)(object)optimizationProblem, optimizer.OptimizerId);
        }
    }
}
