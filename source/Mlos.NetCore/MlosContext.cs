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
    /// MlosContext.
    /// </summary>
    public static class MlosContext
    {
        /// <summary>
        /// Gets or sets the feedback channel instance.
        /// </summary>
        public static ISharedChannel FeedbackChannel { get; set; }

        public static ISharedConfigAccessor SharedConfigManager { get; set; }

        public static IOptimizerFactory OptimizerFactory { get; set; }
    }
}
