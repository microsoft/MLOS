// -----------------------------------------------------------------------
// <copyright file="SharedConfigMemoryRegion.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace Mlos.Core.Internal
{
    /// <summary>
    /// Memory region where the target process creates the components' shared configuration.
    /// </summary>
    [CodegenType]
    internal partial struct SharedConfigMemoryRegion
    {
        /// <summary>
        /// Memory region header.
        /// </summary>
        internal MemoryRegion MemoryHeader;

        /// <summary>
        /// Shared configurations stored in the lookup table.
        /// </summary>
        internal SharedConfigDictionary SharedConfigDictionary;
    }

    /// <summary>
    /// Structure keeps a dictionary of the shared configs.
    /// Contains an allocator, the config offsets.
    /// </summary>
    /// <remarks>
    /// Shared configs are allocated in the memory region using the allocator.
    /// First, we allocate array of offsets that will be used as an open hashmap.
    /// Because we are allocating in the shared memory region, we are using offsets (not pointers).
    /// </remarks>
    [CodegenType]
    internal partial struct SharedConfigDictionary
    {
        /// <summary>
        /// Memory allocator.
        /// </summary>
        internal ArenaAllocator Allocator;

        /// <summary>
        /// Offset to the array of configs (offsets to configs).
        /// </summary>
        /// <remarks>
        /// The offset is calculated from the beginning of the dictionary structure.
        /// </remarks>
        internal uint OffsetToConfigsArray;
    }

    /// <summary>
    /// Message is used to register shared config memory with the agent.
    /// When the target process creates a shared memory region, it sends the message
    /// to the agent to register the memory region as a shared config memory.
    /// </summary>
    [CodegenMessage]
    internal partial struct RegisterSharedConfigMemoryRegionRequestMessage
    {
        internal uint MemoryRegionId;
    }
}
