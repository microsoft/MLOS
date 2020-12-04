// -----------------------------------------------------------------------
// <copyright file="ExperimentSession.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    /// <summary>
    /// Experiment session base class.
    /// </summary>
    public abstract class ExperimentSession
    {
        private readonly MlosContext mlosContext;

        /// <summary>
        /// Initializes a new instance of the <see cref="ExperimentSession"/> class.
        /// </summary>
        /// <param name="mlosContext"></param>
        public ExperimentSession(MlosContext mlosContext)
        {
            this.mlosContext = mlosContext;
        }

        /// <summary>
        /// Gets MlosContext associated with the experiment session.
        /// </summary>
        public MlosContext MlosContext => mlosContext;
    }
}
