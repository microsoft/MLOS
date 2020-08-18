// -----------------------------------------------------------------------
// <copyright file="ArenaAllocator.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using Mlos.SettingsSystem.Attributes;

namespace Mlos.Core.Internal
{
    [CodegenType]
    internal partial class UIntArray
    {
        internal uint Count;

        [FixedSizeArray(1)]
        internal readonly uint[] Elements;
    }

    /// <summary>
    /// Allocation entry.
    /// </summary>
    /// <remarks>
    /// #TODO move to ArenaAllocator allocator.
    /// </remarks>
    [CodegenType]
    internal partial struct AllocationEntry
    {
        internal uint NextEntryOffset;
        internal uint PrevEntryoffset;
    }

    /// <summary>
    /// Simple memory allocator.
    /// </summary>
    [CodegenType]
    internal partial struct ArenaAllocator
    {
        /// <summary>
        /// Size of the memory we are allocating from.
        /// </summary>
        internal uint AllocationBlockSize;

        /// <summary>
        /// Offset to start of allocation block in the memory regtion.
        /// </summary>
        internal uint AllocationBlockOffset;

        /// <summary>
        /// Total number of Allocations.
        /// </summary>
        internal uint AllocationCount;

        /// <summary>
        /// Offset to recently allocated object.
        /// </summary>
        internal uint LastAllocatedOffset;

        /// <summary>
        /// Offset to available block of memory.
        /// </summary>
        internal uint FreeOffset;
    }
}
