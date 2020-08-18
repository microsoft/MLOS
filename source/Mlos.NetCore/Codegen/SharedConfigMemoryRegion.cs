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
    /// Memory region holding components configurations.
    /// </summary>
    [CodegenType]
    internal partial class SharedConfigMemoryRegion
    {
        /// <summary>
        /// Memory region header.
        /// </summary>
        internal MemoryRegion MemoryHeader;

        /// <summary>
        /// Memory allocator.
        /// </summary>
        internal ArenaAllocator Allocator;

        /// <summary>
        /// Offset to the array of configs (offsets to configs).
        /// </summary>
        internal uint ConfigsArrayOffset;
    }

    [CodegenMessage]
    internal partial struct RegisterSharedConfigMemoryRegionRequestMessage
    {
        internal uint MemoryRegionId;
    }
}
