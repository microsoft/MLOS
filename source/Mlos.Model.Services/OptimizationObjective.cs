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
        /// <summary>
        /// Gets or sets optimization objective name.
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether the objective is meant to be either maximized or minimized.
        /// </summary>
        public bool Minimize { get; set; }

        public OptimizationObjective(string name, bool minimize)
        {
            Name = name;
            Minimize = minimize;
        }
    }
}
