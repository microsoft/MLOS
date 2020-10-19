// -----------------------------------------------------------------------
// <copyright file="ExperimentSessionManager.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

using Mlos.Core;

namespace Mlos.Agent
{
    public class ExperimentSessionManager
    {
        public static Dictionary<string, string> AssemblyPathByName = new Dictionary<string, string>();

        private string loadedExperimentName;
        private Assembly loadedExperimentAssembly;
        private dynamic experiment;

        private readonly MlosContext mlosContext;

        /// <summary>
        /// Initializes a new instance of the <see cref="ExperimentSessionManager"/> class.
        /// </summary>
        /// <param name="mlosContext"></param>
        public ExperimentSessionManager(MlosContext mlosContext)
        {
            this.mlosContext = mlosContext;
        }

        /// <summary>
        /// Load the experiment assembly.
        /// </summary>
        /// <param name="experimentAssemblyPath"></param>
        /// <remarks>
        /// #TODO, this is not complete code, only load experiment is supported.
        /// </remarks>
        public void LoadExperiment(string experimentAssemblyPath)
        {
            //
            string experimentName = Path.GetFileNameWithoutExtension(experimentAssemblyPath);

            loadedExperimentAssembly = Assembly.LoadFrom(experimentAssemblyPath);

            Type experimentType = loadedExperimentAssembly.GetTypes().Single(type => typeof(ExperimentSession).IsAssignableFrom(type));

            experiment = Activator.CreateInstance(type: experimentType, args: new[] { mlosContext });
        }

        public bool StartExperiment(int numRandomIterations, int numGuidedIterations)
        {
            experiment.Start(numRandomIterations, numGuidedIterations);
            return true;
        }

        public IEnumerable<string> AvailableExperimentAssemblies()
        {
            return AssemblyPathByName.Keys;
        }

        public string GetOptimizerId()
        {
            return experiment.GetOptimizerId();
        }

        public string GetParameterSpace(string experimentName)
        {
            if (loadedExperimentName == experimentName)
            {
                return experiment.GetParameterSpace();
            }
            else
            {
                return string.Empty;
            }
        }

        public int GetRemainingRandomIterations()
        {
            return experiment.RemainingRandomIterations;
        }

        public int GetRemainingGuidedIterations()
        {
            return experiment.RemainingGuidedIterations;
        }
    }
}
