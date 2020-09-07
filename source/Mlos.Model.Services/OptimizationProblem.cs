// -----------------------------------------------------------------------
// <copyright file="OptimizationProblem.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Text.Json.Serialization;

using Mlos.Core;
using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services
{
    /// <summary>
    /// Models and Optimization Problem which is generally comprized of Decision Variables (Parameter Space), Context Values (Context Space) and Objectives.
    /// In the future we may wish to extend this to include constraints as well, though right now most of them are expressed by the SimpleHypergrid class.
    /// </summary>
    public class OptimizationProblem : IOptimizationProblem
    {
        [JsonPropertyName("parameter_space")]
        public Hypergrid ParameterSpace { get; set; }

        [JsonPropertyName("context_space")]
        public Hypergrid ContextSpace { get; set; }

        [JsonPropertyName("objective_space")]
        public Hypergrid ObjectiveSpace { get; set; }

        [JsonPropertyName("objectives")]
        public List<OptimizationObjective> Objectives { get; }

        public OptimizationProblem()
        {
            Objectives = new List<OptimizationObjective>();
        }
    }
}
