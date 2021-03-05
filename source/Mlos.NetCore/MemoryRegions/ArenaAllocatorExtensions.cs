// -----------------------------------------------------------------------
// <copyright file="ArenaAllocatorExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;

using MlosInternal = Mlos.Core.Internal;

namespace Proxy.Mlos.Core.Internal
{
    /// <summary>
    /// Extension method class for ArenaAllocator structure.
    /// </summary>
    public static class ArenaAllocatorExtensions
    {
        /// <summary>
        /// Initializes the arena allocator stored in the memory region.
        /// </summary>
        /// <param name="allocator"></param>
        /// <param name="memoryRegion"></param>
        /// <param name="memoryRegionHeaderSize"></param>
        public static void InitializeArenaAllocator(
            this ArenaAllocator allocator,
            MemoryRegion memoryRegion,
            int memoryRegionHeaderSize)
        {
            // Store offset to the allocator itself.
            //
            allocator.OffsetToAllocator = (int)allocator.Buffer.Offset(memoryRegion.Buffer);

            allocator.EndOffset = (uint)memoryRegion.MemoryRegionSize;

            allocator.FreeOffset = Utils.Align((uint)memoryRegionHeaderSize, MlosInternal.ArenaAllocator.AllocationAlignment);
            allocator.AllocationCount = 0;
            allocator.LastOffset = 0;
        }

        /// <summary>
        /// Allocates the memory in the shared memory region.
        /// </summary>
        /// <param name="allocator"></param>
        /// <param name="size"></param>
        /// <returns></returns>
        public static AllocationEntry Allocate(this ArenaAllocator allocator, ulong size)
        {
            size += default(AllocationEntry).CodegenTypeSize();

            if (allocator.FreeOffset + size >= allocator.EndOffset)
            {
                throw new OutOfMemoryException();
            }

            // Update the address.
            //
            uint offset = allocator.FreeOffset;

            // Update memory region properties.
            //
            allocator.FreeOffset += (uint)Utils.Align(size, MlosInternal.ArenaAllocator.AllocationAlignment);
            allocator.AllocationCount++;

            IntPtr memoryRegionPtr = allocator.Buffer - allocator.OffsetToAllocator;

            // Update last allocated entry.
            //
            if (allocator.LastOffset != 0)
            {
                var lastAllocationEntry = new AllocationEntry
                {
                    Buffer = memoryRegionPtr + (int)allocator.LastOffset,
                    NextEntryOffset = offset,
                };
            }

            // Update current allocated entry.
            //
            var allocationEntry = new AllocationEntry
            {
                Buffer = memoryRegionPtr + (int)offset,
                PrevEntryOffset = allocator.LastOffset,
            };

            allocator.LastOffset = offset;

            return allocationEntry;
        }

        /// <summary>
        /// Allocates the memory for the given type in the shared memory region.
        /// </summary>
        /// <typeparam name="T">CodegenProxyType of the allocated object.</typeparam>
        /// <param name="allocator">Allocator instance.</param>
        /// <returns></returns>
        public static T Allocate<T>(this ArenaAllocator allocator)
           where T : ICodegenProxy, new()
        {
            AllocationEntry allocationEntry = allocator.Allocate(default(T).CodegenTypeSize());

            T codegenProxy = new T { Buffer = allocationEntry.Buffer + (int)default(AllocationEntry).CodegenTypeSize() };

            return codegenProxy;
        }
    }
}
