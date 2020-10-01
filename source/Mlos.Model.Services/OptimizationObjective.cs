// -----------------------------------------------------------------------
// <copyright file="OptimizationObjective.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Text.Json.Serialization;

namespace Mlos.Model.Services
{
    /// <summary>
    /// Each of the objectives in the ObjectiveSpace can be either maximized or minimized.
    /// OptimizationObjective assigns this direction to each objective.
    /// </summary>
    public class OptimizationObjective
    {
        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("minimize")]
        public bool Minimize { get; set; }
    }
}
