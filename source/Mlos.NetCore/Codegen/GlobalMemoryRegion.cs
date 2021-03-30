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
    public partial struct GlobalMemoryRegion
    {
        /// <summary>
        /// Default memory size.
        /// </summary>
        public const int GlobalSharedMemorySize = 65536;

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
        /// Global counter for memory regions.
        /// </summary>
        internal ushort GlobalMemoryRegionIndex;

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

    /// <summary>
    /// Registered shared memory region.
    /// </summary>
    [CodegenType]
    public partial struct RegisteredMemoryRegionConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal MemoryRegionId MemoryRegionId;

        /// <summary>
        /// Name of the shared memory map.
        /// </summary>
        internal StringPtr MemoryMapName;

        /// <summary>
        /// Size of the memory region.
        /// </summary>
        internal ulong MemoryRegionSize;
    }

    /// <summary>
    /// Registered named event in given memory region.
    /// </summary>
    [CodegenType]
    public partial struct RegisteredNamedEventConfig
    {
        [ScalarSetting(isPrimaryKey: true)]
        internal MemoryRegionId MemoryRegionId;

        /// <summary>
        /// Name of the event.
        /// </summary>
        internal StringPtr EventName;
    }

    /// <summary>
    /// Message used to exchange file descriptor via Unix domain socket.
    /// </summary>
    [CodegenType]
    public partial struct FileDescriptorExchangeMessage
    {
        /// <summary>
        /// Memory region identifier.
        /// </summary>
        public MemoryRegionId MemoryRegionId;
    }
}
