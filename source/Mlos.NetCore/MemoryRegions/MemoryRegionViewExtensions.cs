// -----------------------------------------------------------------------
// <copyright file="MemoryRegionViewExtensions.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;

using Mlos.Core;
using Mlos.Core.Internal;

using MlosInternal = Mlos.Core.Internal;
using MlosProxyInternal = Proxy.Mlos.Core.Internal;

namespace Proxy.Mlos.Core.Internal
{
    /// <summary>
    /// Memory region extension methods.
    /// </summary>
    public static class MemoryRegionViewExtensions
    {
        /// <summary>
        /// Tries to get a shared memory map name.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <param name="memoryRegionId"></param>
        /// <param name="sharedMemoryMapName"></param>
        /// <returns></returns>
        public static bool TryGetSharedMemoryName(
            this GlobalMemoryRegion globalMemoryRegion,
            MlosInternal.MemoryRegionId memoryRegionId,
            out string sharedMemoryMapName)
        {
            MlosInternal.RegisteredMemoryRegionConfig.CodegenKey registeredMemoryLookupKey = default;
            registeredMemoryLookupKey.MemoryRegionId = memoryRegionId;

            // Locate shared memory region config.
            //
            SharedConfig<MlosProxyInternal.RegisteredMemoryRegionConfig> registeredMemoryRegionSharedConfig =
                SharedConfigManager.Lookup(globalMemoryRegion.SharedConfigDictionary, registeredMemoryLookupKey);

            if (!registeredMemoryRegionSharedConfig.HasSharedConfig)
            {
                sharedMemoryMapName = null;
                return false;
            }

            // Config exists, create a shared config memory region.
            //
            sharedMemoryMapName = registeredMemoryRegionSharedConfig.Config.MemoryMapName.Value;
            return true;
        }

        /// <summary>
        /// Tries to open a shared memory map.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <param name="memoryRegionId"></param>
        /// <param name="sharedMemoryMapView"></param>
        /// <returns></returns>
        public static bool TryOpenExisting(
            this GlobalMemoryRegion globalMemoryRegion,
            MlosInternal.MemoryRegionId memoryRegionId,
            out SharedMemoryMapView sharedMemoryMapView)
        {
            MlosInternal.RegisteredMemoryRegionConfig.CodegenKey registeredMemoryLookupKey = default;
            registeredMemoryLookupKey.MemoryRegionId = memoryRegionId;

            // Locate shared memory region config.
            //
            SharedConfig<MlosProxyInternal.RegisteredMemoryRegionConfig> registeredMemoryRegionSharedConfig =
                SharedConfigManager.Lookup(globalMemoryRegion.SharedConfigDictionary, registeredMemoryLookupKey);

            if (!registeredMemoryRegionSharedConfig.HasSharedConfig)
            {
                sharedMemoryMapView = null;
                return false;
            }

            // Config exists, create a shared config memory region.
            //
            MlosProxyInternal.RegisteredMemoryRegionConfig registeredMemoryRegionConfig = registeredMemoryRegionSharedConfig.Config;

            sharedMemoryMapView = SharedMemoryMapView.OpenExisting(
                registeredMemoryRegionConfig.MemoryMapName.Value,
                registeredMemoryRegionConfig.MemoryRegionSize);

            return true;
        }

        /// <summary>
        /// Tries to open a named event.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <param name="memoryRegionId"></param>
        /// <param name="namedEvent"></param>
        /// <returns></returns>
        public static bool TryOpenExisting(
            this GlobalMemoryRegion globalMemoryRegion,
            MlosInternal.MemoryRegionId memoryRegionId,
            out NamedEvent namedEvent)
        {
            MlosInternal.RegisteredNamedEventConfig.CodegenKey namedEventLookupKey = default;
            namedEventLookupKey.MemoryRegionId = memoryRegionId;

            // Locate named event config.
            //
            SharedConfig<MlosProxyInternal.RegisteredNamedEventConfig> registeredNamedEventSharedConfig =
                SharedConfigManager.Lookup(globalMemoryRegion.SharedConfigDictionary, namedEventLookupKey);

            if (!registeredNamedEventSharedConfig.HasSharedConfig)
            {
                namedEvent = null;
                return false;
            }

            // Config exists, create a named event.
            //
            MlosProxyInternal.RegisteredNamedEventConfig registeredNamedEventConfig = registeredNamedEventSharedConfig.Config;

            namedEvent = NamedEvent.CreateOrOpen(registeredNamedEventConfig.EventName.Value);

            return true;
        }

        /// <summary>
        /// Initialize GlobalMemoryRegion.
        /// </summary>
        /// <param name="globalMemoryRegion"></param>
        /// <returns></returns>
        public static GlobalMemoryRegion InitializeMemoryRegion(this GlobalMemoryRegion globalMemoryRegion)
        {
            // Initialize properties.
            //
            globalMemoryRegion.GlobalMemoryRegionIndex = 1;

            globalMemoryRegion.RegisteredSettingsAssemblyCount.Store(1);

            MemoryRegion memoryHeader = globalMemoryRegion.MemoryHeader;
            MemoryRegionId memoryRegionId = memoryHeader.MemoryRegionId;
            memoryRegionId.Type = MemoryRegionType.Global;

            SharedConfigDictionary sharedConfigDictionary = globalMemoryRegion.SharedConfigDictionary;
            ArenaAllocator allocator = sharedConfigDictionary.Allocator;

            // Initialize memory allocator.
            //
            allocator.InitializeArenaAllocator(memoryHeader, (int)globalMemoryRegion.CodegenTypeSize());

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
            SharedConfigDictionary sharedConfigDictionary = sharedConfigMemoryRegion.SharedConfigDictionary;
            ArenaAllocator allocator = sharedConfigDictionary.Allocator;

            MemoryRegion memoryHeader = sharedConfigMemoryRegion.MemoryHeader;
            MemoryRegionId memoryRegionId = memoryHeader.MemoryRegionId;
            memoryRegionId.Type = MemoryRegionType.SharedConfig;

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
        internal void Initialize(SharedMemoryRegionView<T> sharedMemory)
        {
            if (typeof(T) == typeof(GlobalMemoryRegion))
            {
                var globalMemoryRegion = (GlobalMemoryRegion)(object)sharedMemory.MemoryRegion();
                globalMemoryRegion.InitializeMemoryRegion();
            }
            else if (typeof(T) == typeof(SharedConfigMemoryRegion))
            {
                var sharedMemoryRegionView = (SharedConfigMemoryRegion)(object)sharedMemory.MemoryRegion();
                sharedMemoryRegionView.InitializeMemoryRegion();
            }
            else
            {
                throw new ArgumentException("Unsupported memory region type.");
            }
        }
    }
}
