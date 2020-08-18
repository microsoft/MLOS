// -----------------------------------------------------------------------
// <copyright file="SimpleBayesianOptimizerExecutionContext.cs" company="Microsoft Corporation">
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

namespace Mlos.Model.Services.Client.Proxies
{
    /// <summary>
    /// Describes the context in which the SimpleBayesianOptimizer rpc should be executed.
    /// </summary>
    public class SimpleBayesianOptimizerExecutionContext
    {
        [JsonPropertyName("optimizer_id")]
        public Guid? OptimizerId { get; set; }

        [JsonPropertyName("model_versions")]
        public List<int> ModelVersions { get; }

        public SimpleBayesianOptimizerExecutionContext()
        {
            ModelVersions = new List<int>();
        }
    }
}
