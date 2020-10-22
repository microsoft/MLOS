// -----------------------------------------------------------------------
// <copyright file="GlobalMemoryRegion.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;
using Mlos.SettingsSystem.StdTypes;

namespace Mlos.Core.Internal
{
    [CodegenType]
    internal partial struct GlobalMemoryRegion
    {
        /// <summary>
        /// Memory region header.
        /// </summary>
        internal MemoryRegion MemoryHeader;

        /// <summary>
        /// Control channel synchronization object.
        /// </summary>
        internal ChannelSynchronization ControlChannelSynchronization;

        /// <summary>
        /// Control channel synchronization object.
        /// </summary>
        internal ChannelSynchronization FeedbackChannelSynchronization;

        /// <summary>
        /// Gets or sets information how many processes are using the global memory region.
        /// </summary>
        internal AtomicUInt32 AttachedProcessesCount;

        /// <summary>
        /// Total number of regions.
        /// </summary>
        internal uint TotalMemoryRegionCount;

        /// <summary>
        /// Number of registered settings assembly.
        /// </summary>
        internal AtomicUInt32 RegisteredSettingsAssemblyCount;

        /// <summary>
        /// Shared configurations stored in the lookup table.
        /// </summary>
        /// <remarks>
        /// In the global memory region we keep the information about:
        /// - registered settings assembly,
        /// - registered shared config memory regions.
        /// </remarks>
        internal SharedConfigDictionary SharedConfigDictionary;
    }
}
