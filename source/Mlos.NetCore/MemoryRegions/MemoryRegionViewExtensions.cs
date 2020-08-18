// -----------------------------------------------------------------------
// <copyright file="MemoryRegionViewExtensions.cs" company="Microsoft Corporation">
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
    /// Memory region extension methods.
    /// </summary>
    public static class MemoryRegionViewExtensions
    {
        /// <summary>
        /// Initialize SharedChannelMemoryRegion.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <returns></returns>
        public static GlobalMemoryRegion InitializeMemoryRegion(this GlobalMemoryRegion globalMemoryRegion)
        {
            // Initialize properties.
            //
            globalMemoryRegion.TotalMemoryRegionCount = 1;

            globalMemoryRegion.RegisteredSettingsAssemblyCount.Store(1);

            return globalMemoryRegion;
        }

        /// <summary>
        /// Initialize SharedConfigMemoryRegion.
        /// </summary>
        /// <param name="sharedConfigMemoryRegion"></param>
        /// <returns></returns>
        public static SharedConfigMemoryRegion InitializeMemoryRegion(this SharedConfigMemoryRegion sharedConfigMemoryRegion)
        {
            // Initialize memory allocator.
            //
            var allocator = sharedConfigMemoryRegion.Allocator;
            allocator.AllocationBlockOffset = Utils.Align((uint)sharedConfigMemoryRegion.CodegenTypeSize(), 256);
            allocator.AllocationBlockSize = (uint)sharedConfigMemoryRegion.MemoryHeader.MemoryRegionSize - allocator.AllocationBlockOffset;

            allocator.FreeOffset = allocator.AllocationBlockOffset;
            allocator.AllocationCount = 0;
            allocator.LastAllocatedOffset = 0;

            // Allocate array for shared config offsets.
            //
            uint elementCount = 2048;
            AllocationEntry allocationEntry = sharedConfigMemoryRegion.Allocate(default(UIntArray).CodegenTypeSize() + (sizeof(uint) * elementCount));

            sharedConfigMemoryRegion.ConfigsArrayOffset = (uint)allocationEntry.Buffer.Offset(sharedConfigMemoryRegion.Buffer) + (uint)default(AllocationEntry).CodegenTypeSize();

            UIntArray configsOffsetArray = sharedConfigMemoryRegion.ConfigsOffsetArray;
            configsOffsetArray.Count = elementCount;

            return sharedConfigMemoryRegion;
        }
    }

    /// <summary>
    /// Helper struct used to initialize memory regions.
    /// </summary>
    /// <typeparam name="T">MemoryRegion type.</typeparam>
    internal struct MemoryRegionInitializer<T>
         where T : ICodegenProxy, new()
    {
        internal void Initalize(SharedMemoryRegionView<T> sharedMemory)
        {
            if (typeof(T) == typeof(GlobalMemoryRegion))
            {
                GlobalMemoryRegion globalMemoryRegion = (GlobalMemoryRegion)(object)sharedMemory.MemoryRegion();
                globalMemoryRegion.InitializeMemoryRegion();
            }
            else if (typeof(T) == typeof(SharedConfigMemoryRegion))
            {
                SharedConfigMemoryRegion sharedMemoryRegionView = (SharedConfigMemoryRegion)(object)sharedMemory.MemoryRegion();
                sharedMemoryRegionView.InitializeMemoryRegion();
            }
            else
            {
                throw new ArgumentException("Unsupported memory region type.");
            }
        }
    }
}
