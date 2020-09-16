// -----------------------------------------------------------------------
// <copyright file="BayesianOptimizerFactory.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using Grpc.Net.Client;

using Mlos.Core;
using Mlos.OptimizerService;

using MlosOptimizerService = Mlos.OptimizerService.OptimizerService;

namespace Mlos.Model.Services.Client.BayesianOptimizer
{
    /// <summary>
    /// Produces BayesianOptimizerProxy objects.
    ///
    /// This factory can later be generalized to produce proxies to other types of optimizers.
    ///
    /// </summary>
    public class BayesianOptimizerFactory : IOptimizerFactory
    {
        private Uri optimizerAddressUri;

        public BayesianOptimizerFactory(Uri optimizerAddressUri)
        {
            this.optimizerAddressUri = optimizerAddressUri;
        }

        /// <summary>
        /// Creates an instance of a BayesianOptimizer and registers it with the models database.
        /// </summary>
        /// <param name="optimizationProblem"></param>
        /// <typeparam name="TOptimizationProblem"> . </typeparam>
        /// <returns></returns>
        public IOptimizerProxy CreateRemoteOptimizer<TOptimizationProblem>(TOptimizationProblem optimizationProblem)
            where TOptimizationProblem : IOptimizationProblem
        {
            // Check if we support this instance of optimization problem.
            //
            if (typeof(TOptimizationProblem) == typeof(OptimizationProblem))
            {
                return CreateRemoteOptimizer((OptimizationProblem)(object)optimizationProblem);
            }

            // Unknown, unsupported optimization problem.
            //
            throw new ArgumentException("Unsupported optimization problem type", nameof(optimizationProblem));
        }

        private BayesianOptimizerProxy CreateRemoteOptimizer(OptimizationProblem optimizationProblem)
        {
            GrpcChannel channel = GrpcChannel.ForAddress(optimizerAddressUri);
            var client = new MlosOptimizerService.OptimizerServiceClient(channel);

            OptimizerHandle optimizerHandle = client.CreateOptimizer(
                new CreateOptimizerRequest
                {
                    OptimizationProblem = optimizationProblem.ToOptimizerServiceOptimizationProblem(),
                    OptimizerConfig = string.Empty,
                });

            return new BayesianOptimizerProxy(client, optimizerHandle);
        }
    }
}
