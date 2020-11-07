// -----------------------------------------------------------------------
// <copyright file="ArenaAllocatorExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;

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
        /// <param name="firstAllocationOffset"></param>
        public static void InitializeArenaAllocator(
            this ArenaAllocator allocator,
            MemoryRegion memoryRegion,
            int firstAllocationOffset)
        {
            // Store offset to the allocator itself.
            //
            allocator.OffsetToAllocator = (int)allocator.Buffer.Offset(memoryRegion.Buffer);

            allocator.FirstAllocationOffset = Utils.Align((uint)firstAllocationOffset, 256);
            allocator.AllocationBlockSize = (uint)memoryRegion.MemoryRegionSize - allocator.FirstAllocationOffset;

            allocator.FreeOffset = allocator.FirstAllocationOffset;
            allocator.AllocationCount = 0;
            allocator.LastAllocatedOffset = 0;
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

            if (allocator.FreeOffset + size >= allocator.AllocationBlockSize + allocator.FirstAllocationOffset)
            {
                throw new OutOfMemoryException();
            }

            // Update the address.
            //
            uint offset = allocator.FreeOffset;

            // Update memory region properties.
            //
            allocator.FreeOffset += (uint)Utils.Align(size, 64);
            allocator.AllocationCount++;

            IntPtr memoryRegionPtr = allocator.Buffer - allocator.OffsetToAllocator;

            // Update last allocated entry.
            //
            if (allocator.LastAllocatedOffset != 0)
            {
                AllocationEntry lastAllocationEntry = new AllocationEntry
                {
                    Buffer = memoryRegionPtr + (int)allocator.LastAllocatedOffset,
                };

                lastAllocationEntry.NextEntryOffset = offset;
            }

            // Update current allocated entry.
            //
            AllocationEntry allocationEntry = new AllocationEntry
            {
                Buffer = memoryRegionPtr + (int)offset,
            };

            allocationEntry.PrevEntryoffset = allocator.LastAllocatedOffset;

            allocator.LastAllocatedOffset = offset;

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

            T codegenProxy = new T() { Buffer = allocationEntry.Buffer + (int)default(AllocationEntry).CodegenTypeSize() };

            return codegenProxy;
        }
    }
}
