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
        /// Initialize GlobalMemoryRegion.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <returns></returns>
        public static GlobalMemoryRegion InitializeMemoryRegion(this GlobalMemoryRegion globalMemoryRegion)
        {
            // Initialize properties.
            //
            globalMemoryRegion.TotalMemoryRegionCount = 1;

            globalMemoryRegion.RegisteredSettingsAssemblyCount.Store(1);

            var sharedConfigDictionary = globalMemoryRegion.SharedConfigDictionary;
            var allocator = sharedConfigDictionary.Allocator;

            // Initialize memory allocator.
            //
            allocator.InitializeArenaAllocator(globalMemoryRegion.MemoryHeader, (int)globalMemoryRegion.CodegenTypeSize());

            // Initialize shared config dictionary.
            //
            sharedConfigDictionary.InitializeSharedConfigDictionary();

            return globalMemoryRegion;
        }

        /// <summary>
        /// Initialize SharedConfigMemoryRegion.
        /// </summary>
        /// <param name="sharedConfigMemoryRegion"></param>
        /// <returns></returns>
        public static SharedConfigMemoryRegion InitializeMemoryRegion(this SharedConfigMemoryRegion sharedConfigMemoryRegion)
        {
            var sharedConfigDictionary = sharedConfigMemoryRegion.SharedConfigDictionary;
            var allocator = sharedConfigDictionary.Allocator;

            // Initialize memory allocator.
            //
            allocator.InitializeArenaAllocator(sharedConfigMemoryRegion.MemoryHeader, (int)sharedConfigMemoryRegion.CodegenTypeSize());

            // Initialize shared config dictionary.
            //
            sharedConfigDictionary.InitializeSharedConfigDictionary();

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
