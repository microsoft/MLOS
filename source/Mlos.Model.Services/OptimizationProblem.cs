// -----------------------------------------------------------------------
// <copyright file="OptimizationProblem.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

using Mlos.Core;
using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services
{
    /// <summary>
    /// Models and Optimization Problem which is generally comprised of Decision Variables (Parameter Space), Context Values (Context Space) and Objectives.
    /// In the future we may wish to extend this to include constraints as well, though right now most of them are expressed by the SimpleHypergrid class.
    /// </summary>
    public class OptimizationProblem : IOptimizationProblem
    {
        public Hypergrid ParameterSpace { get; set; }

        public Hypergrid ContextSpace { get; set; }

        public Hypergrid ObjectiveSpace { get; set; }

        public List<OptimizationObjective> Objectives { get; }

        /// <summary>
        /// Initializes a new instance of the <see cref="OptimizationProblem"/> class.
        /// Ctor.
        /// </summary>
        public OptimizationProblem()
        {
            Objectives = new List<OptimizationObjective>();
        }

        public OptimizationProblem(Hypergrid parameterSpace, Hypergrid objectiveSpace, IEnumerable<OptimizationObjective> objectives)
        {
            ParameterSpace = parameterSpace;
            ObjectiveSpace = objectiveSpace;
            Objectives = objectives.ToList();
        }

        public OptimizationProblem(Hypergrid parameterSpace, Hypergrid contextSpace, Hypergrid objectiveSpace, IEnumerable<OptimizationObjective> objectives)
        {
            ParameterSpace = parameterSpace;
            ContextSpace = contextSpace;
            ObjectiveSpace = objectiveSpace;
            Objectives = objectives.ToList();
        }
    }
}
