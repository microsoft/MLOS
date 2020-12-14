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
    public partial class UIntArray
    {
        /// <summary>
        /// Number of elements in the array.
        /// </summary>
        internal uint Count;

        /// <summary>
        /// Elements array is dynamically allocated during the initialization.
        /// </summary>
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
    public partial struct AllocationEntry
    {
        internal uint NextEntryOffset;
        internal uint PrevEntryOffset;
    }

    /// <summary>
    /// Simple memory allocator.
    /// </summary>
    [CodegenType]
    public partial struct ArenaAllocator
    {
        /// <summary>
        /// Allocation alignment.
        /// </summary>
        public const int AllocationAlignment = 64;

        /// <summary>
        /// Offset to the allocator from the beginning of the memory region.
        /// </summary>
        internal int OffsetToAllocator;

        /// <summary>
        /// Maximum allowed allocation offset, equals to the memory region size.
        /// </summary>
        internal uint EndOffset;

        /// <summary>
        /// Total number of Allocations.
        /// </summary>
        internal uint AllocationCount;

        /// <summary>
        /// Offset to recently allocated object.
        /// </summary>
        internal uint LastOffset;

        /// <summary>
        /// Offset to available block of memory.
        /// </summary>
        internal uint FreeOffset;
    }
}
