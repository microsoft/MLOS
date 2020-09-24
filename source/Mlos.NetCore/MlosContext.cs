// -----------------------------------------------------------------------
// <copyright file="MlosContext.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

namespace Mlos.Core
{
    /// <summary>
    /// MlosContext encapsulates the shared memory regions for config and
    /// feedback for the Mlos.Agent when processing messages from smart
    /// components using their handlers.  It also includes a reference to the
    /// optimizer connection for those message handlers to use.
    /// </summary>
    /// <remarks>
    /// See Also: Mlos.Core/MlosContext.h for the corresponding C++ smart
    /// component side.
    /// </remarks>
    public static class MlosContext
    {
        /// <summary>
        /// Gets or sets the feedback channel instance.
        /// </summary>
        public static ISharedChannel FeedbackChannel { get; set; }

        public static ISharedConfigAccessor SharedConfigManager { get; set; }

        /// <summary>
        /// Gets or sets the connection to the optimizer.
        /// </summary>
        /// <remarks>
        /// Typically this will be assigned for a deployment specific situation
        /// (see Mlos.Agent.Server/MlosAgentServer.cs for an example) prior to
        /// starting the Mlos.Agent and made available for message handlers to
        /// use (see SmartCache.SettingsRegistry/AssemblyInitializer.cs for an
        /// example).
        /// </remarks>
        public static IOptimizerFactory OptimizerFactory { get; set; }
    }
}
