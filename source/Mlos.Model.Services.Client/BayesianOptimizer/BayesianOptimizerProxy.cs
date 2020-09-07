// -----------------------------------------------------------------------
// <copyright file="BayesianOptimizerProxy.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Linq;
using Mlos.Core;
using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services.Client.BayesianOptimizer
{
    /// <summary>
    /// A proxy to a BayesianOptimizer executing within the Mlos.Model.Services.
    /// </summary>
    public class BayesianOptimizerProxy : IOptimizerProxy
    {
        private OptimizerService.OptimizerService.OptimizerServiceClient client;

        private OptimizerService.OptimizerHandle optimizerHandle;

        public BayesianOptimizerProxy(OptimizerService.OptimizerService.OptimizerServiceClient client, OptimizerService.OptimizerHandle optimizerHandle)
        {
            this.client = client;
            this.optimizerHandle = optimizerHandle;
        }

        /// <inheritdoc/>
        public IOptimizationProblem GetOptimizationProblem()
        {
            OptimizerService.OptimizerInfo optimizerInfo = client.GetOptimizerInfo(optimizerHandle);

            Hypergrid contextSpace = Hypergrid.FromJson(optimizerInfo.OptimizationProblem.ContextSpace?.HypergridJsonString);
            Hypergrid objectiveSpace = Hypergrid.FromJson(optimizerInfo.OptimizationProblem.ObjectiveSpace?.HypergridJsonString);
            Hypergrid parameterSpace = Hypergrid.FromJson(optimizerInfo.OptimizationProblem.ParameterSpace?.HypergridJsonString);

            var optimizationProblem = new OptimizationProblem
            {
                ContextSpace = contextSpace,
                ObjectiveSpace = objectiveSpace,
                ParameterSpace = parameterSpace,
            };

            // Add optimization objectives.
            //
            optimizationProblem.Objectives.AddRange(
                optimizerInfo.OptimizationProblem.Objectives.Select(r =>
                    new OptimizationObjective
                    {
                        Minimize = r.Minimize,
                        Name = r.Name,
                    }));

            return optimizationProblem;
        }

        /// <inheritdoc/>
        public void Register(string paramsJsonString, string objectiveName, double objectiveValue)
        {
            client.RegisterObservation(
                new OptimizerService.RegisterObservationRequest
                {
                    OptimizerHandle = optimizerHandle,
                    Observation = new OptimizerService.Observation
                    {
                        Features = new OptimizerService.Features
                        {
                            FeaturesJsonString = paramsJsonString,
                        },
                        ObjectiveValues = new OptimizerService.ObjectiveValues
                        {
                            ObjectiveValuesJsonString = @$"{{""{objectiveName}"": {objectiveValue} }}",
                        },
                    },
                });

            Console.WriteLine($"Register {paramsJsonString} {objectiveName} = {objectiveValue}");
        }

        /// <inheritdoc/>
        public string Suggest(bool random = false)
        {
            OptimizerService.ConfigurationParameters configurationParameters = client.Suggest(
                new OptimizerService.SuggestRequest
                {
                    OptimizerHandle = optimizerHandle,
                    Context = new OptimizerService.Context
                    {
                        ContextJsonString = string.Empty,
                    },
                    Random = random,
                });

            string suggestedParameter = configurationParameters.ParametersJsonString;
            Console.WriteLine($"Suggest {random} {suggestedParameter}");
            return suggestedParameter;
        }
    }
}
